from sqlalchemy.orm import Mapped

from src.models import TimestampMixin, IdMixin, CustomBase


class Link(CustomBase, IdMixin, TimestampMixin):
    __tablename__ = "link"

    url: Mapped[str]
    link_domain: Mapped[str]
    pool: Mapped[int]
