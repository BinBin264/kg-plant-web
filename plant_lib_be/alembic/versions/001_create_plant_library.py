# versions/001_init_plant_lib_lite.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# ---- Alembic identifiers ----
revision = "001_init_plant_lib_lite"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # (Tùy chọn) bật pg_trgm để search gần đúng tiếng Việt
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    # Schema riêng
    op.execute("CREATE SCHEMA IF NOT EXISTS kb;")

    # ===================== TABLE: crops =====================
    op.create_table(
        "crops",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.Text(), nullable=False),
        schema="kb",
    )

    # ===================== TABLE: diseases =====================
    op.create_table(
        "diseases",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.Text(), nullable=False),
        # pathogen_type: nhóm mầm bệnh (không dấu)
        sa.Column("pathogen_type", sa.Text(), nullable=False),
        sa.Column("symptoms", sa.Text()),
        sa.Column("prevention_steps", pg.ARRAY(sa.Text())),
        # chỉ cần image_url bên diseases
        sa.Column("image_url", sa.Text(), nullable=True),
        schema="kb",
    )

    # Ràng buộc nhóm mầm bệnh
    op.create_check_constraint(
        "ck_diseases_pathogen_type",
        "diseases",
        "pathogen_type IN ('nam','vi_khuan','vi_rut','ve_bet','sau_bo','thieu_chat')",
        schema="kb",
    )

    # ================ TABLE: disease_crops (N-N) ================
    op.create_table(
        "disease_crops",
        sa.Column("disease_id", sa.BigInteger(), nullable=False),
        sa.Column("crop_id", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(["disease_id"], ["kb.diseases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["crop_id"], ["kb.crops.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("disease_id", "crop_id"),
        schema="kb",
    )

    # ======================== Indexes ========================
    op.create_index(
        "ix_diseases_name_trgm",
        "diseases", ["name"],
        schema="kb",
        postgresql_using="gin",
        postgresql_ops={"name": "gin_trgm_ops"},
    )
    op.create_index("ix_diseases_pathogen_type", "diseases", ["pathogen_type"], schema="kb")
    op.create_index("ix_dc_disease", "disease_crops", ["disease_id"], schema="kb")
    op.create_index("ix_dc_crop", "disease_crops", ["crop_id"], schema="kb")


def downgrade():
    # Xoá index
    op.drop_index("ix_dc_crop", table_name="disease_crops", schema="kb")
    op.drop_index("ix_dc_disease", table_name="disease_crops", schema="kb")
    op.drop_index("ix_diseases_pathogen_type", table_name="diseases", schema="kb")
    op.drop_index("ix_diseases_name_trgm", table_name="diseases", schema="kb")

    # Xoá bảng
    op.drop_table("disease_crops", schema="kb")
    op.drop_table("diseases", schema="kb")
    op.drop_table("crops", schema="kb")

    # Xoá schema & extension (tuỳ chọn)
    op.execute("DROP SCHEMA IF EXISTS kb CASCADE;")
    op.execute("DROP EXTENSION IF EXISTS pg_trgm;")
