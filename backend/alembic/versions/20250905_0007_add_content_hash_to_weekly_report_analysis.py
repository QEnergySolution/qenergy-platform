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
    bind = op.get_bind()
    col_exists = bind.execute(
        sa.text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='weekly_report_analysis' AND column_name='content_hash')"
        )
    ).scalar()
    if not col_exists:
        op.add_column('weekly_report_analysis', sa.Column('content_hash', sa.String(32), nullable=True))


def downgrade():
    """Remove content_hash column from weekly_report_analysis table"""
    op.drop_column('weekly_report_analysis', 'content_hash')
