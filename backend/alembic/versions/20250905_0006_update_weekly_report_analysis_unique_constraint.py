"""update weekly_report_analysis unique constraint to include category

Revision ID: 20250905_0006
Revises: 20250905_0005
Create Date: 2025-09-05 17:30:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20250905_0006"
down_revision = "20250905_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    # Drop old unique constraints if they exist
    for old_name in ("uq_analysis_project_cw_lang", "weekly_report_analysis_project_code_cw_label_language_key"):
        exists = bind.execute(sa.text("SELECT EXISTS (SELECT 1 FROM pg_constraint WHERE conname=:n)"), {"n": old_name}).scalar()
        if exists:
            try:
                op.drop_constraint(old_name, "weekly_report_analysis", type_="unique")
            except Exception:
                pass

    # Create the new unique constraint if missing
    new_name = "uq_analysis_project_cw_lang_category"
    exists_new = bind.execute(sa.text("SELECT EXISTS (SELECT 1 FROM pg_constraint WHERE conname=:n)"), {"n": new_name}).scalar()
    if not exists_new:
        try:
            op.create_unique_constraint(
                new_name,
                "weekly_report_analysis",
                ["project_code", "cw_label", "language", "category"],
            )
        except Exception:
            pass


def downgrade() -> None:
    # Drop the new constraint
    op.drop_constraint("uq_analysis_project_cw_lang_category", "weekly_report_analysis", type_="unique")
    
    # Recreate the old constraint
    op.create_unique_constraint(
        "uq_analysis_project_cw_lang", 
        "weekly_report_analysis", 
        ["project_code", "cw_label", "language"]
    )
