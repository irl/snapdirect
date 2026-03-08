from fastapi import APIRouter, HTTPException, BackgroundTasks
from starlette import status
from starlette.responses import HTMLResponse

from src.config import settings
from src.google.config import settings as google_settings
from src.snapshots.client import Snapshot
from src.snapshots.schemas import SnapshotContext
from src.snapshots.tasks import upload_snapshot

router = APIRouter()


@router.get(
    "/debug/context",
    summary="Generate the context used by the snapshot template for debugging purposes. Endpoint disabled on production deployments.",
    response_model=SnapshotContext,
)
def context(url: str = "https://www.bbc.com/russian/articles/ckgeey4dqgxo"):
    if settings.ENVIRONMENT.is_debug:
        return Snapshot(url).get_context()
    raise HTTPException(status.HTTP_404_NOT_FOUND)


@router.get(
    "/debug/demo",
    summary="Generate a rendered snapshot template for debugging purposes. Endpoint disabled on production deployments.",
    response_class=HTMLResponse,
)
def parse(url: str = "https://www.bbc.com/russian/articles/ckgeey4dqgxo"):
    if settings.ENVIRONMENT.is_debug:
        return Snapshot(url).render()
    raise HTTPException(status.HTTP_404_NOT_FOUND)


@router.get(
    "/debug/upload",
    summary="Generate a rendered snapshot template for debugging purposes and upload to Google Cloud Storage. Endpoint disabled on production deployments.",
    response_class=HTMLResponse,
)
def upload(
    background_tasks: BackgroundTasks,
    url: str = "https://www.bbc.com/russian/articles/ckgeey4dqgxo",
):
    if settings.ENVIRONMENT.is_debug:
        rendered = Snapshot(url).render()
        background_tasks.add_task(upload_snapshot, "debug2.html", rendered)
        return f'<a href="https://storage.googleapis.com/{google_settings.BUCKET_NAME}/debug.html">Google Cloud Storage</a>'
    raise HTTPException(status.HTTP_404_NOT_FOUND)
