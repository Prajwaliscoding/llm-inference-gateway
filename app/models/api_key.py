from app.models.base import Base
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from sqlalchemy import DateTime,func


class ApiKey(Base):
    __tablename__="api_keys"

    id:Mapped[int] = mapped_column(primary_key=True)
    hashed_key:Mapped[str] = mapped_column(unique=True, index=True)
    name:Mapped[str] = mapped_column()
    created_at:Mapped[datetime] = mapped_column(DateTime,server_default=func.now())
    is_active:Mapped[bool]=mapped_column(default=True)
