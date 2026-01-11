import os
import uuid
import cv2
from ultralytics import YOLO

yolo_model = YOLO("yolov8n.pt")

VEHICLE_LABELS = {"car", "bus", "truck"}
CONF_THRESHOLD = 0.5   # 필요하면 0.6으로 조절

def detect_vehicles(image_path: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)

    img = cv2.imread(image_path)
    if img is None:
        return []

    results = yolo_model(img)[0]
    crop_paths = []

    for box in results.boxes:
        cls_id = int(box.cls[0])
        label = results.names[cls_id]
        conf = float(box.conf[0])

        # 차량만 + 신뢰도 기준
        if label not in VEHICLE_LABELS:
            continue
        if conf < CONF_THRESHOLD:
            continue

        x1, y1, x2, y2 = map(int, box.xyxy[0])

        h, w = img.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        crop = img[y1:y2, x1:x2]
        if crop.size == 0:
            continue

        crop_path = os.path.join(output_dir, f"{uuid.uuid4()}.jpg")
        cv2.imwrite(crop_path, crop)
        crop_paths.append(crop_path)

    return crop_paths