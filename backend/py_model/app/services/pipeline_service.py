import os
import uuid
from typing import List

from app.services.vehicle_detect_service import detect_vehicles
from app.services.accident_service import predict_accident
from app.services.vehicle_service import predict_vehicle_type
from app.services.yolo_service import YoloService
from app.services.drive_cnn_service import CNNService


# =========================
# Services (싱글톤)
# =========================
yolo_service = YoloService()
cnn_service = CNNService()


# =========================
# Base / dirs
# =========================
BASE_DIR = os.path.dirname(__file__)

CROP_DIR = os.path.join(BASE_DIR, "..", "..", "temp", "crops")
STATIC_DIR = os.path.join(BASE_DIR, "..", "..", "static")
ANNOTATED_DIR = os.path.join(STATIC_DIR, "annotated")

os.makedirs(CROP_DIR, exist_ok=True)
os.makedirs(ANNOTATED_DIR, exist_ok=True)


# ============================================================
# 단일 이미지 파이프라인
# ============================================================
def analyze_single_pipeline(image_path: str):
    # -------------------------
    # 1. 차량 탐지
    # -------------------------
    vehicle_images = detect_vehicles(image_path, CROP_DIR)
    vehicle_count = len(vehicle_images)

    vehicles = []
    accident_vehicles = []
    has_accident = False

    # -------------------------
    # 2. 🔥 차종 분류 (한 번만)
    # -------------------------
    vehicle_type_result = predict_vehicle_type(image_path)

    vehicle_type = (
        vehicle_type_result.get("label")
        if isinstance(vehicle_type_result, dict)
        else vehicle_type_result
    )

    vehicle_type_confidence = (
        vehicle_type_result.get("confidence")
        if isinstance(vehicle_type_result, dict)
        else None
    )

    # -------------------------
    # 3. 차량별 사고 판단
    # -------------------------
    for idx, v_path in enumerate(vehicle_images, start=1):
        result = predict_accident(v_path)

        vehicles.append({
            "vehicle_id": idx,
            "accident": result["is_accident"],
            "confidence": result.get("confidence"),

            # ✅ 핵심: 차량 객체 안에 차종 삽입
            "vehicle_type": vehicle_type,
            "vehicle_type_confidence": vehicle_type_confidence,
        })

        if result["is_accident"]:
            has_accident = True
            filename = os.path.basename(v_path)

            accident_vehicles.append({
                "vehicle_id": idx,
                "crop_path": v_path,
                "crop_url": f"/static/crops/{filename}"
            })

    # -------------------------
    # 🚦 사고 없음
    # -------------------------
    if not has_accident:
        return {
            "mode": "single",
            "status": "NO_ACCIDENT",
            "vehicle_count": vehicle_count,
            "vehicles": vehicles,
            "accident_vehicle_count": 0,
            "accident_vehicles": [],
            "vehicle": vehicle_type_result,
            "support_images": [],
            "damage_result": None,
            "yolo_image_url": None,
            "drivable_result": None,
            "accident": {
                "accident_detected": False,
                "accident_state": "NO_ACCIDENT",
                "accident_type": "UNKNOWN",
                "confidence_level": "LOW",
                "scores": {},
            }
        }

    # -------------------------
    # 4. 사고 차량 damage 단계
    # -------------------------
    from app.services.damage_service import detect_damage_by_vehicle_internal

    damage_result = detect_damage_by_vehicle_internal({
        "accident_vehicles": accident_vehicles
    })

    # -------------------------
    # 5. YOLO 이미지 생성
    # -------------------------
    yolo_image_url = None
    image_bytes = None
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        annotated_bytes, _ = yolo_service.detect_and_draw(image_bytes)

        filename = f"yolo_{uuid.uuid4().hex}.jpg"
        save_path = os.path.join(ANNOTATED_DIR, filename)

        with open(save_path, "wb") as f:
            f.write(annotated_bytes)

        yolo_image_url = f"/static/annotated/{filename}"
    except Exception as e:
        print("YOLO annotated image failed:", e)

    # -------------------------
    # 6. CNN 주행 가능 판단
    # -------------------------
    drivable_result = None
    if image_bytes is not None:
        drivable_result = cnn_service.judge(
            detections=damage_result.get("detections", []),
            image_bytes=image_bytes
        )

    # -------------------------
    # 7. 최종 반환
    # -------------------------
    return {
        "mode": "single",
        "status": "ANALYZED",
        "vehicle_count": vehicle_count,
        "vehicles": vehicles,
        "accident_vehicle_count": len(accident_vehicles),
        "accident_vehicles": accident_vehicles,
        "vehicle": vehicle_type_result,
        "support_images": [],
        "damage_result": damage_result,
        "yolo_image_url": yolo_image_url,
        "drivable_result": drivable_result,
        "accident": damage_result.get("accident")
    }


