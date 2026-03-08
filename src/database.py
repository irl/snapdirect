import contextlib
from typing import Annotated, Iterator, Generator

from fastapi import Depends
from sqlalchemy import (
    MetaData, create_engine, Connection,
)
from sqlalchemy.orm import sessionmaker, Session

from src.config import settings
from src.constants import DB_NAMING_CONVENTION

engine = create_engine(
    str(settings.DATABASE_URL),
    pool_size=settings.DATABASE_POOL_SIZE,
    pool_recycle=settings.DATABASE_POOL_TTL,
    pool_pre_ping=settings.DATABASE_POOL_PRE_PING,
)
metadata = MetaData(naming_convention=DB_NAMING_CONVENTION)
sm = sessionmaker(autocommit=False, expire_on_commit=False, bind=engine)


@contextlib.contextmanager
def get_db_connection() -> Iterator[Connection]:
    with engine.connect() as connection:
        try:
            yield connection
        except Exception:
            connection.rollback()
            raise


@contextlib.contextmanager
def get_db_session() -> Iterator[Session]:
    session = sm()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None]:
    with get_db_session() as session:
        yield session


DbSession = Annotated[Session, Depends(get_db)]
