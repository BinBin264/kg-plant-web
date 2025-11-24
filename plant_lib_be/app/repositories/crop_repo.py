from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.models.crop import Crop

class CropRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_paginated(self, page: int = 1, size: int = 10):
        total = self.db.scalar(select(func.count(Crop.id))) or 0
        offset = max(page - 1, 0) * size
        stmt = select(Crop).order_by(Crop.name.asc()).limit(size).offset(offset)
        items = self.db.execute(stmt).scalars().all()
        return items, total
