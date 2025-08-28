from sqlalchemy import String, Date, Text as SAText, TIMESTAMP, text
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class ProjectHistory(Base):
    __tablename__ = "project_history"

    id: Mapped[str] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    project_code: Mapped[str] = mapped_column(String(32), nullable=False)
    category: Mapped[str | None] = mapped_column(String(128))
    entry_type: Mapped[str] = mapped_column(String(50), nullable=False)
    log_date: Mapped[str] = mapped_column(Date, nullable=False)
    cw_label: Mapped[str | None] = mapped_column(String(8))
    title: Mapped[str | None] = mapped_column(String(255))
    summary: Mapped[str] = mapped_column(SAText, nullable=False)
    next_actions: Mapped[str | None] = mapped_column(SAText)
    source_text: Mapped[str | None] = mapped_column(SAText)
    owner: Mapped[str | None] = mapped_column(String(255))
    attachment_url: Mapped[str | None] = mapped_column(String(1024))
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    updated_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)
    updated_by: Mapped[str] = mapped_column(String(255), nullable=False)


