from urllib.parse import urlparse

from fastapi import APIRouter

from src.database import DbSession
from src.mirrors.schemas import MirrorLinks, RedirectorData
from src.mirrors.service import refresh_mirrors
from src.security import ApiKey

router = APIRouter()


@router.post("/api/v1/mirrors")
def update_mirrors(db: DbSession, auth: ApiKey, data: RedirectorData):
    for pool, data in enumerate(data.pools):
        refresh_mirrors(db, pool, data.origins)
    db.commit()


@router.get("/api/v1/resolve", response_model=MirrorLinks)
def resolve_mirror(db: DbSession, auth: ApiKey, url: str):
    parsed = urlparse(url)
    try:
        mirror = resolve_mirror(db, parsed.netloc)
        return {"url": parsed._replace(netloc=mirror)}
    except ValueError:
        return {"mirrors": []}
