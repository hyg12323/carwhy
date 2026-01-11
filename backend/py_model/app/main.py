from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles   # ✅ 추가
from dotenv import load_dotenv

from app.routers import (
    damage,
    pipeline,
    gpt_router
)

# =========================
# env 로드
# =========================
load_dotenv()

# =========================
# FastAPI 앱 생성
# =========================
app = FastAPI(title="Car Damage Detection API")

# =========================
# 🔥 CORS 설정 (그대로 둠)
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# 🔥 static mount (필수)
# =========================
app.mount("/static", StaticFiles(directory="static"), name="static")

# =========================
# Routers
# =========================
app.include_router(damage.router)
app.include_router(pipeline.router)
app.include_router(gpt_router.router)
