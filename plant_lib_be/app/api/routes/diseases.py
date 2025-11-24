from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.deps import get_session
from app.services.disease_service import DiseaseService
from app.schemas.disease import DiseasePage, DiseaseOut

router = APIRouter(prefix="/diseases", tags=["diseases"])

@router.get("/", response_model=DiseasePage)
def list_diseases(
    q: str | None = Query(None, description="Tìm theo tên/triệu chứng"),
    pathogen_type: str | None = Query(None, description="nam|vi_khuan|vi_rut|ve_bet|sau_bo|khac"),
    crop: str | None = Query(None, description="Tên cây trồng (VI)"),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_session),
):
    svc = DiseaseService(db)
    return svc.search_paginated(q=q, pathogen_type=pathogen_type, crop_name=crop, page=page, size=size)

@router.get("/{disease_id}", response_model=DiseaseOut)
def get_disease(disease_id: int, db: Session = Depends(get_session)):
    svc = DiseaseService(db)
    disease = svc.get(disease_id)
    if not disease:
        raise HTTPException(status_code=404, detail="Không tìm thấy bệnh")
    return disease
