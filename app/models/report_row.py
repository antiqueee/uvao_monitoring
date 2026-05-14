import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ReportRow(Base):
    __tablename__ = "report_rows"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resource_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("resources.id"), nullable=False, index=True
    )
    repost_owner_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    repost_post_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    repost_url: Mapped[str] = mapped_column(Text, nullable=False)
    repost_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    followers_count: Mapped[int] = mapped_column(Integer, nullable=False)
    views_count: Mapped[int | None] = mapped_column(Integer)
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)

    report = relationship("Report", back_populates="rows")
    resource = relationship("Resource", back_populates="report_rows")
