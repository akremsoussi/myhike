from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings


def make_url(database: str) -> URL:
    # URL.create échappe les caractères spéciaux du mot de passe.
    return URL.create(
        "mysql+pymysql",
        username=settings.db_user,
        password=settings.db_password,
        host=settings.db_host,
        port=settings.db_port,
        database=database,
        query={"charset": "utf8mb4"},
    )


database_url = make_url(settings.db_name)

engine = create_engine(
    database_url,
    pool_pre_ping=True,  # reconnecte si MySQL a fermé une connexion inactive
    pool_recycle=3600,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session


DbSession = Annotated[Session, Depends(get_db)]
