"""add source_text to project_history

Revision ID: 20250826_0004
Revises: 20250826_0003
Create Date: 2025-08-26 02:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20250826_0004"
down_revision = "20250826_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    col_exists = bind.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='project_history' AND column_name='source_text')"
        )
    ).scalar()
    if not col_exists:
        op.add_column("project_history", sa.Column("source_text", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("project_history", "source_text")


