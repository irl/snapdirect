from sqlalchemy.orm import Session

from src.snapshots.models import Snapshot


def resolve_snapshot(db: Session, url: str) -> str | None:
    s = db.query(Snapshot).filter(Snapshot.url == url, Snapshot.pool == 0).first()
    return s.link if s else None
