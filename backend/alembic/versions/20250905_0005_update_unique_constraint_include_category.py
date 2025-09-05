"""update unique constraint to include category

Revision ID: 20250905_0005
Revises: 20250826_0004
Create Date: 2025-09-05 17:00:00

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "20250905_0005"
down_revision = "20250826_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the old unique constraint (try both possible names)
    try:
        op.drop_constraint("uq_history_project_code_log_date", "project_history", type_="unique")
    except Exception:
        # Fallback to auto-generated name
        op.drop_constraint("project_history_project_code_log_date_key", "project_history", type_="unique")
    
    # Add the new unique constraint with category
    op.create_unique_constraint(
        "uq_history_project_code_log_date_category", 
        "project_history", 
        ["project_code", "log_date", "category"]
    )


def downgrade() -> None:
    # Drop the new constraint
    op.drop_constraint("uq_history_project_code_log_date_category", "project_history", type_="unique")
    
    # Recreate the old constraint with original name
    op.create_unique_constraint(
        "uq_history_project_code_log_date", 
        "project_history", 
        ["project_code", "log_date"]
    )
