import logging

from fastapi import APIRouter, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db import DbSession

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
def health(response: Response, db: DbSession) -> dict[str, str]:
    """Indique si l'API répond et si elle joint la base MySQL."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        # Le détail reste dans les logs du serveur, jamais dans la réponse.
        logger.exception("Connexion à MySQL impossible")
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"api": "ok", "database": "error"}
    return {"api": "ok", "database": "ok"}
