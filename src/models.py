from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, JSON, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from src.database import metadata


class CustomBase(DeclarativeBase):
    type_annotation_map = {
        datetime: DateTime(timezone=True),
        dict[str, Any]: JSON,
    }
    metadata = metadata


class ActivatedMixin:
    active: Mapped[bool] = mapped_column(default=True)


class DeletedTimestampMixin:
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)


class DescriptionMixin:
    description: Mapped[str]


class IdMixin:
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())
