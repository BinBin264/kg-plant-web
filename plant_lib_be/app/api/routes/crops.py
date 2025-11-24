from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.api.deps import get_session
from app.services.crop_service import CropService
from app.schemas.crop import CropPage

router = APIRouter(prefix="/crops", tags=["crops"])

@router.get("/", response_model=CropPage)
def list_crops(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_session),
):
    return CropService(db).list_paginated(page=page, size=size)
