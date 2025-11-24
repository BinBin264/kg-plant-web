# versions/003_apply_disease_images.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text
import unicodedata
import re

# ---- Alembic identifiers ----
revision = "003_apply_disease_images"
down_revision = "002_seed_plant_lib_data"
branch_labels = None
depends_on = None


def _slugify(s: str) -> str:
    """Bỏ dấu tiếng Việt, chuyển thường, thay non a-z0-9 thành '-', trim '-'."""
    if s is None:
        return ""
    s = s.replace("Đ", "D").replace("đ", "d")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def upgrade():
    conn = op.get_bind()

    # Map name -> Plantix ID (100001..100005)
    mapping = {
        "Bệnh thối rễ và cổ rễ ở Táo": "100001",
        "Bệnh phấn trắng": "100002",
        "Bệnh sương mai (mốc sương)": "100003",
        "Bệnh sương mai trên kê": "100004",
        "Bệnh thối đen cây ăn quả": "100005",
    }

    for name, did in mapping.items():
        conn.execute(
            text(
                """
                UPDATE kb.diseases
                   SET image_url = :url
                 WHERE name = :name
                """
            ),
            {"url": f"/assets/images/diseases/{did}.jpg", "name": name},
        )


def downgrade():
    conn = op.get_bind()

    # Khôi phục về convention slug theo name
    names = [
        "Bệnh thối rễ và cổ rễ ở Táo",
        "Bệnh phấn trắng",
        "Bệnh sương mai (mốc sương)",
        "Bệnh sương mai trên kê",
        "Bệnh thối đen cây ăn quả",
    ]

    for name in names:
        slug = _slugify(name)
        conn.execute(
            text(
                """
                UPDATE kb.diseases
                   SET image_url = :url
                 WHERE name = :name
                """
            ),
            {"url": f"/assets/images/diseases/{slug}.jpg", "name": name},
        )
