"""Images envoyées : traitement, stockage sur le disque et droit de lecture.

Chaque image est décodée puis réencodée en WebP : le fichier servi ne contient jamais
les métadonnées de l'original (EXIF, dont la position GPS de la photo), ni autre chose
qu'une image.
"""

import io
import os
import secrets
import warnings
from collections.abc import Collection
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import exists, func, or_, select
from sqlalchemy.orm import Session

from app.config import settings
from app.errors import ApiError
from app.models import Community, Post, RefugePhoto, Report, Role, Upload, User
from app.schemas.media import UploadKind
from app.services.visibility import post_visible_to

ACCEPTED_FORMATS = {"JPEG", "PNG", "WEBP"}
# Côté le plus long après redimensionnement ; l'icône est recadrée en carré.
MAX_SIDE: dict[UploadKind, int] = {"photo": 2048, "banner": 2048, "icon": 512}
# Au-delà, l'image est refusée avant d'être décodée (bombe de décompression).
MAX_PIXELS = 50_000_000
WEBP_QUALITY = 82
# Images envoyées mais pas encore rattachées : de quoi remplir quelques formulaires.
MAX_PENDING_UPLOADS = 30

Image.MAX_IMAGE_PIXELS = MAX_PIXELS


def path_for(key: str) -> Path:
    # Sous-dossiers par préfixe : pas des milliers de fichiers dans un même dossier.
    return settings.media_dir / key[:2] / f"{key}.webp"


def _invalid_image() -> ApiError:
    return ApiError(422, "invalid_image", "Ce fichier n'est pas une image JPEG, PNG ou WebP.")


def process(data: bytes, kind: UploadKind) -> tuple[bytes, int, int]:
    """Image réencodée en WebP, redressée et redimensionnée : (contenu, largeur, hauteur)."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            image = Image.open(io.BytesIO(data))
            if image.format not in ACCEPTED_FORMATS:
                raise _invalid_image()
            image.load()
    except (UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise _invalid_image() from None
    except OSError:  # fichier tronqué ou corrompu
        raise _invalid_image() from None

    # Photo prise téléphone tourné : on applique l'orientation EXIF avant de la retirer.
    image = ImageOps.exif_transpose(image)
    has_alpha = image.mode in ("RGBA", "LA") or "transparency" in image.info
    image = image.convert("RGBA" if has_alpha else "RGB")
    side = MAX_SIDE[kind]
    if kind == "icon":
        image = ImageOps.fit(image, (min(side, *image.size),) * 2)
    else:
        image.thumbnail((side, side))

    output = io.BytesIO()
    image.save(output, "WEBP", quality=WEBP_QUALITY)
    return output.getvalue(), image.width, image.height


def store(db: Session, owner: User, data: bytes, kind: UploadKind) -> Upload:
    pending = db.scalar(select(func.count()).where(Upload.owner_id == owner.id, unattached()))
    if (pending or 0) >= MAX_PENDING_UPLOADS:
        raise ApiError(
            429, "too_many_uploads", "Trop d'images en attente : publiez ou réessayez plus tard."
        )
    upload = _save(data, kind)
    upload.owner_id = owner.id
    db.add(upload)
    db.commit()
    return upload


def store_imported(db: Session, data: bytes) -> Upload:
    """Photo copiée depuis refuges.info : sans propriétaire, à rattacher à une `RefugePhoto`."""
    upload = _save(data, "photo")
    db.add(upload)
    return upload


def _save(data: bytes, kind: UploadKind) -> Upload:
    content, width, height = process(data, kind)
    key = secrets.token_hex(16)
    path = path_for(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Écriture dans un fichier temporaire puis renommage : jamais de fichier à moitié écrit.
    temporary = path.with_suffix(".tmp")
    temporary.write_bytes(content)
    os.replace(temporary, path)
    return Upload(key=key, width=width, height=height)


def _used_by_community():
    return exists().where(or_(Community.banner_id == Upload.id, Community.icon_id == Upload.id))


def _used_by_refuge():
    return exists().where(RefugePhoto.upload_id == Upload.id)


def unattached():
    """Image rattachée à rien : ni à un post, ni à une communauté, ni à un refuge."""
    return Upload.post_id.is_(None) & ~_used_by_community() & ~_used_by_refuge()


def claim(db: Session, owner: User, ids: Collection[int], field: str) -> list[Upload]:
    """Images de `owner` encore libres, dans l'ordre de `ids` ; 422 sinon."""
    if not ids:
        return []
    uploads = {
        upload.id: upload
        for upload in db.scalars(
            select(Upload).where(Upload.id.in_(ids), Upload.owner_id == owner.id, unattached())
        )
    }
    if len(uploads) != len(set(ids)):
        raise ApiError(
            422,
            "validation_error",
            "Certains champs sont invalides.",
            fields={field: "Cette image n'est plus disponible : ajoutez-la à nouveau."},
        )
    return [uploads[upload_id] for upload_id in ids]


def can_view(db: Session, viewer: User, upload: Upload) -> bool:
    """Même règle que pour le contenu auquel l'image est rattachée."""
    if upload.owner_id == viewer.id:
        return True
    if upload.post_id is not None:
        visible = db.scalar(
            select(exists().where(Post.id == upload.post_id, post_visible_to(viewer)))
        )
        if visible:
            return True
        # Un modérateur voit les photos d'un post signalé, comme son texte (page Signalements).
        return viewer.role in (Role.MODERATOR, Role.SUPER_ADMIN) and bool(
            db.scalar(
                select(
                    exists().where(Report.post_id == upload.post_id, Report.resolved_at.is_(None))
                )
            )
        )
    # Bannière ou icône d'une communauté, photo d'un refuge : visibles par tous les membres.
    public = or_(_used_by_community(), _used_by_refuge())
    return bool(db.scalar(select(exists().where(Upload.id == upload.id, public))))
