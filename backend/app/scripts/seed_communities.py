"""Crée les communautés de départ, en attendant l'écran de modération 15.

Usage (après import_refuges) :
    .venv/bin/python -m app.scripts.seed_communities

Relançable sans risque : une communauté existante (même slug) n'est pas modifiée, sauf
si elle n'a pas encore de massif (refuges importés après un premier lancement).
Chaque communauté est rattachée au massif dont le nom contient `massif`, et à ses
refuges gardés les plus grands.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import GUARDED_KINDS, Community, Massif, Refuge

REFUGES_PER_COMMUNITY = 3

COMMUNITIES = [
    {
        "slug": "ecrins",
        "name": "Randonneurs des Écrins",
        "region": "Alpes",
        "massif": "Écrins",
        "description": "Sorties, conditions et bons plans autour des refuges des Écrins.",
    },
    {
        "slug": "mont-blanc",
        "name": "Mont-Blanc & Aiguilles Rouges",
        "region": "Alpes",
        "massif": "Mont Blanc",
        "description": "Préparer ses tours et ses nuits en refuge dans le massif du Mont-Blanc.",
    },
    {
        "slug": "vanoise",
        "name": "Vanoise",
        "region": "Alpes",
        "massif": "Vanoise",
        "description": "Le parc national de la Vanoise, ses refuges et ses bouquetins.",
    },
    {
        "slug": "vercors",
        "name": "Vercors",
        "region": "Préalpes",
        "massif": "Vercors",
        "description": "Hauts-plateaux, cabanes non gardées et itinéraires hors des foules.",
    },
    {
        "slug": "chartreuse",
        "name": "Chartreuse",
        "region": "Préalpes",
        "massif": "Chartreuse",
        "description": "Randonnées et bivouacs en Chartreuse.",
    },
    {
        "slug": "pyrenees-centrales",
        "name": "Pyrénées centrales",
        "region": "Pyrénées",
        "massif": "Bigorre",
        "description": "Du Néouvielle au Vignemale : refuges, lacs et cols.",
    },
]


def find_massif(db: Session, name: str) -> Massif | None:
    # Collation MySQL insensible à la casse et aux accents.
    return db.scalars(
        select(Massif).where(Massif.name.like(f"%{name}%")).order_by(Massif.name)
    ).first()


def biggest_refuges(db: Session, massif: Massif) -> list[Refuge]:
    return list(
        db.scalars(
            select(Refuge)
            .where(Refuge.massif_id == massif.id, Refuge.kind.in_(GUARDED_KINDS))
            .order_by(Refuge.capacity.desc(), Refuge.name)
            .limit(REFUGES_PER_COMMUNITY)
        )
    )


def main() -> None:
    created = completed = 0
    with SessionLocal() as db:
        for item in COMMUNITIES:
            community = db.scalar(select(Community).where(Community.slug == item["slug"]))
            if community is not None and community.massif_id is not None:
                continue
            massif = find_massif(db, item["massif"])
            if massif is None:
                print(f"Massif « {item['massif']} » introuvable : lancer import_refuges d'abord ?")
            if community is None:
                community = Community(
                    slug=item["slug"],
                    name=item["name"],
                    region=item["region"],
                    description=item["description"],
                )
                db.add(community)
                created += 1
            elif massif is not None:
                completed += 1
            if massif is not None:
                community.massif = massif
                community.refuges = biggest_refuges(db, massif)
        db.commit()
    print(f"{created} communauté(s) créée(s), {completed} complétée(s).")


if __name__ == "__main__":
    main()
