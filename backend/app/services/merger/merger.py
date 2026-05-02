from typing import Dict
from collections import defaultdict
import os
import numpy as np
import torch
import open_clip
from PIL import Image
from scipy.optimize import linear_sum_assignment
from transformers import BlipProcessor, BlipForConditionalGeneration

BASE_URL = "http://localhost:8000/images"

device = "cuda" if torch.cuda.is_available() else "cpu"

model, _, preprocess = open_clip.create_model_and_transforms(
    "ViT-B-32",
    pretrained="laion2b_s34b_b79k"
)
model = model.to(device)
model.eval()
tokenizer = open_clip.get_tokenizer("ViT-B-32")

blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
blip_model = BlipForConditionalGeneration.from_pretrained(
    "Salesforce/blip-image-captioning-base"
).to(device)


def generate_caption(path):
    try:
        img = Image.open(path).convert("RGB")
        inputs = blip_processor(img, return_tensors="pt").to(device)
        out = blip_model.generate(**inputs, max_new_tokens=20)
        return blip_processor.decode(out[0], skip_special_tokens=True).lower()
    except:
        return ""


def _normalize(text):
    return text.strip().lower() if text else "unknown"


def _to_url(path):
    return f"{BASE_URL}/{os.path.basename(path)}"


def _clean_issue(issue):
    if not issue:
        return "unknown"
    issue = issue.lower()
    if "damp" in issue: return "dampness"
    if "leak" in issue: return "leakage"
    if "crack" in issue: return "cracks"
    if "seep" in issue: return "seepage"
    if "tile" in issue or "joint" in issue: return "tile defect"
    return issue


def encode_images(images):
    valid, tensors, captions = [], [], []

    for img in images:
        try:
            path = img["path"]
            image = preprocess(Image.open(path).convert("RGB"))
            caption = generate_caption(path)

            tensors.append(image)
            valid.append(img)
            captions.append(caption)
        except:
            continue

    if not tensors:
        return [], None, []

    batch = torch.stack(tensors).to(device)

    with torch.no_grad():
        feats = model.encode_image(batch)

    return valid, feats / feats.norm(dim=-1, keepdim=True), captions


def encode_texts(texts):
    tokens = tokenizer(texts).to(device)
    with torch.no_grad():
        feats = model.encode_text(tokens)
    return feats / feats.norm(dim=-1, keepdim=True)


def build_query(area, issues):
    parts = [area]

    for i in issues:
        parts.append(i["issue_type"])
        parts.extend(i["descriptions"])

    parts.append("wall ceiling bathroom pipe leakage damp crack seepage")
    return " ".join(parts)


def boost_score(area, caption, score):
    cap = caption.lower()

    if "bathroom" in area and ("tile" in cap or "toilet" in cap):
        score += 0.3

    if "parking" in area and ("pipe" in cap or "ceiling" in cap):
        score += 0.3

    if "external" in area and ("wall" in cap or "crack" in cap):
        score += 0.25

    return score


def build_sentence(issues):
    if not issues:
        return "No major issues observed."

    parts = []

    for i in issues:
        issue = i["issue_type"]
        locs = ", ".join(i.get("locations", []))
        desc = " ".join(i.get("descriptions", []))

        sentence = f"{issue} observed"

        if locs and locs != "unknown":
            sentence += f" at {locs}"

        if desc:
            sentence += f", {desc}"

        parts.append(sentence)

    return " ".join(parts)


def merge_data(structured_data: Dict):

    observations = structured_data.get("observations", [])
    images = structured_data.get("images", [])

    for img in images:
        img["url"] = _to_url(img["path"])

    area_map = defaultdict(lambda: {
        "issues": [],
        "thermal": {"available": False, "images": []}
    })

    for obs in observations:
        if not obs.get("issue_type"):
            continue

        area = _normalize(obs["area"])
        issue_type = _clean_issue(obs["issue_type"])

        entry = {
            "issue_type": issue_type,
            "locations": [_normalize(obs.get("sub_area"))],
            "descriptions": [obs["description"]],
            "source": obs.get("source", "inspection")
        }

        area_map[area]["issues"].append(entry)

        if obs.get("source") == "thermal":
            area_map[area]["thermal"]["available"] = True

    areas = list(area_map.keys())

    queries = [build_query(a, area_map[a]["issues"]) for a in areas]
    text_emb = encode_texts(queries)

    valid_imgs, img_emb, captions = encode_images(images)

    if img_emb is None:
        return {"area_analysis": []}

    sim = (img_emb @ text_emb.T).cpu().numpy()

    for i, caption in enumerate(captions):
        for j, area in enumerate(areas):
            sim[i][j] = boost_score(area, caption, sim[i][j])

    cost = -sim
    row_ind, col_ind = linear_sum_assignment(cost)

    assignments = defaultdict(list)
    global_used = set()

    for r, c in zip(row_ind, col_ind):
        if sim[r][c] > 0.22:
            img = valid_imgs[r]
            assignments[areas[c]].append((img, sim[r][c], img_emb[r]))
            global_used.add(img["path"])

    for j, area in enumerate(areas):
        scores = sim[:, j]
        ranked = np.argsort(scores)[::-1]

        for idx in ranked:
            if len(assignments[area]) >= 1:
                break

            img = valid_imgs[idx]
            path = img["path"]

            if path in global_used:
                continue

            if scores[idx] < 0.25:
                break

            assignments[area].append((img, scores[idx], img_emb[idx]))
            global_used.add(path)

    def is_dup(e, selected):
        for s in selected:
            if torch.dot(e, s).item() > 0.92:
                return True
        return False

    final_assignments = {}

    for area, items in assignments.items():
        selected_urls = []
        selected_embs = []

        for img, score, emb in sorted(items, key=lambda x: x[1], reverse=True):
            if not is_dup(emb, selected_embs):
                selected_urls.append(img["url"])
                selected_embs.append(emb)

        if not selected_urls:
            selected_urls = ["Image Not Available"]

        final_assignments[area] = selected_urls[:1]

    output = []

    for area in areas:
        issues = area_map[area]["issues"]

        output.append({
            "area": area,
            "issues": issues,
            "summary": build_sentence(issues),
            "thermal": area_map[area]["thermal"],
            "images": final_assignments.get(area, ["Image Not Available"])
        })

    return {"area_analysis": output}