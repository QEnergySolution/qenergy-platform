"""add_content_hash_to_weekly_report_analysis

Revision ID: 20250905_0007
Revises: 20250905_0006
Create Date: 2024-09-05 10:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250905_0007'
down_revision = '20250905_0006'
branch_labels = None
depends_on = None


def upgrade():
    """Add content_hash column to weekly_report_analysis table"""
    op.add_column('weekly_report_analysis', sa.Column('content_hash', sa.String(32), nullable=True))


def downgrade():
    """Remove content_hash column from weekly_report_analysis table"""
    op.drop_column('weekly_report_analysis', 'content_hash')
