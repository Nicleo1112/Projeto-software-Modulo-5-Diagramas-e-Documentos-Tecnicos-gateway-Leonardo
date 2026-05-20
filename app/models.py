from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DiagramHistory(Base):
    __tablename__ = "diagram_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_code: Mapped[str] = mapped_column(Text, nullable=False)
    diagram_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    project_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    project_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    classes: Mapped[list] = mapped_column(JSONB, nullable=False)
    plantuml: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
