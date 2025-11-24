import sqlalchemy as sa
from .base import Base

# Bảng nối N-N giữa bệnh và cây trồng
disease_crops = sa.Table(
    "disease_crops",
    Base.metadata,
    sa.Column("disease_id", sa.BigInteger, sa.ForeignKey("kb.diseases.id", ondelete="CASCADE"), primary_key=True),
    sa.Column("crop_id",    sa.BigInteger, sa.ForeignKey("kb.crops.id", ondelete="CASCADE"), primary_key=True),
    schema="kb",
)
