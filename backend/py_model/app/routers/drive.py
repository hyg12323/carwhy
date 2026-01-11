from fastapi import APIRouter, UploadFile, File, Body
from app.services.drive_cnn_service import CNNService

router = APIRouter(
    prefix="/drive",
    tags=["Drivability"]
)

drive_cnn_service = CNNService()


@router.post("/judge")
async def judge_drivable(
    detections: list = Body(...),
    file: UploadFile = File(...)
):
    image_bytes = await file.read()

    return drive_cnn_service.judge(
        detections=detections,
        image_bytes=image_bytes
    )
