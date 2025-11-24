# app/main.py
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.routes.diseases import router as diseases_router
from app.api.routes.crops import router as crops_router
from app.api.routes.kg_pipeline import router as kg_router
from app.api.routes.upload import router as upload_router

app = FastAPI(title="Plant Lib API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "https://hcknplpr-3000.asse.devtunnels.ms"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Static paths ===
# Project structure giả định:
# PROJECT_ROOT/
# ├─ app/
# │  └─ main.py
# └─ assets/
#    └─ images/
#       └─ diseases/
BASE_DIR = Path(__file__).resolve().parent.parent      # → PROJECT_ROOT/app → parent = PROJECT_ROOT
ASSETS_DIR = BASE_DIR / "assets"
DISEASE_IMG_DIR = ASSETS_DIR / "images" / "diseases"

print("[STATIC] ASSETS_DIR      :", ASSETS_DIR)
print("[STATIC] DISEASE_IMG_DIR :", DISEASE_IMG_DIR)

if not DISEASE_IMG_DIR.exists():
    print("[WARN] Diseases image dir not found:", DISEASE_IMG_DIR)

# 1) Mount /assets → dùng được đúng path API trả về: /assets/images/diseases/100001.jpg
app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")

# 2) Mount /images → truy cập trực tiếp: /images/100001.jpg
app.mount("/images", StaticFiles(directory=str(DISEASE_IMG_DIR)), name="images")

# 3) (tuỳ chọn) /image/{filename} → /image/100001.jpg
@app.get("/image/{filename}")
def get_image(filename: str):
    file_path = (DISEASE_IMG_DIR / filename).resolve()

    # Chặn path traversal
    if DISEASE_IMG_DIR not in file_path.parents:
        raise HTTPException(status_code=400, detail="Invalid path")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Not found")

    return FileResponse(str(file_path))

# Health
@app.get("/health")
def health():
    return {"status": "ok"}

# Routers
app.include_router(crops_router)
app.include_router(diseases_router)
app.include_router(kg_router)
app.include_router(upload_router)
