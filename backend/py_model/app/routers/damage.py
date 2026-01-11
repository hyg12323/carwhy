from fastapi import APIRouter, UploadFile, File, Query
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from typing import List

from app.services.yolo_service import YoloService
from app.services.accident_rule_service import estimate_accident_type
from app.services.drive_cnn_service import CNNService

import io

router = APIRouter(prefix="/damage", tags=["Damage Detection"])

# =========================
# Services (싱글톤)
# =========================
yolo_service = YoloService()
cnn_service = CNNService()


class AccidentVehicle(BaseModel):
    vehicle_id: int
    crop_path: str


class DamageByVehicleRequest(BaseModel):
    accident_vehicles: List[AccidentVehicle]

# =========================
# Health Check
# =========================
@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "yolo_loaded": yolo_service.is_ready(),
        "cnn_loaded": True
    }


# =========================
# 단일 이미지 파손 탐지 + 주행 가능 판단
# =========================
@router.post("/detect")
async def detect_damage(file: UploadFile = File(...)):
    image_bytes = await file.read()

    # 1. YOLO 파손 탐지
    damage_result = yolo_service.detect(image_bytes)
    detections = damage_result["detections"]

    if not detections:
        return {
            "status": "UNSURE",
            "message": "파손을 탐지하지 못했습니다",
            "detections": [],
            "drivable": None
        }

    # 2. CNN 주행 가능 판단
    drive_result = cnn_service.judge(
        detections=detections,
        image_bytes=image_bytes
    )

    # 3. 사고 유형 판단 (car_count 제거)
    accident = estimate_accident_type(detections)

    return {
        "status": "DETECTED",
        "detections": detections,
        "accident": accident,
        "drivable": drive_result
    }


# =========================
# 이미지 + 시각화 (YOLO 전용)
# =========================
@router.post("/detect/image")
async def detect_damage_image(
    file: UploadFile = File(...),
    conf: float = Query(0.4, ge=0.0, le=1.0)
):
    image_bytes = await file.read()

    img_bytes, detections = yolo_service.detect_and_draw(
        image_bytes,
        conf_threshold=conf
    )

    if not detections:
        return JSONResponse(
            status_code=200,
            content={
                "status": "UNSURE",
                "message": "파손 여부를 판단하기 어렵습니다",
                "detections": []
            }
        )

    accident_result = estimate_accident_type(detections)

    return StreamingResponse(
        io.BytesIO(img_bytes),
        media_type="image/jpeg",
        headers={
            "X-Detection-Status": "DETECTED",
            "X-Detection-Count": str(len(detections)),
            "X-Primary-Damage": detections[0]["class_name"],
            "X-Accident-Type": accident_result["accident_type"],
            "X-Accident-Detected": str(accident_result["accident_detected"]),
            "X-Confidence-Threshold": str(conf)
        }
    )


# =========================
# 멀티 이미지 파손 탐지 (CNN 1회)
# =========================
@router.post("/detect/multi")
async def detect_damage_multi(files: list[UploadFile] = File(...)):
    all_detections = []
    image_results = []
    first_image_bytes = None

    for idx, file in enumerate(files):
        image_bytes = await file.read()

        if first_image_bytes is None:
            first_image_bytes = image_bytes

        result = yolo_service.detect(image_bytes)
        if not result["detections"]:
            result = yolo_service.detect_with_car_crop(image_bytes)

        image_results.append({
            "image_index": idx,
            "filename": file.filename,
            "detection_count": len(result["detections"]),
            "detections": result["detections"]
        })

        all_detections.extend(result["detections"])

    if not all_detections:
        return {
            "status": "UNSURE",
            "message": "모든 이미지에서 파손을 탐지하지 못했습니다",
            "image_count": len(files),
            "drivable": None,
            "images": image_results
        }

    # CNN 주행 가능 판단 (대표 이미지 1회)
    drive_result = cnn_service.judge(
        detections=all_detections,
        image_bytes=first_image_bytes
    )

    #  multi 모드 명시
    accident = estimate_accident_type(
        all_detections,
        mode="multi"
    )

    return {
        "status": "DETECTED",
        "accident": accident,
        "drivable": drive_result,
        "total_detection_count": len(all_detections),
        "images": image_results
    }

@router.post("/detect/by-vehicle")
async def detect_damage_by_vehicle(req: DamageByVehicleRequest):
    vehicle_results = []
    all_detections = []

    # 사고 차량이 아예 없는 경우
    if not req.accident_vehicles:
        return {
            "status": "NO_ACCIDENT_VEHICLE",
            "vehicles": [],
            "drivable": None
        }

    representative_image_bytes = None

    for v in req.accident_vehicles:
        # crop 이미지 로드
        try:
            with open(v.crop_path, "rb") as f:
                image_bytes = f.read()
        except FileNotFoundError:
            # crop 파일이 없는 경우도 명확히 처리
            vehicle_results.append({
                "vehicle_id": v.vehicle_id,
                "damages": [],
                "error": "crop_image_not_found"
            })
            continue

        # 대표 이미지 (CNN 판단용)
        if representative_image_bytes is None:
            representative_image_bytes = image_bytes

        # YOLO 파손 탐지 (차량 crop 기준)
        result = yolo_service.detect(image_bytes)
        detections = result["detections"]

        vehicle_results.append({
            "vehicle_id": v.vehicle_id,
            "damages": detections
        })

        all_detections.extend(detections)

    # 모든 사고 차량에서 파손이 하나도 없는 경우
    if not all_detections:
        return {
            "status": "NO_DAMAGE_DETECTED",
            "vehicles": vehicle_results,
            "drivable": None
        }

    # CNN 주행 가능 판단 (사고 차량 전체 기준 1회)
    drive_result = cnn_service.judge(
        detections=all_detections,
        image_bytes=representative_image_bytes
    )

    return {
        "status": "DETECTED",
        "vehicle_count": len(vehicle_results),
        "vehicles": vehicle_results,
        "drivable": drive_result
    }