from fastapi import APIRouter, HTTPException, Header, Query, BackgroundTasks
from starlette import status
from starlette.responses import RedirectResponse

from src.config import settings
from src.database import DbSession
from src.link.models import Link
from src.mirrors.service import resolve_mirror
from src.security import ApiKey
from src.snapshots.router import snap
from src.utils import hashids

router = APIRouter()


@router.get("/api/v1/link")
def get_link(background_tasks: BackgroundTasks, db: DbSession, auth: ApiKey, url: str, type_: str = Query(default="auto", alias="type")):
    if auth and type_ in ["auto", "live", "live-short"]:
        s = db.query(Link).filter(Link.url == url, Link.pool == 0).first()
        if not s and resolve_mirror(db, url):
            s = Link(url=url, pool=0, link_domain=settings.LINK_DOMAIN)
            db.add(s)
            db.commit()
        if s:
            return {"url": f"https://{s.link_domain}/{hashids.encode(s.id)}"}
    if type_ in ["auto", "snapshot"]:
        if isinstance(s := snap(background_tasks, db, auth, url), dict):
            return s
    if type_ in ["auto", "live", "live-direct"]:
        if mirror := resolve_mirror(db, url):
            return {"url": mirror}
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)


@router.get("/{hash_}")
def resolve_hash(db: DbSession, hash_: str, host: str = Header(settings.LINK_DOMAIN)):
    try:
        id_ = hashids.decode(hash_)[0]
    except IndexError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    link = (
        db.query(Link)
        .filter(Link.id == id_, Link.link_domain == host.lower().strip())
        .first()
    )
    if not link:
        return RedirectResponse(
            settings.INVALID_URL,
            status_code=status.HTTP_302_FOUND,
            headers={"Referrer-Policy": "no-referrer"},
        )
    if host.lower().strip() != settings.API_DOMAIN:
        return RedirectResponse(
            resolve_mirror(db, link.url),
            status_code=status.HTTP_302_FOUND,
            headers={"Referrer-Policy": "no-referrer"},
        )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
