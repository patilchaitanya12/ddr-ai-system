import os
import uuid
from typing import Dict, List

import fitz  
from fastapi import UploadFile


# Folder to store extracted images
IMAGE_OUTPUT_DIR = "backend/data/raw/images"


def _save_uploaded_file(upload_file: UploadFile) -> str:
    """Save uploaded file temporarily"""
    file_id = str(uuid.uuid4())
    file_path = f"backend/data/raw/{file_id}_{upload_file.filename}"

    with open(file_path, "wb") as f:
        f.write(upload_file.file.read())

    return file_path


def _extract_text_from_pdf(pdf_path: str) -> str:
    """Extract full text from PDF"""
    doc = fitz.open(pdf_path)
    full_text = ""

    for page in doc:
        full_text += page.get_text()

    return full_text


def _extract_images_from_pdf(pdf_path: str, prefix: str) -> List[str]:
    """Extract images and save them locally"""
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

            image_filename = f"{prefix}_p{page_index}_{img_index}.{image_ext}"
            image_path = os.path.join(IMAGE_OUTPUT_DIR, image_filename)

            with open(image_path, "wb") as img_file:
                img_file.write(image_bytes)

            image_paths.append(image_path)

    return image_paths


async def parse_documents(
    inspection_file: UploadFile,
    thermal_file: UploadFile
) -> Dict:
    """
    Main parser function:
    - Saves files
    - Extracts text + images
    """

    #Save files
    inspection_path = _save_uploaded_file(inspection_file)
    thermal_path = _save_uploaded_file(thermal_file)

    #Extract text
    inspection_text = _extract_text_from_pdf(inspection_path)
    thermal_text = _extract_text_from_pdf(thermal_path)

    #Extract images
    inspection_images = _extract_images_from_pdf(inspection_path, "inspection")
    thermal_images = _extract_images_from_pdf(thermal_path, "thermal")

    return {
        "inspection": {
            "text": inspection_text,
            "images": inspection_images,
            "file_path": inspection_path
        },
        "thermal": {
            "text": thermal_text,
            "images": thermal_images,
            "file_path": thermal_path
        }
    }