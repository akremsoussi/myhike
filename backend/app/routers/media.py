from typing import Annotated

from fastapi import APIRouter, File, Form, Path, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select

from app.config import settings
from app.db import DbSession
from app.deps import ActiveUser
from app.errors import ApiError
from app.models import Upload
from app.schemas.media import UploadKind, UploadOut
from app.services import media

router = APIRouter(tags=["media"])


@router.post("/uploads", status_code=status.HTTP_201_CREATED)
def upload_image(
    file: Annotated[UploadFile, File()],
    db: DbSession,
    viewer: ActiveUser,
    kind: Annotated[UploadKind, Form()] = "photo",
) -> UploadOut:
    """Envoie une image (multipart), à rattacher ensuite à un post ou à une communauté.

    Fonction synchrone : le traitement de l'image tourne hors de la boucle d'événements.
    """
    max_bytes = settings.upload_max_mb * 1024 * 1024
    data = file.file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ApiError(
            413, "file_too_large", f"Image trop lourde ({settings.upload_max_mb} Mo max.)."
        )
    upload = media.store(db, viewer, data, kind)
    return UploadOut.model_validate(upload)


@router.get("/media/{key}.webp", response_class=FileResponse)
def get_image(
    key: Annotated[str, Path(pattern="^[0-9a-f]{32}$")], db: DbSession, viewer: ActiveUser
) -> FileResponse:
    """Sert une image à qui a le droit de voir ce qui la contient ; 404 sinon."""
    upload = db.scalar(select(Upload).where(Upload.key == key))
    path = media.path_for(key)
    if upload is None or not media.can_view(db, viewer, upload) or not path.is_file():
        raise ApiError(404, "not_found", "Cette image n'existe pas.")
    return FileResponse(
        path,
        media_type="image/webp",
        # Privé : le navigateur peut la garder, pas un cache partagé. Une heure seulement,
        # pour qu'une amitié retirée ne laisse pas les photos « Amis » visibles longtemps.
        headers={"Cache-Control": "private, max-age=3600"},
    )
