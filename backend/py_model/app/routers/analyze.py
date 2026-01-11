import os
import uuid
from typing import List
from fastapi import APIRouter, UploadFile, File

from app.services.vehicle_detect_service import detect_vehicles
from app.services.accident_service import predict_accident
from app.services.vehicle_service import predict_vehicle_type

# =========================
# Router
# =========================
router = APIRouter(
    prefix="/analyze",
    tags=["Analysis"]
)

# =========================
# Temp 저장 경로
# =========================
BASE_DIR = os.path.dirname(__file__)
UPLOAD_DIR = os.path.join(BASE_DIR, "..", "..", "temp")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ============================================================
# 단일 이미지 분석
# - 사고 여부 판단
# - 차량 종류 분류
# - 결과와 상관없이 damage로 전달
# ============================================================
@router.post("/single")
async def analyze_single(file: UploadFile = File(...)):
    filename = f"{uuid.uuid4()}.jpg"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as f:
        f.write(await file.read())

    # 차량 crop 생성
    CROP_DIR = os.path.join(UPLOAD_DIR, "crops")
    os.makedirs(CROP_DIR, exist_ok=True)

    vehicle_images = detect_vehicles(file_path, CROP_DIR)

    vehicles = []
    accident_vehicles = []

    for idx, img_path in enumerate(vehicle_images, start=1):
        accident_result = predict_accident(img_path)

        vehicle_info = {
            "vehicle_id": idx,
            "crop_path": img_path,
            "accident": accident_result["is_accident"],
            "confidence": accident_result.get("confidence")
        }
        vehicles.append(vehicle_info)

        # 사고 차량만 추림
        if accident_result["is_accident"]:
            accident_vehicles.append({
                "vehicle_id": idx,
                "crop_path": img_path
            })

    # 차종 분류 (전체 이미지 기준 1회)
    vehicle_result = predict_vehicle_type(file_path)

    return {
        "vehicle_count": len(vehicles),
        "vehicles": vehicles,                 # 전체 차량 정보
        "accident_vehicle_count": len(accident_vehicles),
        "accident_vehicles": accident_vehicles,  # 다음 단계 입력
        "vehicle": vehicle_result,
        "next": "/damage/detect"
    }


# ============================================================
# 다중 이미지 분석
# - 대표 이미지 기준 사고 판단
# - 대표 이미지 기준 차량 분류
# - 모든 이미지는 damage/multi로 전달
# ============================================================
@router.post("/multi")
async def analyze_multi(files: List[UploadFile] = File(...)):
    image_paths = []
    first_image_path = None

    # 1. 이미지 저장
    for idx, file in enumerate(files):
        filename = f"{uuid.uuid4()}.jpg"
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as f:
            f.write(await file.read())

        image_paths.append(file_path)

        if idx == 0:
            first_image_path = file_path

    # 2. 대표 이미지에서 차량 분리
    CROP_DIR = os.path.join(UPLOAD_DIR, "crops")
    os.makedirs(CROP_DIR, exist_ok=True)

    vehicle_images = detect_vehicles(first_image_path, CROP_DIR)

    vehicles = []
    accident_vehicles = []

    # 3. 차량 crop 기준 사고 판단
    for idx, img_path in enumerate(vehicle_images, start=1):
        accident_result = predict_accident(img_path)

        vehicle_info = {
            "vehicle_id": idx,
            "crop_path": img_path,
            "accident": accident_result["is_accident"],
            "confidence": accident_result.get("confidence")
        }
        vehicles.append(vehicle_info)

        if accident_result["is_accident"]:
            accident_vehicles.append({
                "vehicle_id": idx,
                "crop_path": img_path
            })

    # 4. 차종 분류 (대표 이미지 기준)
    vehicle_result = predict_vehicle_type(first_image_path)

    return {
        "vehicle_count": len(vehicles),
        "vehicles": vehicles,
        "accident_vehicle_count": len(accident_vehicles),
        "accident_vehicles": accident_vehicles,
        "vehicle": vehicle_result,
        "support_images": image_paths[1:],  # 대표 이미지 제외
        "next": "/damage/detect"
    }
