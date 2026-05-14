import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ResourceType(str, enum.Enum):
    okrug_community = "okrug_community"
    district_community = "district_community"
    lom_personal = "lom_personal"
    other = "other"


class Resource(Base):
    __tablename__ = "resources"
    __table_args__ = (UniqueConstraint("network_id", "vk_owner_id", name="uq_resource_network_owner"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    network_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("networks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vk_owner_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    vk_screen_name: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_type: Mapped[ResourceType] = mapped_column(
        Enum(ResourceType, name="resource_type"), nullable=False
    )
    category_label: Mapped[str | None] = mapped_column(String(128))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    network = relationship("Network", back_populates="resources")
    report_rows = relationship("ReportRow", back_populates="resource")

    @property
    def category_name(self) -> str:
        labels = {
            ResourceType.okrug_community: "окружное сообщество",
            ResourceType.district_community: "районное сообщество",
            ResourceType.lom_personal: "личная страница ЛОМа",
        }
        if self.resource_type == ResourceType.other:
            return self.category_label or "иной ресурс"
        return labels[self.resource_type]
