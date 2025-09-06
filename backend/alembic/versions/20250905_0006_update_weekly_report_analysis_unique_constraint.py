"""update weekly_report_analysis unique constraint to include category

Revision ID: 20250905_0006
Revises: 20250905_0005
Create Date: 2025-09-05 17:30:00

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "20250905_0006"
down_revision = "20250905_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the old unique constraint
    try:
        op.drop_constraint("uq_analysis_project_cw_lang", "weekly_report_analysis", type_="unique")
    except Exception:
        # Fallback to auto-generated name if the named constraint doesn't exist
        try:
            op.drop_constraint("weekly_report_analysis_project_code_cw_label_language_key", "weekly_report_analysis", type_="unique")
        except Exception:
            # If neither exists, continue (might be a fresh database)
            pass
    
    # Add the new unique constraint with category
    op.create_unique_constraint(
        "uq_analysis_project_cw_lang_category", 
        "weekly_report_analysis", 
        ["project_code", "cw_label", "language", "category"]
    )


def downgrade() -> None:
    # Drop the new constraint
    op.drop_constraint("uq_analysis_project_cw_lang_category", "weekly_report_analysis", type_="unique")
    
    # Recreate the old constraint
    op.create_unique_constraint(
        "uq_analysis_project_cw_lang", 
        "weekly_report_analysis", 
        ["project_code", "cw_label", "language"]
    )
