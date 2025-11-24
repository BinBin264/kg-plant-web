# Giúp Alembic autogenerate thấy đủ bảng khi cần
from .base import Base
from .crop import Crop
from .disease import Disease
from .associations import disease_crops

__all__ = ["Base", "Crop", "Disease", "disease_crops"]
