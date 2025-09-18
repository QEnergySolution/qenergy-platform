"""update unique constraint to include category

Revision ID: 20250905_0005
Revises: 20250826_0004
Create Date: 2025-09-05 17:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20250905_0005"
down_revision = "20250826_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    # Drop the old unique constraint if it exists (try both names)
    for old_name in ("uq_history_project_code_log_date", "project_history_project_code_log_date_key"):
        exists = bind.execute(sa.text("SELECT EXISTS (SELECT 1 FROM pg_constraint WHERE conname=:n)"), {"n": old_name}).scalar()
        if exists:
            try:
                op.drop_constraint(old_name, "project_history", type_="unique")
            except Exception:
                pass

    # Add the new unique constraint with category if missing
    new_name = "uq_history_project_code_log_date_category"
    exists_new = bind.execute(sa.text("SELECT EXISTS (SELECT 1 FROM pg_constraint WHERE conname=:n)"), {"n": new_name}).scalar()
    if not exists_new:
        try:
            op.create_unique_constraint(
                new_name,
                "project_history",
                ["project_code", "log_date", "category"],
            )
        except Exception:
            pass


def downgrade() -> None:
    # Drop the new constraint
    op.drop_constraint("uq_history_project_code_log_date_category", "project_history", type_="unique")
    
    # Recreate the old constraint with original name
    op.create_unique_constraint(
        "uq_history_project_code_log_date", 
        "project_history", 
        ["project_code", "log_date"]
    )
