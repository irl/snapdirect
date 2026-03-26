from typing import Annotated

from fastapi import Depends, Header, HTTPException
from starlette import status

from src.config import settings


def api_key(host: str = Header(), authorization: str | None = Header(None)) -> bool:
    if host.lower().strip() != settings.API_DOMAIN.strip():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    try:
        if authorization.split()[1] == settings.API_KEY:
            return True
        return False
    except AttributeError, TypeError, IndexError:
        return False


ApiKey = Annotated[bool, Depends(api_key)]
