from fastapi import APIRouter, HTTPException, BackgroundTasks
from starlette import status
from starlette.responses import HTMLResponse

from src.database import DbSession
from src.security import ApiKey
from src.snapshots.config import config_for_url
from src.snapshots.models import Snapshot, SnapshotState, SnapshotProvider
from src.config import settings
from src.snapshots.client import SnapshotCamera
from src.snapshots.schemas import SnapshotContext
from src.snapshots.tasks import generate_snapshot

router = APIRouter()


@router.get(
    "/api/v1/snap-context",
    summary="Generate the context used by the snapshot template for debugging purposes.",
    response_model=SnapshotContext,
)
def context(auth: ApiKey, url: str = "https://www.bbc.com/russian/articles/ckgeey4dqgxo"):
    if settings.ENVIRONMENT.is_debug or auth:
        ctx = SnapshotCamera(url).get_context()
        if ctx is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, detail="No configuration for URL"
            )
        return ctx
    raise HTTPException(status.HTTP_404_NOT_FOUND)


@router.get(
    "/api/v1/snap-preview",
    summary="Generate a rendered snapshot template for debugging purposes.",
    response_class=HTMLResponse,
)
def parse(auth: ApiKey, url: str = "https://www.bbc.com/russian/articles/ckgeey4dqgxo"):
    if settings.ENVIRONMENT.is_debug or auth:
        return SnapshotCamera(url).render()
    raise HTTPException(status.HTTP_403_FORBIDDEN)


@router.get(
    "/api/v1/snap",
    summary="Generate a rendered snapshot template and upload to Google Cloud Storage.",
)
def snap(
    background_tasks: BackgroundTasks,
    db: DbSession,
    auth: ApiKey,
    url: str = "https://www.bbc.com/russian/articles/ckgeey4dqgxo",
):
    s = db.query(Snapshot).filter(Snapshot.url == url, Snapshot.pool == 0).first()
    if not s and config_for_url(url):
        s = Snapshot(
            url=url,
            pool=0,
            snapshot_state=SnapshotState.PENDING,
            provider=SnapshotProvider.GOOGLE,
        )
        db.add(s)
        db.commit()
        background_tasks.add_task(generate_snapshot, s.id)
    if s:
        return {"url": s.link}
    raise HTTPException(status.HTTP_404_NOT_FOUND)
