import os
from pathlib import Path

# Sans backend/.env (CI…), un mot de passe factice suffit à importer l'application.
# Jamais quand .env existe : une variable d'environnement passerait avant le vrai mot de passe.
if not (Path(__file__).resolve().parent.parent / ".env").exists():
    os.environ.setdefault("DB_PASSWORD", "test")

from collections.abc import Callable, Iterator  # noqa: E402

import pytest  # noqa: E402
from fastapi import APIRouter  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.exc import OperationalError  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

from app.config import settings  # noqa: E402
from app.db import get_db, make_url  # noqa: E402
from app.deps import ActiveUser, ModeratorUser  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402

if settings.db_name_test == settings.db_name:
    raise RuntimeError("DB_NAME_TEST doit être différent de DB_NAME : les tests vident la base.")

test_engine = create_engine(make_url(settings.db_name_test), pool_pre_ping=True)
TestSession = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)

# Routes réservées aux tests, pour vérifier les dépendances d'accès.
_test_router = APIRouter(prefix="/api/_test")


@_test_router.get("/active")
def _active_only(user: ActiveUser) -> dict[str, str]:
    return {"username": user.username}


@_test_router.get("/moderator")
def _moderator_only(user: ModeratorUser) -> dict[str, str]:
    return {"username": user.username}


app.include_router(_test_router)


@pytest.fixture(scope="session")
def database() -> Iterator[None]:
    try:
        with test_engine.connect():
            pass
    except OperationalError:
        name, user = settings.db_name_test, settings.db_user
        pytest.exit(
            f"Base de test « {name} » injoignable. Créez-la avec :\n"
            f'  sudo mysql -e "CREATE DATABASE {name} CHARACTER SET utf8mb4; '
            f"GRANT ALL PRIVILEGES ON {name}.* TO '{user}'@'localhost';\"",
            returncode=1,
        )
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)
    yield
    Base.metadata.drop_all(test_engine)


@pytest.fixture
def db(database: None) -> Iterator[Session]:
    """Session sur la base de test, vidée après chaque test."""
    with TestSession() as session:
        yield session
    with test_engine.begin() as connection:
        connection.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        for table in Base.metadata.sorted_tables:
            connection.execute(text(f"TRUNCATE TABLE {table.name}"))
        connection.execute(text("SET FOREIGN_KEY_CHECKS = 1"))


@pytest.fixture(autouse=True)
def media_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Images envoyées pendant le test : dans un dossier temporaire, jamais backend/uploads."""
    directory = tmp_path / "uploads"
    monkeypatch.setattr(settings, "media_dir", directory)
    return directory


@pytest.fixture
def outbox(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, str]]:
    """Emails de confirmation « envoyés » pendant le test."""
    sent: list[dict[str, str]] = []

    def fake_send(to: str, display_name: str, token: str) -> None:
        sent.append({"to": to, "token": token})

    monkeypatch.setattr("app.routers.auth.send_verification_email", fake_send)
    return sent


@pytest.fixture
def client(db: Session, outbox: list[dict[str, str]]) -> Iterator[TestClient]:
    def override_get_db() -> Iterator[Session]:
        with TestSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def active_client(client: TestClient, outbox: list[dict[str, str]]) -> TestClient:
    """Client connecté avec un compte confirmé."""
    client.post(
        "/api/auth/register",
        json={
            "username": "randonneur",
            "email": "randonneur@mail.fr",
            "password": "motdepasse8",
            "accept_terms": True,
        },
    )
    client.post("/api/auth/verify-email", json={"token": outbox[-1]["token"]})
    return client


@pytest.fixture
def make_client(
    client: TestClient, outbox: list[dict[str, str]]
) -> Iterator[Callable[[str], TestClient]]:
    """Crée un compte confirmé `username` et renvoie un client connecté avec (un par personne)."""
    clients: list[TestClient] = []

    def factory(username: str) -> TestClient:
        other = TestClient(app)
        other.__enter__()
        clients.append(other)
        other.post(
            "/api/auth/register",
            json={
                "username": username,
                "email": f"{username}@mail.fr",
                "password": "motdepasse8",
                "accept_terms": True,
            },
        )
        other.post("/api/auth/verify-email", json={"token": outbox[-1]["token"]})
        return other

    yield factory
    for other in clients:
        other.__exit__(None, None, None)
