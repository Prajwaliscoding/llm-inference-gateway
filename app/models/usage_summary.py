from sqlalchemy import ForeignKey, Date, DateTime, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import date,datetime

from app.models.base import Base


class UsageSummary(Base):
    __tablename__ = "usage_summary"
    __table_args__ = (UniqueConstraint("api_key_id", "usage_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    api_key_id: Mapped[int] = mapped_column(ForeignKey("api_keys.id"), index=True)
    usage_date: Mapped[date] = mapped_column(Date)
    total_requests: Mapped[int] = mapped_column(default=0)
    total_cost: Mapped[float] = mapped_column(default=0.0)
    total_tokens: Mapped[int] = mapped_column(default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    