import os
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile, status

# Đường dẫn assets/uploads
ROOT_DIR = Path(__file__).resolve().parents[2]  # .../app
ASSETS_DIR = ROOT_DIR.parent / "assets"
UPLOAD_DIR = ASSETS_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("/", summary="Upload ảnh, trả về path trong /assets/uploads")
async def upload_image(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chỉ hỗ trợ upload ảnh",
        )

    # Tên file an toàn + uuid
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in {".jpg", ".jpeg", ".png", ".bmp", ".gif"}:
        raise HTTPException(status_code=400, detail="Định dạng ảnh không hợp lệ")

    new_name = f"{uuid.uuid4().hex}{ext}"
    dest_path = UPLOAD_DIR / new_name

    try:
        content = await file.read()
        with open(dest_path, "wb") as f:
            f.write(content)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Lưu file thất bại: {exc}")

    # Trả về path để FE gọi qua /assets/...
    public_path = f"/assets/uploads/{new_name}"
    return {"path": public_path}
