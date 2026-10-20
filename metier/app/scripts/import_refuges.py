"""Importe (ou met à jour) les massifs et refuges depuis refuges.info.

Usage :
    .venv/bin/python -m app.scripts.import_refuges              # tous les massifs de la zone
    .venv/bin/python -m app.scripts.import_refuges --massif 18  # Écrins seulement

Relançable sans risque : les refuges sont retrouvés par leur identifiant refuges.info.
"""

import argparse
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Massif, Refuge, utcnow
from app.services import refuges_info


def upsert_massif(db: Session, external_id: int, name: str) -> Massif:
    massif = db.scalar(select(Massif).where(Massif.external_id == external_id))
    if massif is None:
        massif = Massif(external_id=external_id, name=name)
        db.add(massif)
    else:
        massif.name = name
    db.flush()
    return massif


def upsert_refuges(db: Session, massif: Massif, features: list[dict]) -> tuple[int, int, int]:
    """Renvoie (créés, mis à jour, ignorés)."""
    created = updated = skipped = 0
    now = utcnow()
    for feature in features:
        fields = refuges_info.parse_point(feature)
        if fields is None:
            skipped += 1
            continue
        refuge = db.scalar(select(Refuge).where(Refuge.external_id == fields["external_id"]))
        if refuge is None:
            refuge = Refuge(**fields)
            db.add(refuge)
            created += 1
        else:
            for key, value in fields.items():
                setattr(refuge, key, value)
            updated += 1
        refuge.massif_id = massif.id
        refuge.imported_at = now
    return created, updated, skipped


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--massif", type=int, nargs="*", help="ids refuges.info des massifs")
    parser.add_argument("--bbox", default=refuges_info.DEFAULT_BBOX, help="ouest,sud,est,nord")
    parser.add_argument("--delay", type=float, default=1.0, help="pause entre deux requêtes (s)")
    args = parser.parse_args()

    massifs = refuges_info.fetch_massifs(args.bbox)
    if args.massif:
        massifs = [m for m in massifs if m["external_id"] in set(args.massif)]
    print(f"{len(massifs)} massif(s) à importer depuis refuges.info")

    totals = [0, 0, 0]
    with SessionLocal() as db:
        for index, item in enumerate(sorted(massifs, key=lambda m: m["name"]), start=1):
            massif = upsert_massif(db, item["external_id"], item["name"])
            features = refuges_info.fetch_massif_points(item["external_id"])
            counts = upsert_refuges(db, massif, features)
            db.commit()
            totals = [total + count for total, count in zip(totals, counts, strict=True)]
            progress = f"[{index}/{len(massifs)}] {item['name']}"
            print(f"{progress} : {counts[0]} créés, {counts[1]} mis à jour")
            time.sleep(args.delay)  # ne pas surcharger ce service bénévole

    print(f"Terminé : {totals[0]} créés, {totals[1]} mis à jour, {totals[2]} ignorés (détruits).")


if __name__ == "__main__":
    main()
