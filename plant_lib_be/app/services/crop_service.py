import math
from sqlalchemy.orm import Session
from app.repositories.crop_repo import CropRepository

class CropService:
    def __init__(self, db: Session) -> None:
        self.repo = CropRepository(db)

    def list_paginated(self, page: int, size: int):
        items, total = self.repo.list_paginated(page=page, size=size)
        pages = math.ceil(total / size) if size else 1
        return {
            "meta": {
                "total": total, "page": page, "size": size,
                "pages": pages, "has_next": page < pages, "has_prev": page > 1
            },
            "items": items,
        }
