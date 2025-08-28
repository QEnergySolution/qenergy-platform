from sqlalchemy import String, BigInteger, TIMESTAMP, CHAR, Date, Text as SAText, text
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class ReportUpload(Base):
    __tablename__ = "report_uploads"

    id: Mapped[str] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    original_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(CHAR(64), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    uploaded_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)
    parsed_at: Mapped[str | None] = mapped_column(TIMESTAMP(timezone=True))
    cw_label: Mapped[str | None] = mapped_column(String(8))
    doc_date: Mapped[str | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(SAText)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    updated_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)
    updated_by: Mapped[str] = mapped_column(String(255), nullable=False)


