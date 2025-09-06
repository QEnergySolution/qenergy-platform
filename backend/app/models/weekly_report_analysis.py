from sqlalchemy import String, Numeric, TIMESTAMP, Text as SAText, text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class WeeklyReportAnalysis(Base):
    __tablename__ = "weekly_report_analysis"

    id: Mapped[str] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    project_code: Mapped[str] = mapped_column(String(32), nullable=False)
    category: Mapped[str | None] = mapped_column(String(128))
    cw_label: Mapped[str] = mapped_column(String(8), nullable=False)
    language: Mapped[str] = mapped_column(String(2), nullable=False, server_default="EN")
    risk_lvl: Mapped[float | None] = mapped_column(Numeric(5, 2))
    risk_desc: Mapped[str | None] = mapped_column(String(500))
    similarity_lvl: Mapped[float | None] = mapped_column(Numeric(5, 2))
    similarity_desc: Mapped[str | None] = mapped_column(String(500))
    negative_words: Mapped[dict | None] = mapped_column(JSONB)
    content_hash: Mapped[str | None] = mapped_column(String(32))  # MD5 hash for cache invalidation
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)

    __table_args__ = (
        UniqueConstraint("project_code", "cw_label", "language", "category", name="uq_analysis_project_cw_lang_category"),
    )
