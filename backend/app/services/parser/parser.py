import os
import uuid
from typing import Dict, List

import fitz  # PyMuPDF
from fastapi import UploadFile
from pathlib import Path

# Base directory (project root)
BASE_DIR = Path(__file__).resolve().parents[3]

# Storage paths
IMAGE_OUTPUT_DIR = BASE_DIR / "data/raw/images"
UPLOAD_DIR = BASE_DIR / "data/raw"


def _save_uploaded_file(upload_file: UploadFile) -> str:
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    file_id = str(uuid.uuid4())
    file_path = str(UPLOAD_DIR / f"{file_id}_{upload_file.filename}")

    content = upload_file.file.read()

    with open(file_path, "wb") as f:
        f.write(content)

    upload_file.file.seek(0)

    return file_path


def _extract_text_and_pages(pdf_path: str):
    doc = fitz.open(pdf_path)

    full_text = []
    pages = []

    for i, page in enumerate(doc):
        text = page.get_text()

        full_text.append(f"\n--- PAGE {i+1} ---\n{text}")

        pages.append({
            "page": i + 1,
            "text": text
        })

    return "\n".join(full_text), pages


def _extract_images_from_pdf(pdf_path: str, prefix: str) -> List[Dict]:
    os.makedirs(IMAGE_OUTPUT_DIR, exist_ok=True)

    doc = fitz.open(pdf_path)
    image_paths = []

    for page_index in range(len(doc)):
        page = doc[page_index]
        images = page.get_images(full=True)

        for img_index, img in enumerate(images):
            xref = img[0]
            base_image = doc.extract_image(xref)

            image_bytes = base_image["image"]
            image_ext = base_image["ext"]

            image_filename = f"{prefix}_page{page_index+1}_{img_index}.{image_ext}"
            image_path = str(IMAGE_OUTPUT_DIR / image_filename)

            with open(image_path, "wb") as img_file:
                img_file.write(image_bytes)

            image_paths.append({
                "path": image_path,
                "page": page_index + 1
            })

    return image_paths


async def parse_documents(
    inspection_file: UploadFile,
    thermal_file: UploadFile
) -> Dict:

    inspection_path = _save_uploaded_file(inspection_file)
    thermal_path = _save_uploaded_file(thermal_file)

    # TEXT + PAGES
    inspection_text, inspection_pages = _extract_text_and_pages(inspection_path)
    thermal_text, thermal_pages = _extract_text_and_pages(thermal_path)

    # IMAGES
    inspection_images = _extract_images_from_pdf(inspection_path, "inspection")
    thermal_images = _extract_images_from_pdf(thermal_path, "thermal")

    return {
        "inspection": {
            "text": inspection_text,
            "pages": inspection_pages,
            "images": inspection_images,
            "file_path": inspection_path
        },
        "thermal": {
            "text": thermal_text,
            "pages": thermal_pages,
            "images": thermal_images,
            "file_path": thermal_path
        }
    }