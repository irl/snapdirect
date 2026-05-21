from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column

from src.models import CustomBase, IdMixin


class Mirror(CustomBase, IdMixin):
    __tablename__ = "mirror"

    origin: Mapped[str]
    pool: Mapped[int]
    mirror: Mapped[str]
    first_seen: Mapped[datetime]
    last_seen: Mapped[datetime]
    # TODO: Record hits when a redirect goes to the mirror
    hits: Mapped[int] = mapped_column(default=0)
