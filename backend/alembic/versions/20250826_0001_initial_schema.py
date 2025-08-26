"""initial schema

Revision ID: 20250826_0001
Revises: 
Create Date: 2025-08-26 00:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20250826_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # extensions may be required for gen_random_uuid; ensure pgcrypto
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    op.create_table(
        "projects",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_code", sa.String(length=32), nullable=False, unique=True),
        sa.Column("project_name", sa.String(length=255), nullable=False),
        sa.Column("portfolio_cluster", sa.String(length=128), nullable=True),
        sa.Column("status", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_by", sa.String(length=255), nullable=False),
        sa.CheckConstraint("status IN (0,1)", name="ck_projects_status"),
    )
    op.create_index("idx_projects_status", "projects", ["status"]) 

    op.create_table(
        "project_history",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_code", sa.String(length=32), nullable=False),
        sa.Column("category", sa.String(length=128), nullable=True),
        sa.Column("entry_type", sa.String(length=50), nullable=False),
        sa.Column("log_date", sa.Date(), nullable=False),
        sa.Column("cw_label", sa.String(length=8), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("next_actions", sa.Text(), nullable=True),
        sa.Column("owner", sa.String(length=255), nullable=True),
        sa.Column("attachment_url", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_by", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["project_code"], ["projects.project_code"], name="fk_history_project_code", ondelete="RESTRICT"),
        sa.UniqueConstraint("project_code", "log_date", name="uq_history_project_code_log_date"),
        sa.CheckConstraint(
            "entry_type IN ('Report','Issue','Decision','Maintenance','Meeting minutes','Mid-update')",
            name="ck_history_entry_type",
        ),
    )
    op.create_index("idx_project_history_project_code", "project_history", ["project_code"]) 
    op.create_index("idx_project_history_log_date", "project_history", ["log_date"]) 
    op.create_index("idx_project_history_cw_label", "project_history", ["cw_label"]) 

    op.create_table(
        "weekly_report_analysis",
        sa.Column("id", sa.UUID(), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_code", sa.String(length=32), nullable=False),
        sa.Column("category", sa.String(length=128), nullable=True),
        sa.Column("cw_label", sa.String(length=8), nullable=False),
        sa.Column("language", sa.String(length=2), nullable=False, server_default="EN"),
        sa.Column("risk_lvl", sa.Numeric(5, 2), nullable=True),
        sa.Column("risk_desc", sa.String(length=500), nullable=True),
        sa.Column("similarity_lvl", sa.Numeric(5, 2), nullable=True),
        sa.Column("similarity_desc", sa.String(length=500), nullable=True),
        sa.Column("negative_words", sa.dialects.postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("created_by", sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(["project_code"], ["projects.project_code"], name="fk_analysis_project_code", ondelete="RESTRICT"),
        sa.UniqueConstraint("project_code", "cw_label", "language", name="uq_analysis_project_cw_lang"),
        sa.CheckConstraint("risk_lvl IS NULL OR (risk_lvl >= 0 AND risk_lvl <= 100)", name="ck_analysis_risk_lvl"),
        sa.CheckConstraint("similarity_lvl IS NULL OR (similarity_lvl >= 0 AND similarity_lvl <= 100)", name="ck_analysis_similarity_lvl"),
    )
    op.create_index("idx_analysis_project_cw", "weekly_report_analysis", ["project_code", "cw_label"]) 


def downgrade() -> None:
    op.drop_index("idx_analysis_project_cw", table_name="weekly_report_analysis")
    op.drop_table("weekly_report_analysis")

    op.drop_index("idx_project_history_cw_label", table_name="project_history")
    op.drop_index("idx_project_history_log_date", table_name="project_history")
    op.drop_index("idx_project_history_project_code", table_name="project_history")
    op.drop_table("project_history")

    op.drop_index("idx_projects_status", table_name="projects")
    op.drop_table("projects")


