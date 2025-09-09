"""add project_name to project_history

Revision ID: 20250906_0008
Revises: 20250905_0007
Create Date: 2025-09-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250906_0008'
down_revision = '20250905_0007'
branch_labels = None
depends_on = None


def upgrade():
    # Add nullable project_name column
    op.add_column('project_history', sa.Column('project_name', sa.String(length=255), nullable=True))

    # Backfill from projects table where possible
    op.execute(
        """
        UPDATE project_history ph
        SET project_name = p.project_name
        FROM projects p
        WHERE p.project_code = ph.project_code AND ph.project_name IS NULL
        """
    )


def downgrade():
    op.drop_column('project_history', 'project_name')
