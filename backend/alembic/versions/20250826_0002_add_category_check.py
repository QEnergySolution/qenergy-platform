"""add category check on project_history

Revision ID: 20250826_0002
Revises: 20250826_0001
Create Date: 2025-08-26 00:30:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20250826_0002"
down_revision = "20250826_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    exists = bind.execute(sa.text("SELECT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='ck_history_category')")).scalar()
    if not exists:
        op.execute(
            """
            ALTER TABLE project_history
            ADD CONSTRAINT ck_history_category
            CHECK (category IS NULL OR category IN ('Development','EPC','Finance','Investment'))
            """
        )


def downgrade() -> None:
    op.execute("ALTER TABLE project_history DROP CONSTRAINT IF EXISTS ck_history_category")


