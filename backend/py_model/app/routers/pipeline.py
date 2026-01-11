from fastapi import APIRouter, UploadFile, File
from typing import List
import os
import uuid

from app.services.pipeline_service import (
    analyze_single_pipeline,
    analyze_multi_pipeline
)

router = APIRouter(
    prefix="/pipeline",
    tags=["Pipeline"]
)

# =========================
# Upload temp dir
# =========================
BASE_DIR = os.path.dirname(__file__)
UPLOAD_DIR = os.path.join(BASE_DIR, "..", "..", "temp")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ============================================================
# 단일 이미지 파이프라인
# FormData key: image
# ============================================================
@router.post("/single")
async def pipeline_single(image: UploadFile = File(...)):
    # 확장자 유지 (png/jpg/webp 대응)
    ext = os.path.splitext(image.filename)[1] or ".jpg"
    filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(await image.read())

    try:
        result = analyze_single_pipeline(file_path)
        return result
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


# ============================================================
# 다중 이미지 파이프라인
# FormData key: images
# ============================================================
@router.post("/multi")
async def pipeline_multi(images: List[UploadFile] = File(...)):
    image_paths = []

    try:
        for image in images:
            ext = os.path.splitext(image.filename)[1] or ".jpg"
            filename = f"{uuid.uuid4()}{ext}"
            file_path = os.path.join(UPLOAD_DIR, filename)

            with open(file_path, "wb") as f:
                f.write(await image.read())

            image_paths.append(file_path)

        result = analyze_multi_pipeline(image_paths)
        return result

    finally:
        for path in image_paths:
            if os.path.exists(path):
                os.remove(path)
