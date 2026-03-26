from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Header, HTTPException
from starlette import status
from starlette.responses import RedirectResponse

from src.config import app_configs, settings
from src.link.router import router as link_router
from src.mirrors.tasks import update_rsf_mirrors
from src.mirrors.router import router as mirrors_router
from src.snapshots.router import router as snapshots_router


@asynccontextmanager
async def lifespan(_application: FastAPI) -> AsyncGenerator:
    await update_rsf_mirrors()
    # Startup
    yield
    # Shutdown


app = FastAPI(**app_configs, lifespan=lifespan)

app.include_router(link_router)
app.include_router(snapshots_router)
app.include_router(mirrors_router)


@app.get("/")
def home(host: str = Header(settings.LINK_DOMAIN)):
    if host.lower().strip() != settings.API_DOMAIN:
        return RedirectResponse(
            settings.INVALID_URL,
            status_code=status.HTTP_302_FOUND,
            headers={"Referrer-Policy": "no-referrer"},
        )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@app.get("/api/v1/healthcheck", include_in_schema=False)
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}
