from datetime import datetime
from enum import Enum

from sqlalchemy.orm import Mapped

from src.models import (
    CustomBase,
    IdMixin,
    DeletedTimestampMixin,
    TimestampMixin,
)
from src.google.config import settings as google_settings
from src.utils import hashids


class SnapshotProvider(Enum):
    GOOGLE = "google"
    # TODO: when adding make sure to update alembic migration with
    #       op.execute("ALTER TYPE snapshotprovider ADD VALUE 'aws'")
    # AWS = "aws"
    # OVH = "ovh"
    # ORACLE = "oracle"


# class SnapshotConfiguration(CustomBase, IdMixin, TimestampMixin, DeletedTimestampMixin, DescriptionMixin):
#     __tablename__ = "snapshot_template"
#
#     domain: Mapped[str]
#     path: Mapped[str]
#     configuration: Mapped[dict[str, Any]]


class SnapshotState(Enum):
    PENDING = "pending"
    FAILED = "failed"
    UPDATING = "updating"
    FROZEN = "frozen"
    EXPIRED = "expired"


class Snapshot(CustomBase, IdMixin, TimestampMixin, DeletedTimestampMixin):
    __tablename__ = "snapshot"

    url: Mapped[str]
    pool: Mapped[int]
    snapshot_state: Mapped[SnapshotState]
    provider: Mapped[SnapshotProvider]
    snapshot_published_at: Mapped[datetime | None]

    @property
    def link(self) -> str:
        if self.provider == SnapshotProvider.GOOGLE:
            return f"https://storage.googleapis.com/{google_settings.BUCKET_NAME}/{hashids.encode(self.id)}.html"
        return "unknown-provider"  # impossible because all enum options
