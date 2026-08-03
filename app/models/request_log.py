from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, DateTime, func
from datetime import datetime
from app.models.base import Base


class RequestLog(Base):

    __tablename__ = "requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    api_key_id: Mapped[int] = mapped_column(ForeignKey("api_keys.id"), index=True)
    model: Mapped[str] = mapped_column()
    provider: Mapped[str] = mapped_column()
    prompt_tokens: Mapped[int] = mapped_column()
    completion_tokens: Mapped[int] = mapped_column()
    cost: Mapped[float] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())



