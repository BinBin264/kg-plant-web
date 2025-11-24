import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base
from .associations import disease_crops

class Crop(Base):
    __tablename__ = "crops"
    __table_args__ = {"schema": "kb"}

    id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)  # Tên cây trồng (VI)

    diseases: Mapped[list["Disease"]] = relationship(
        "Disease",
        secondary=disease_crops,
        back_populates="crops",
        lazy="selectin",
    )
