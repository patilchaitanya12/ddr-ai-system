from typing import Dict
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer("all-MiniLM-L6-v2")


def deduplicate_texts(texts, threshold=0.8):
    if not texts:
        return []

    embeddings = model.encode(texts)
    selected = []
    used = set()

    for i in range(len(texts)):
        if i in used:
            continue

        selected.append(texts[i])

        for j in range(i + 1, len(texts)):
            sim = cosine_similarity([embeddings[i]], [embeddings[j]])[0][0]
            if sim > threshold:
                used.add(j)

    return selected


def generate_ddr(reasoned_data: Dict) -> Dict:
    final_analysis = reasoned_data.get("final_analysis", [])

    property_summary = set()
    area_observations = []
    root_causes = set()
    severity_list = []
    recommendations = []
    missing_info = set()
    additional_notes = []

    for area_data in final_analysis:
        area = area_data.get("area", "unknown")
        issues = area_data.get("issues", [])
        analysis = area_data.get("analysis", {})
        images = area_data.get("images", [])

        for issue in issues:
            clean_issue = issue.get("issue_type", "").lower()
            if clean_issue and clean_issue not in ["unknown", "open"]:
                property_summary.add(clean_issue)

        descriptions = []
        locations = set()

        for issue in issues:
            descriptions.extend(issue.get("descriptions", []))
            locations.update(issue.get("locations", []))

        details = f"""
Issues Identified:
- {"; ".join(set(descriptions)) if descriptions else "Not Available"}

Locations:
- {", ".join([l for l in locations if l != "unknown"]) if locations else "Not Available"}
"""

        area_observations.append({
            "area": area,
            "details": details.strip(),
            "images": images
        })

        for cause in analysis.get("probable_root_cause", []):
            root_causes.add(cause.strip().capitalize())

        severity = analysis.get("severity", {})
        severity_list.append({
            "area": area,
            "severity": f"{severity.get('level', 'Unknown')} Risk",
            "reason": severity.get("reason", "Not Available")
        })

        recommendations.extend(analysis.get("recommended_actions", []))

        for missing in analysis.get("missing_information", []):
            missing_info.add(missing)

        for conflict in analysis.get("conflicts", []):
            additional_notes.append(conflict)

    return {
        "property_issue_summary": sorted(list(property_summary)),
        "area_wise_observations": area_observations,
        "probable_root_cause": sorted(list(root_causes)),
        "severity_assessment": severity_list,
        "recommended_actions": deduplicate_texts(recommendations),
        "additional_notes": additional_notes,
        "missing_or_unclear_information": sorted(list(missing_info))
    }