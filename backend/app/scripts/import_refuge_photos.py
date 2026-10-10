"""Copie les photos des refuges depuis refuges.info (photos des commentaires, CC BY-SA 2.0).

Usage :
    .venv/bin/python -m app.scripts.import_refuge_photos              # refuges jamais vérifiés
    .venv/bin/python -m app.scripts.import_refuge_photos --massif 18  # Écrins seulement
    .venv/bin/python -m app.scripts.import_refuge_photos --again      # revérifie tout

À lancer après `app.scripts.import_refuges`. Relançable : une photo déjà copiée n'est pas
retéléchargée, et un refuge déjà vérifié est sauté (sauf avec --again). Une photo retirée
de refuges.info est retirée ici aussi lors d'une nouvelle vérification.

Chaque photo est réencodée en WebP comme les images envoyées (métadonnées retirées) et
servie par l'API : le navigateur ne charge jamais rien depuis refuges.info.
"""

import argparse
import time
import urllib.error

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.db import SessionLocal
from app.errors import ApiError
from app.models import Massif, Refuge, RefugePhoto, utcnow
from app.services import media, refuges_info

DEFAULT_PER_REFUGE = 3


def sync_refuge(
    db: Session, refuge: Refuge, photos: list[dict], per_refuge: int, delay: float = 0
) -> tuple[int, int]:
    """Met les photos du refuge à jour d'après `photos` (triées) : (ajoutées, retirées)."""
    wanted = photos[:per_refuge]
    wanted_ids = {photo["external_id"] for photo in wanted}
    existing = {photo.external_id: photo for photo in refuge.photos}

    removed = 0
    for external_id, photo in existing.items():
        if external_id not in wanted_ids:
            # L'image (et son fichier, effacé par clean_uploads) part avec la photo.
            db.delete(photo.upload)
            refuge.photos.remove(photo)
            removed += 1

    added = 0
    max_bytes = settings.upload_max_mb * 1024 * 1024
    for position, item in enumerate(wanted):
        photo = existing.get(item["external_id"])
        if photo is None:
            try:
                data = refuges_info.fetch_image(item["url"], max_bytes)
                upload = media.store_imported(db, data)
            except (OSError, ValueError, ApiError):
                continue  # image absente ou illisible : on réessaiera à la prochaine vérification
            photo = RefugePhoto(external_id=item["external_id"], upload=upload)
            refuge.photos.append(photo)
            added += 1
            time.sleep(delay)
        photo.author = item["author"]
        photo.caption = item["caption"]
        photo.taken_at = item["taken_at"]
        photo.position = position
    refuge.photos_checked_at = utcnow()
    return added, removed


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--massif", type=int, nargs="*", help="ids refuges.info des massifs")
    parser.add_argument("--again", action="store_true", help="revérifier les refuges déjà vus")
    parser.add_argument("--per-refuge", type=int, default=DEFAULT_PER_REFUGE, help="photos max")
    parser.add_argument("--delay", type=float, default=0.5, help="pause entre deux requêtes (s)")
    args = parser.parse_args()

    with SessionLocal() as db:
        query = select(Refuge).options(selectinload(Refuge.photos).selectinload(RefugePhoto.upload))
        if args.massif:
            query = query.join(Refuge.massif).where(Massif.external_id.in_(args.massif))
        if not args.again:
            query = query.where(Refuge.photos_checked_at.is_(None))
        refuges = db.scalars(query.order_by(Refuge.id)).all()
        print(f"{len(refuges)} refuge(s) à vérifier sur refuges.info")

        totals = [0, 0]
        for index, refuge in enumerate(refuges, start=1):
            try:
                photos = refuges_info.fetch_photos(refuge.external_id)
            except (urllib.error.URLError, OSError, ValueError) as error:
                print(f"[{index}/{len(refuges)}] {refuge.name} : erreur ({error}), sauté")
                time.sleep(args.delay)
                continue
            added, removed = sync_refuge(db, refuge, photos, args.per_refuge, args.delay)
            db.commit()
            totals[0] += added
            totals[1] += removed
            if added or removed:
                print(f"[{index}/{len(refuges)}] {refuge.name} : +{added} −{removed}")
            elif index % 100 == 0:
                print(f"[{index}/{len(refuges)}] …")
            time.sleep(args.delay)  # ne pas surcharger ce service bénévole

    print(f"Terminé : {totals[0]} photo(s) ajoutée(s), {totals[1]} retirée(s).")


if __name__ == "__main__":
    main()
