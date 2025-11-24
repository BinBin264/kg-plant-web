import math
from sqlalchemy.orm import Session
from app.repositories.disease_repo import DiseaseRepository

class DiseaseService:
    def __init__(self, db: Session) -> None:
        self.repo = DiseaseRepository(db)

    def get(self, id_: int):
        return self.repo.get(id_)

    def search_paginated(
        self,
        q: str | None,
        pathogen_type: str | None,
        crop_name: str | None,
        page: int,
        size: int
    ):
        size = max(int(size or 10), 1)
        page = max(int(page or 1), 1)

        items, total = self.repo.list_paginated(
            q=q,
            pathogen_type=pathogen_type,
            crop_name=crop_name,
            page=page,
            size=size,
        )
        pages = math.ceil(total / size) if size else 1
        return {
            "meta": {
                "total": total,
                "page": page,
                "size": size,
                "pages": pages,
                "has_next": page < pages,
                "has_prev": page > 1,
            },
            "items": items,
        }
