"""add report_uploads and source_upload_id fk

Revision ID: 20250826_0003
Revises: 20250826_0002
Create Date: 2025-08-26 01:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20250826_0003"
down_revision = "20250826_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    # Create report_uploads table if it does not exist
    table_exists = bind.execute(sa.text("SELECT to_regclass('public.report_uploads') IS NOT NULL")).scalar()
    if not table_exists:
        op.create_table(
            "report_uploads",
            sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("original_filename", sa.String(length=512), nullable=False),
            sa.Column("storage_path", sa.String(length=1024), nullable=False),
            sa.Column("mime_type", sa.String(length=128), nullable=False),
            sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
            sa.Column("sha256", sa.CHAR(length=64), nullable=False, unique=True),
            sa.Column("status", sa.String(length=16), nullable=False),
            sa.Column("uploaded_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.Column("parsed_at", sa.TIMESTAMP(timezone=True), nullable=True),
            sa.Column("cw_label", sa.String(length=8), nullable=True),
            sa.Column("doc_date", sa.Date(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.Column("created_by", sa.String(length=255), nullable=False),
            sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
            sa.Column("updated_by", sa.String(length=255), nullable=False),
            sa.CheckConstraint(
                "status IN ('received','parsed','failed','partial')",
                name="ck_report_uploads_status",
            ),
        )

    # Ensure source_upload_id column exists on project_history
    col_exists = bind.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='project_history' AND column_name='source_upload_id')"
        )
    ).scalar()
    if not col_exists:
        op.add_column(
            "project_history",
            sa.Column("source_upload_id", sa.UUID(), nullable=True),
        )

    # Create FK if not existing (accept either historical or new name)
    fk_exists = bind.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM pg_constraint WHERE conname IN ('fk_history_source_upload_id','fk_project_history_source_upload'))"
        )
    ).scalar()
    if not fk_exists:
        try:
            op.create_foreign_key(
                "fk_history_source_upload_id",
                "project_history",
                "report_uploads",
                ["source_upload_id"],
                ["id"],
                ondelete="SET NULL",
            )
        except Exception:
            # Ignore if concurrently created
            pass

    # Create index if not existing (accept either historical or new name)
    idx_exists = bind.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM pg_class WHERE relkind='i' AND relname IN ('idx_project_history_source_upload_id','idx_project_history_source_upload'))"
        )
    ).scalar()
    if not idx_exists:
        try:
            op.create_index(
                "idx_project_history_source_upload_id",
                "project_history",
                ["source_upload_id"],
            )
        except Exception:
            pass


def downgrade() -> None:
    op.drop_index("idx_project_history_source_upload_id", table_name="project_history")
    op.drop_constraint("fk_history_source_upload_id", "project_history", type_="foreignkey")
    op.drop_column("project_history", "source_upload_id")

    op.drop_table("report_uploads")


