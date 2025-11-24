# versions/004_create_kg_pipeline_tables.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

# ---- Alembic identifiers ----
revision = "004_create_kg_pipeline_tables"
down_revision = "003_apply_disease_images"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "kg_users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("username", sa.String(length=100), nullable=False, unique=True, index=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True, index=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("last_login", sa.DateTime()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )

    op.create_table(
        "kg_user_sessions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("kg_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_token", sa.String(length=255), nullable=False, unique=True, index=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("last_activity", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("ip_address", sa.String(length=45)),
        sa.Column("user_agent", sa.Text()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )

    op.create_table(
        "kg_chat_histories",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(length=36),
            sa.ForeignKey("kg_user_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("user_id", sa.String(length=36), sa.ForeignKey("kg_users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("query_language", sa.String(length=10), server_default=sa.text("'vi'"), nullable=False),
        sa.Column("intent", sa.String(length=50)),
        sa.Column("answer", sa.Text()),
        sa.Column("answer_language", sa.String(length=10)),
        sa.Column("pipeline_data", pg.JSONB(astext_type=sa.Text())),
        sa.Column("image_path", sa.Text()),
        sa.Column("total_results", sa.Integer(), server_default="0", nullable=False),
        sa.Column("processing_time", sa.Integer()),
        sa.Column("from_cache", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("user_rating", sa.Integer()),
        sa.Column("user_feedback", sa.Text()),
    )

    op.create_table(
        "kg_query_caches",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "session_id",
            sa.String(length=36),
            sa.ForeignKey("kg_user_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("query_hash", sa.String(length=64), nullable=False, unique=True, index=True),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("image_path", sa.Text()),
        sa.Column("cached_result", pg.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("hit_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("last_accessed", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table("kg_query_caches")
    op.drop_table("kg_chat_histories")
    op.drop_table("kg_user_sessions")
    op.drop_table("kg_users")
