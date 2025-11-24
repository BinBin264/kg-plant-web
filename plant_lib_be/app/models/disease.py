import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.dialects.postgresql import ARRAY
from .base import Base
from .associations import disease_crops

# Giá trị hợp lệ (không dấu) - đồng bộ với CHECK ở migration 001
PATHOGEN_TYPES = {"nam", "vi_khuan", "vi_rut", "ve_bet", "sau_bo", "thieu_chat"}

class Disease(Base):
    __tablename__ = "diseases"
    __table_args__ = {"schema": "kb"}

    id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(sa.Text, nullable=False)                 # Tên bệnh (VI)
    pathogen_type: Mapped[str] = mapped_column(sa.Text, nullable=False)        # nam/vi_khuan/vi_rut/ve_bet/sau_bo/thieu_chat
    symptoms: Mapped[str | None] = mapped_column(sa.Text)                      # Mô tả triệu chứng (VI)
    prevention_steps: Mapped[list[str] | None] = mapped_column(ARRAY(sa.Text)) # Danh sách biện pháp (VI)
    image_url: Mapped[str | None] = mapped_column(sa.Text)                     # Đường dẫn ảnh minh họa

    # Quan hệ N-N với Crop
    crops: Mapped[list["Crop"]] = relationship(
        "Crop",
        secondary=disease_crops,
        back_populates="diseases",
        lazy="selectin",
    )

    @validates("pathogen_type")
    def _validate_pathogen_type(self, key, value: str) -> str:
        if value not in PATHOGEN_TYPES:
            raise ValueError(
                f"pathogen_type '{value}' không hợp lệ. "
                f"Giá trị hợp lệ: {sorted(PATHOGEN_TYPES)}"
            )
        return value
