from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func, distinct
from app.models.disease import Disease
from app.models.crop import Crop

class DiseaseRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, id_: int) -> Disease | None:
        # Trả về None nếu không tìm thấy
        return self.db.get(Disease, id_)

    def list_paginated(
        self,
        q: str | None = None,
        pathogen_type: str | None = None,
        crop_name: str | None = None,
        page: int = 1,
        size: int = 10,
    ) -> tuple[list[Disease], int]:

        filters = []
        join_crop = False

        if q:
            like = f"%{q}%"
            # Tìm theo tên & triệu chứng (case-insensitive)
            filters.append(or_(Disease.name.ilike(like), Disease.symptoms.ilike(like)))
        if pathogen_type:
            filters.append(Disease.pathogen_type == pathogen_type)
        if crop_name:
            join_crop = True
            filters.append(Crop.name == crop_name)

        # ----- total count -----
        count_stmt = select(func.count(distinct(Disease.id))).select_from(Disease)
        if join_crop:
            count_stmt = count_stmt.join(Disease.crops)
        if filters:
            count_stmt = count_stmt.where(*filters)
        total: int = self.db.scalar(count_stmt) or 0

        # ----- page data -----
        size = max(int(size or 10), 1)
        page = max(int(page or 1), 1)
        offset = (page - 1) * size

        if join_crop:
            # Khi join có thể trùng -> dùng DISTINCT
            stmt = select(Disease).join(Disease.crops)
            if filters:
                stmt = stmt.where(*filters)
            stmt = stmt.distinct()
        else:
            stmt = select(Disease)
            if filters:
                stmt = stmt.where(*filters)

        stmt = stmt.order_by(Disease.name.asc()).limit(size).offset(offset)
        items = self.db.execute(stmt).scalars().all()
        return items, total
