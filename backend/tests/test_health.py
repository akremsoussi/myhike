from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.db import get_db
from app.main import app

client = TestClient(app)


class UnreachableDatabase:
    def execute(self, *args, **kwargs):
        raise OperationalError("SELECT 1", {}, Exception("connexion refusée"))


def test_health_reports_database_error():
    app.dependency_overrides[get_db] = lambda: UnreachableDatabase()
    try:
        response = client.get("/api/health")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"api": "ok", "database": "error"}
