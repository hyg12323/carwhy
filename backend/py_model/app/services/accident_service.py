import os
import numpy as np
import onnxruntime as ort
from PIL import Image

# =========================
# 설정
# =========================
IMG_SIZE = 224
CLASS_NAMES = ["accident", "normal"]

BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(
    BASE_DIR,
    "..",
    "..",
    "models",
    "accident_model.onnx"
)

# =========================
# 모델 로드 (서버 시작 시 1회)
# =========================
session = ort.InferenceSession(
    MODEL_PATH,
    providers=["CPUExecutionProvider"]
)
input_name = session.get_inputs()[0].name

# =========================
# 이미지 전처리
# =========================
def _preprocess_image(img_path: str) -> np.ndarray:
    img = Image.open(img_path).convert("RGB")
    img = img.resize((IMG_SIZE, IMG_SIZE))
    x = np.array(img).astype(np.float32) / 255.0
    x = np.expand_dims(x, axis=0)  # (1, 224, 224, 3)
    return x

# =========================
# 사고 여부 예측
# =========================
def predict_accident(img_path: str, threshold: float = 0.5) -> dict:
    x = _preprocess_image(img_path)

    probs = session.run(None, {input_name: x})[0][0]
    accident_prob = float(probs[0])  # 0번 = accident

    return {
        "is_accident": accident_prob >= threshold,
        "confidence": accident_prob,
        "probabilities": {
            CLASS_NAMES[i]: float(probs[i])
            for i in range(len(CLASS_NAMES))
        }
    }
