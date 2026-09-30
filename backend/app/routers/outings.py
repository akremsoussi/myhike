from typing import Annotated, Literal

from fastapi import APIRouter, Query, status
from sqlalchemy import exists, select
from sqlalchemy.orm import selectinload

from app.db import DbSession
from app.deps import ActiveUser
from app.errors import ApiError
from app.models import (
    Outing,
    OutingInvitation,
    OutingParticipant,
    OutingStop,
    User,
    utcnow,
)
from app.routers.users import get_user
from app.schemas.outings import InvitationIn, OutingDetail, OutingIn, OutingSummary
from app.services import outings
from app.services.outings import is_participant_clause, outing_visible_to

router = APIRouter(prefix="/outings", tags=["outings"])

Scope = Literal["upcoming", "mine", "joined", "past"]

LIST_LIMIT = 100

# Chargement groupé de ce qu'affiche une carte de sortie.
LOAD = (
    selectinload(Outing.organizer),
    selectinload(Outing.stops).selectinload(OutingStop.refuge),
    selectinload(Outing.participants).selectinload(OutingParticipant.user),
)


def _load(db: DbSession, outing_id: int, viewer: User) -> Outing:
    """Sortie visible, rechargée avec tout ce qu'affiche l'écran 11."""
    outings.get_visible(db, viewer, outing_id)
    return db.scalars(
        select(Outing).where(Outing.id == outing_id).options(*LOAD).execution_options(
            populate_existing=True
        )
    ).one()


@router.get("")
def list_outings(
    db: DbSession,
    viewer: ActiveUser,
    scope: Scope = "upcoming",
    refuge_id: Annotated[int | None, Query(ge=1)] = None,
) -> list[OutingSummary]:
    """Onglets de l'écran 10 ; `refuge_id` : sorties prévues à un refuge (écran 04).

    upcoming : toutes les sorties à venir visibles · mine : celles que j'organise ·
    joined : celles où je participe sans les organiser · past : passées, où j'ai participé.
    """
    now = utcnow()
    query = select(Outing).where(outing_visible_to(viewer))
    if scope == "upcoming":
        query = query.where(Outing.starts_at >= now).order_by(Outing.starts_at)
    elif scope == "mine":
        query = query.where(Outing.organizer_id == viewer.id, Outing.starts_at >= now)
        query = query.order_by(Outing.starts_at)
    elif scope == "joined":
        query = query.where(
            is_participant_clause(viewer.id),
            Outing.organizer_id != viewer.id,
            Outing.starts_at >= now,
        ).order_by(Outing.starts_at)
    else:
        query = query.where(is_participant_clause(viewer.id), Outing.starts_at < now)
        query = query.order_by(Outing.starts_at.desc())
    if refuge_id is not None:
        query = query.where(
            exists().where(OutingStop.outing_id == Outing.id, OutingStop.refuge_id == refuge_id)
        )
    rows = db.scalars(query.options(*LOAD).limit(LIST_LIMIT)).all()
    return [outings.summary(outing, viewer) for outing in rows]


@router.get("/{outing_id}")
def get_outing(outing_id: int, db: DbSession, viewer: ActiveUser) -> OutingDetail:
    return outings.detail(db, _load(db, outing_id, viewer), viewer)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_outing(data: OutingIn, db: DbSession, viewer: ActiveUser) -> OutingDetail:
    """Écran 12. L'organisateur participe d'office."""
    if data.starts_at < utcnow():
        raise ApiError(422, "validation_error", "Certains champs sont invalides.",
                       fields={"starts_at": "La sortie doit être dans le futur."})
    outing = Outing(organizer_id=viewer.id)
    db.add(outing)
    outings.apply(db, outing, data)
    outing.participants.append(OutingParticipant(user_id=viewer.id))
    db.commit()
    return outings.detail(db, _load(db, outing.id, viewer), viewer)


@router.put("/{outing_id}")
def update_outing(
    outing_id: int, data: OutingIn, db: DbSession, viewer: ActiveUser
) -> OutingDetail:
    outing = _load(db, outing_id, viewer)
    if outing.organizer_id != viewer.id:
        raise ApiError(403, "forbidden", "Seul l'organisateur peut modifier cette sortie.")
    if outing.starts_at < utcnow():
        raise ApiError(409, "outing_past", "Cette sortie a déjà eu lieu.")
    if data.max_participants < len(outing.participants):
        raise ApiError(422, "validation_error", "Certains champs sont invalides.",
                       fields={"max_participants": "Moins de places que de participants."})
    outings.apply(db, outing, data)
    db.commit()
    return outings.detail(db, _load(db, outing.id, viewer), viewer)


@router.delete("/{outing_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_outing(outing_id: int, db: DbSession, viewer: ActiveUser) -> None:
    outing = outings.get_visible(db, viewer, outing_id)
    if not outings.can_manage(outing, viewer):
        raise ApiError(403, "forbidden", "Seul l'organisateur peut supprimer cette sortie.")
    db.delete(outing)
    db.commit()


@router.put("/{outing_id}/participation")
def join(outing_id: int, db: DbSession, viewer: ActiveUser) -> OutingDetail:
    """« Rejoindre la sortie »."""
    outing = _load(db, outing_id, viewer)
    result = outings.detail(db, outing, viewer)
    if not result.is_participant:
        problem = outings.can_join(outing, viewer, result.is_invited, False)
        if problem is not None:
            code, message = outings.JOIN_ERRORS[problem]
            raise ApiError(code, problem, message)
        db.add(OutingParticipant(outing_id=outing.id, user_id=viewer.id))
        db.commit()
    return outings.detail(db, _load(db, outing.id, viewer), viewer)


@router.delete("/{outing_id}/participation")
def leave(outing_id: int, db: DbSession, viewer: ActiveUser) -> OutingDetail:
    """« Quitter la sortie ». L'organisateur ne peut pas quitter sa propre sortie."""
    outing = _load(db, outing_id, viewer)
    if outing.organizer_id == viewer.id:
        raise ApiError(
            409, "organizer_cannot_leave", "L'organisateur ne peut pas quitter sa sortie."
        )
    participation = db.get(OutingParticipant, (outing.id, viewer.id))
    if participation is not None:
        db.delete(participation)
        db.commit()
    return outings.detail(db, _load(db, outing.id, viewer), viewer)


@router.post("/{outing_id}/invitations", status_code=status.HTTP_204_NO_CONTENT)
def invite(outing_id: int, data: InvitationIn, db: DbSession, viewer: ActiveUser) -> None:
    """« Inviter à une sortie » (écran 06). Réservé à l'organisateur."""
    outing = outings.get_visible(db, viewer, outing_id)
    if outing.organizer_id != viewer.id:
        raise ApiError(403, "forbidden", "Seul l'organisateur peut inviter.")
    if outing.starts_at < utcnow():
        raise ApiError(409, "outing_past", "Cette sortie a déjà eu lieu.")
    guest = get_user(db, data.username)
    if guest.id != viewer.id and db.get(OutingInvitation, (outing.id, guest.id)) is None:
        db.add(OutingInvitation(outing_id=outing.id, user_id=guest.id, invited_by_id=viewer.id))
        db.commit()
