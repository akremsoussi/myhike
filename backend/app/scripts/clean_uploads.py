"""Supprime les images inutiles : envoyées mais jamais publiées, ou dont le contenu a disparu.

Usage (de temps en temps, par exemple une fois par jour) :
    .venv/bin/python -m app.scripts.clean_uploads

- Une image rattachée à rien (formulaire abandonné, post ou communauté supprimés) est
  effacée au bout de 24 h : le temps de finir un formulaire.
- Un fichier du dossier `MEDIA_DIR` sans ligne en base est effacé, lui aussi après 24 h.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal
from app.models import Upload, utcnow
from app.services.media import unattached

GRACE_PERIOD = timedelta(hours=24)


def clean(db: Session, now: datetime | None = None) -> tuple[int, int]:
    """(lignes supprimées, fichiers supprimés)."""
    now = now or utcnow()
    rows = db.execute(
        delete(Upload)
        .where(unattached(), Upload.created_at < now - GRACE_PERIOD)
        .execution_options(synchronize_session=False)
    ).rowcount
    db.commit()

    keys = set(db.scalars(select(Upload.key)))
    # `now` est en UTC sans fuseau (comme en base) : on le précise avant de comparer.
    cutoff = (now - GRACE_PERIOD).replace(tzinfo=UTC).timestamp()
    files = 0
    if settings.media_dir.is_dir():
        for path in settings.media_dir.glob("*/*"):
            # Un fichier récent est peut-être en cours d'envoi (ligne pas encore en base).
            if path.stem not in keys and path.stat().st_mtime < cutoff:
                path.unlink()
                files += 1
    return rows, files


def main() -> None:
    with SessionLocal() as db:
        rows, files = clean(db)
    print(f"{rows} image(s) non rattachée(s) supprimée(s), {files} fichier(s) effacé(s).")


if __name__ == "__main__":
    main()
