from pydantic import BaseModel, Field
from typing import Optional, List
from .crop import CropOut
from .common import PageMeta

class DiseaseOut(BaseModel):
    id: int
    name: str
    pathogen_type: str
    symptoms: Optional[str] = None
    prevention_steps: Optional[List[str]] = None
    image_url: Optional[str] = None
    crops: List[CropOut] = Field(default_factory=list)

    class Config:
        # Nếu bạn đang ở Pydantic v2, cân nhắc:
        # from pydantic import ConfigDict
        # model_config = ConfigDict(from_attributes=True)
        from_attributes = True

class DiseasePage(BaseModel):
    meta: PageMeta
    items: List[DiseaseOut]
