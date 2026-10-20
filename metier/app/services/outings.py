"""Sorties : qui les voit, qui peut les rejoindre, et leurs chiffres (distance, dénivelé)."""


from sqlalchemy import ColumnElement, exists, or_, select
from sqlalchemy.orm import Session

from app.errors import ApiError
from app.models import (
    Outing,
    OutingInvitation,
    OutingParticipant,
    OutingStop,
    OutingVisibility,
    Refuge,
    Role,
    User,
    utcnow,
)
from app.schemas.communities import AuthorOut
from app.schemas.outings import OutingDetail, OutingIn, OutingSummary, StopOut
from app.services import geo

PREVIEW_PARTICIPANTS = 3


def is_participant_clause(user_id: int) -> ColumnElement[bool]:
    return exists().where(
        OutingParticipant.outing_id == Outing.id, OutingParticipant.user_id == user_id
    )


def is_invited_clause(user_id: int) -> ColumnElement[bool]:
    return exists().where(
        OutingInvitation.outing_id == Outing.id, OutingInvitation.user_id == user_id
    )


def outing_visible_to(viewer: User) -> ColumnElement[bool]:
    """Publique : tout le monde. Sur invitation : organisateur, participants et invités."""
    return or_(
        Outing.visibility == OutingVisibility.PUBLIC,
        Outing.organizer_id == viewer.id,
        is_participant_clause(viewer.id),
        is_invited_clause(viewer.id),
    )


def get_visible(db: Session, viewer: User, outing_id: int) -> Outing:
    """Sortie lisible par `viewer` ; sinon 404, comme si elle n'existait pas."""
    outing = db.scalar(select(Outing).where(Outing.id == outing_id, outing_visible_to(viewer)))
    if outing is None:
        raise ApiError(404, "not_found", "Cette sortie n'existe pas.")
    return outing


def _stop_points(outing: Outing) -> list[list[float]]:
    return [[float(stop.latitude), float(stop.longitude)] for stop in outing.stops]


def distance_m(outing: Outing) -> int:
    """Longueur du chemin tracé, ou à défaut distance à vol d'oiseau entre les points de stop."""
    points = outing.path if len(outing.path) >= 2 else _stop_points(outing)
    return geo.length_m(points)


def elevation_gain_m(outing: Outing) -> int | None:
    """Somme des montées entre points de stop d'altitude connue ; None si moins de deux."""
    altitudes = [s.refuge.altitude for s in outing.stops if s.refuge and s.refuge.altitude]
    if len(altitudes) < 2:
        return None
    return sum(max(0, b - a) for a, b in zip(altitudes, altitudes[1:], strict=False))


def summary(outing: Outing, viewer: User) -> OutingSummary:
    participants = [p.user for p in outing.participants]
    return OutingSummary(
        id=outing.id,
        title=outing.title,
        starts_at=outing.starts_at,
        organizer=AuthorOut.model_validate(outing.organizer),
        visibility=outing.visibility,
        status="full" if len(participants) >= outing.max_participants else "open",
        participant_count=len(participants),
        max_participants=outing.max_participants,
        stop_count=len(outing.stops),
        participants_preview=[
            AuthorOut.model_validate(u) for u in participants[:PREVIEW_PARTICIPANTS]
        ],
        preview=outing.path if len(outing.path) >= 2 else _stop_points(outing),
        is_participant=any(u.id == viewer.id for u in participants),
    )


def detail(db: Session, outing: Outing, viewer: User) -> OutingDetail:
    base = summary(outing, viewer)
    is_invited = (
        db.get(OutingInvitation, (outing.id, viewer.id)) is not None
        or outing.organizer_id == viewer.id
    )
    return OutingDetail(
        **base.model_dump(),
        stops=[
            StopOut(
                position=stop.position,
                name=stop.name,
                latitude=float(stop.latitude),
                longitude=float(stop.longitude),
                refuge_id=stop.refuge_id,
                altitude=stop.refuge.altitude if stop.refuge else None,
            )
            for stop in outing.stops
        ],
        participants=[AuthorOut.model_validate(p.user) for p in outing.participants],
        path=outing.path,
        distance_m=distance_m(outing),
        elevation_gain_m=elevation_gain_m(outing),
        is_organizer=outing.organizer_id == viewer.id,
        is_invited=is_invited,
        can_join=can_join(outing, viewer, is_invited, base.is_participant) is None,
    )


def can_join(outing: Outing, viewer: User, is_invited: bool, is_participant: bool) -> str | None:
    """None si `viewer` peut rejoindre, sinon le code de l'empêchement."""
    if is_participant:
        return "already_participant"
    if outing.starts_at < utcnow():
        return "outing_past"
    if outing.visibility == OutingVisibility.INVITATION and not is_invited:
        return "invitation_required"
    if len(outing.participants) >= outing.max_participants:
        return "outing_full"
    return None


JOIN_ERRORS = {
    "outing_past": (409, "Cette sortie a déjà eu lieu."),
    "invitation_required": (403, "Cette sortie est sur invitation."),
    "outing_full": (409, "Cette sortie est complète."),
}


def apply(db: Session, outing: Outing, data: OutingIn) -> None:
    """Recopie le formulaire de l'écran 12 dans `outing` (points de stop remplacés)."""
    refuge_ids = {stop.refuge_id for stop in data.stops if stop.refuge_id is not None}
    refuges = {
        refuge.id: refuge
        for refuge in db.scalars(select(Refuge).where(Refuge.id.in_(refuge_ids)))
    }
    if len(refuges) != len(refuge_ids):
        raise ApiError(422, "unknown_refuge", "Un des refuges choisis n'existe pas.")

    outing.title = data.title
    outing.starts_at = data.starts_at
    outing.max_participants = data.max_participants
    outing.visibility = data.visibility
    outing.path = [list(point) for point in data.path]
    outing.stops.clear()
    db.flush()  # supprime les anciens points avant d'insérer les nouveaux
    for position, stop in enumerate(data.stops, start=1):
        refuge = refuges.get(stop.refuge_id) if stop.refuge_id is not None else None
        outing.stops.append(
            OutingStop(
                position=position,
                refuge_id=refuge.id if refuge else None,
                name=refuge.name if refuge else (stop.name or "Point libre"),
                latitude=refuge.latitude if refuge else stop.latitude,
                longitude=refuge.longitude if refuge else stop.longitude,
            )
        )


def can_manage(outing: Outing, viewer: User) -> bool:
    return outing.organizer_id == viewer.id or viewer.role in (Role.MODERATOR, Role.SUPER_ADMIN)
