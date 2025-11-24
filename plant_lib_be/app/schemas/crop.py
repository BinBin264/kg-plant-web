# app/schemas/crop.py
from pydantic import BaseModel
from typing import List
from .common import PageMeta  # nếu bạn dùng phân trang

class CropOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class CropPage(BaseModel):
    meta: PageMeta
    items: List[CropOut]