# ============================================================
# 다중 이미지 파이프라인
# ============================================================
def analyze_multi_pipeline(image_paths: List[str]):
    representative_image = image_paths[0]

    vehicle_images = detect_vehicles(representative_image, CROP_DIR)
    vehicle_count = len(vehicle_images)

    vehicles = []
    accident_vehicles = []
    has_accident = False

    # 🔥 차종 분류
    vehicle_type_result = predict_vehicle_type(representative_image)

    vehicle_type = (
        vehicle_type_result.get("label")
        if isinstance(vehicle_type_result, dict)
        else vehicle_type_result
    )

    vehicle_type_confidence = (
        vehicle_type_result.get("confidence")
        if isinstance(vehicle_type_result, dict)
        else None
    )

    for idx, v_path in enumerate(vehicle_images, start=1):
        result = predict_accident(v_path)

        vehicles.append({
            "vehicle_id": idx,
            "accident": result["is_accident"],
            "confidence": result.get("confidence"),
            "vehicle_type": vehicle_type,
            "vehicle_type_confidence": vehicle_type_confidence,
        })

        if result["is_accident"]:
            has_accident = True
            filename = os.path.basename(v_path)

            accident_vehicles.append({
                "vehicle_id": idx,
                "crop_path": v_path,
                "crop_url": f"/static/crops/{filename}"
            })

    support_images = [
        f"/static/uploads/{os.path.basename(p)}"
        for p in image_paths[1:]
    ]

    if not has_accident:
        return {
            "mode": "multi",
            "status": "NO_ACCIDENT",
            "vehicle_count": vehicle_count,
            "vehicles": vehicles,
            "accident_vehicle_count": 0,
            "accident_vehicles": [],
            "vehicle": vehicle_type_result,
            "support_images": support_images,
            "damage_result": None,
            "yolo_image_url": None,
            "drivable_result": None,
            "accident": {
                "accident_detected": False,
                "accident_state": "NO_ACCIDENT",
                "accident_type": "UNKNOWN",
                "confidence_level": "LOW",
                "scores": {},
            }
        }

    from app.services.damage_service import detect_damage_by_vehicle_internal

    damage_result = detect_damage_by_vehicle_internal({
        "accident_vehicles": accident_vehicles
    })

    yolo_image_url = None
    image_bytes = None
    try:
        with open(representative_image, "rb") as f:
            image_bytes = f.read()

        annotated_bytes, _ = yolo_service.detect_and_draw(image_bytes)

        filename = f"yolo_{uuid.uuid4().hex}.jpg"
        save_path = os.path.join(ANNOTATED_DIR, filename)

        with open(save_path, "wb") as f:
            f.write(annotated_bytes)

        yolo_image_url = f"/static/annotated/{filename}"
    except Exception as e:
        print("YOLO annotated image failed:", e)

    drivable_result = None
    if image_bytes is not None:
        drivable_result = cnn_service.judge(
            detections=damage_result.get("detections", []),
            image_bytes=image_bytes
        )

    return {
        "mode": "multi",
        "status": "ANALYZED",
        "vehicle_count": vehicle_count,
        "vehicles": vehicles,
        "accident_vehicle_count": len(accident_vehicles),
        "accident_vehicles": accident_vehicles,
        "vehicle": vehicle_type_result,
        "support_images": support_images,
        "damage_result": damage_result,
        "yolo_image_url": yolo_image_url,
        "drivable_result": drivable_result,
        "accident": damage_result.get("accident")
    }
