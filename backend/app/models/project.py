from sqlalchemy import String, Integer, TIMESTAMP, text
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    project_code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    portfolio_cluster: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)
    updated_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=text("NOW()"), nullable=False)
    updated_by: Mapped[str] = mapped_column(String(255), nullable=False)


