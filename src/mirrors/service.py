import random
from datetime import datetime, timedelta
from urllib.parse import urlparse, urlunparse

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.kldscp.client import KLDSCP_SUPPORTED_ORIGINS, get_kaleidoscope_mirror
from src.mirrors.models import Mirror


def _refresh_mirror(db: Session, mirror: str, origin: str, pool: int):
    if mirror.startswith("https://"):
        mirror = mirror[8:]
    existing = (
        db.query(Mirror)
        .filter(Mirror.origin == origin, Mirror.mirror == mirror, Mirror.pool == pool)
        .first()
    )
    if existing:
        existing.last_seen = func.now()
    else:
        db.add(
            Mirror(
                origin=origin,
                mirror=mirror,
                pool=pool,
                first_seen=func.now(),
                last_seen=func.now(),
            )
        )


def refresh_mirrors(db: Session, pool: int, data: dict[str, str | list[str]]):
    for key in data:
        if key.startswith("https://") and key.endswith("/"):
            origin = key[8:-1]
        else:
            origin = key
        if "/" in origin:
            # TODO: flag this to operator
            continue
        if isinstance(data[key], list):
            for mirror in data[key]:
                _refresh_mirror(db, mirror, origin, pool)
        elif isinstance(data[key], str):
            _refresh_mirror(db, data[key], origin, pool)
        else:
            raise TypeError("data must be dict[str, str | list[str]]")
    db.query(Mirror).filter(
        Mirror.pool == pool, Mirror.last_seen < datetime.now() - timedelta(minutes=5)
    ).delete()


def get_mirrors(db: Session, origin: str, pool=None) -> list[str]:
    if pool is None:
        pool = [0, -2]
    elif isinstance(pool, int):
        pool = [pool]
    result = db.query(Mirror).filter(Mirror.origin == origin, Mirror.pool.in_(pool)).all()
    mirrors = [m.mirror for m in result]
    if not mirrors:
        if origin in KLDSCP_SUPPORTED_ORIGINS:
            if (k_mirror := get_kaleidoscope_mirror(origin)) is not None:
                mirrors.append(k_mirror)
    return mirrors


def resolve_mirror(db: Session, url: str) -> str | None:
    parsed = urlparse(url)
    try:
        mirror = random.choice(get_mirrors(db, parsed.netloc))
        return urlunparse(parsed._replace(netloc=f"{mirror}"))
    except IndexError:
        return None
