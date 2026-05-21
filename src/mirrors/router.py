from urllib.parse import urlparse

from fastapi import APIRouter

from src.database import DbSession
from src.mirrors.schemas import MirrorLinks, RedirectorData
from src.mirrors.service import refresh_mirrors, resolve_mirror as resolve_mirror_service
from src.security import ApiKey

router = APIRouter()


@router.post("/api/v1/mirrors")
def update_mirrors(db: DbSession, auth: ApiKey, data: RedirectorData):
    for pool, pool_data in enumerate(data.pools):
        refresh_mirrors(db, pool, pool_data.origins)
    db.commit()
