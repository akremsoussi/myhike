from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import Select, exists, func, or_, select
from sqlalchemy.orm import joinedload

from app.db import DbSession
from app.deps import ActiveUser
from app.errors import ApiError
from app.models import GUARDED_KINDS, Massif, Outing, OutingStop, Refuge, utcnow
from app.schemas.refuges import MassifOut, RefugeDetail, RefugeList, RefugeSummary
from app.services.outings import outing_visible_to

router = APIRouter(tags=["refuges"])

MAX_LIMIT = 2000


def _parse_bbox(bbox: str) -> tuple[float, float, float, float]:
    """« ouest,sud,est,nord » en degrés."""
    try:
        west, south, east, north = (float(part) for part in bbox.split(","))
    except ValueError:
        raise ApiError(422, "invalid_bbox", "bbox attendu : ouest,sud,est,nord.") from None
    if not (-180 <= west <= east <= 180 and -90 <= south <= north <= 90):
        raise ApiError(422, "invalid_bbox", "bbox hors limites.")
    return west, south, east, north


def _escape_like(text: str) -> str:
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@router.get("/refuges")
def list_refuges(
    db: DbSession,
    viewer: ActiveUser,
    bbox: Annotated[str | None, Query(description="ouest,sud,est,nord")] = None,
    guarded: Annotated[bool | None, Query(description="true : gardés, false : non gardés")] = None,
    q: Annotated[str | None, Query(min_length=2, max_length=100)] = None,
    with_outing: Annotated[
        bool, Query(description="seulement les refuges d'une sortie à venir visible")
    ] = False,
    limit: Annotated[int, Query(ge=1, le=MAX_LIMIT)] = 500,
) -> RefugeList:
    """Refuges de la zone visible (carte) ou correspondant à une recherche (liste)."""
    query: Select = select(Refuge).outerjoin(Refuge.massif)
    if bbox is not None:
        west, south, east, north = _parse_bbox(bbox)
        query = query.where(
            Refuge.longitude.between(west, east), Refuge.latitude.between(south, north)
        )
    if guarded is True:
        query = query.where(Refuge.kind.in_(GUARDED_KINDS))
    elif guarded is False:
        query = query.where(Refuge.kind.not_in(GUARDED_KINDS))
    if with_outing:
        query = query.where(
            exists()
            .where(
                OutingStop.refuge_id == Refuge.id,
                OutingStop.outing_id == Outing.id,
                Outing.starts_at >= utcnow(),
                outing_visible_to(viewer),
            )
        )
    if q:
        # Collation MySQL utf8mb4_0900_ai_ci : insensible à la casse et aux accents.
        pattern = f"%{_escape_like(q.strip())}%"
        query = query.where(or_(Refuge.name.like(pattern), Massif.name.like(pattern)))

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(
        query.options(joinedload(Refuge.massif)).order_by(Refuge.name, Refuge.id).limit(limit)
    ).all()
    return RefugeList(total=total, items=[RefugeSummary.model_validate(row) for row in rows])


@router.get("/refuges/{refuge_id}")
def get_refuge(refuge_id: int, db: DbSession, _: ActiveUser) -> RefugeDetail:
    refuge = db.get(Refuge, refuge_id, options=[joinedload(Refuge.massif)])
    if refuge is None:
        raise ApiError(404, "not_found", "Ce refuge n'existe pas.")
    return RefugeDetail.model_validate(refuge)


@router.get("/massifs")
def list_massifs(db: DbSession, _: ActiveUser) -> list[MassifOut]:
    return [MassifOut.model_validate(m) for m in db.scalars(select(Massif).order_by(Massif.name))]
