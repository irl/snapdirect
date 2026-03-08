from sqlalchemy.orm import Mapped

from src.models import CustomBase, IdMixin


class Snapshot(CustomBase, IdMixin):
    __tablename__ = "snapshot"

    url: Mapped[str]
