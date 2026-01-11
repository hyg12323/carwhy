# app/services/damage_service.py

from app.services.yolo_service import YoloService
from app.services.drive_cnn_service import CNNService
from app.services.accident_rule_service import estimate_accident_type

yolo_service = YoloService()
cnn_service = CNNService()


def detect_damage_by_vehicle_internal(payload: dict):
    """
    payload = {
        "accident_vehicles": [
            {"vehicle_id": int, "crop_path": str}
        ]
    }
    """
    vehicle_results = []
    all_detections = []
    drivable_vehicles = []

    for v in payload.get("accident_vehicles", []):
        vehicle_id = v["vehicle_id"]

        try:
            with open(v["crop_path"], "rb") as f:
                image_bytes = f.read()
        except FileNotFoundError:
            vehicle_results.append({
                "vehicle_id": vehicle_id,
                "damages": [],
                "error": "crop_image_not_found"
            })
            continue

        # =========================
        # YOLO 파손 탐지 (차량 crop 기준)
        # =========================
        result = yolo_service.detect(image_bytes)
        detections = result.get("detections", [])

        # 🔥 vehicle_id를 파손 bbox에 붙인다
        for d in detections:
            d["vehicle_id"] = vehicle_id

        vehicle_results.append({
            "vehicle_id": vehicle_id,
            "damages": detections
        })

        all_detections.extend(detections)

        # =========================
        # 🚗 CNN 주행 판단 (차량 단위)
        # =========================
        drive_result = cnn_service.judge(
            detections=detections,     # 🔥 이 차량의 파손만
            image_bytes=image_bytes    # 🔥 이 차량 crop 이미지
        )

        if drive_result.get("vehicles"):
            drivable_vehicles.append(drive_result["vehicles"][0])

    # =========================
    # 파손 자체가 없는 경우
    # =========================
    if not all_detections:
        accident = estimate_accident_type(
            detections=[],
            mode="single"
        )

        return {
            "status": "NO_DAMAGE_DETECTED",
            "vehicles": vehicle_results,
            "drivable": {"vehicles": []},
            "accident": accident
        }

    # =========================
    # 사고 판단 (rule 기반, 전체 기준)
    # =========================
    accident = estimate_accident_type(
        detections=all_detections,
        mode="single"
    )

    return {
        "status": "DETECTED",
        "vehicles": vehicle_results,
        "drivable": {
            "vehicles": drivable_vehicles   # 🔥 차량 수만큼만
        },
        "accident": accident
    }
