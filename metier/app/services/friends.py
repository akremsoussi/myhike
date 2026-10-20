"""Amitiés : une demande `pending` devient `accepted` (amis dans les deux sens) ou `declined`.

Il y a au plus une ligne par sens entre deux personnes (contrainte unique). Toutes les
règles passent par ce module : les routes ne manipulent jamais `Friendship` directement.
"""

import enum

from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.orm import Session

from app.errors import ApiError
from app.models import (
    AccountStatus,
    Audience,
    CommunityMember,
    Friendship,
    FriendshipStatus,
    RequestPolicy,
    User,
    utcnow,
)
from app.services.visibility import friend_ids


class Relation(enum.StrEnum):
    """Relation vue par `viewer` (bouton de l'écran 06)."""

    SELF = "self"
    NONE = "none"
    FRIENDS = "friends"
    REQUEST_SENT = "request_sent"
    REQUEST_RECEIVED = "request_received"


def _between(a: int, b: int):
    return or_(
        and_(Friendship.requester_id == a, Friendship.addressee_id == b),
        and_(Friendship.requester_id == b, Friendship.addressee_id == a),
    )


def rows_between(db: Session, a: User, b: User) -> list[Friendship]:
    return list(db.scalars(select(Friendship).where(_between(a.id, b.id))))


def relation(db: Session, viewer: User, other: User) -> tuple[Relation, Friendship | None]:
    """Relation et ligne concernée (pour la date d'amitié)."""
    if viewer.id == other.id:
        return Relation.SELF, None
    rows = rows_between(db, viewer, other)
    for row in rows:
        if row.status == FriendshipStatus.ACCEPTED:
            return Relation.FRIENDS, row
    for row in rows:
        sent = row.requester_id == viewer.id
        # Une demande refusée reste « envoyée » pour son auteur : il n'est pas prévenu du refus
        # et ne peut pas la renvoyer aussitôt.
        if sent:
            return Relation.REQUEST_SENT, row
        if row.status == FriendshipStatus.PENDING:
            return Relation.REQUEST_RECEIVED, row
    return Relation.NONE, None


def are_friends(db: Session, a: User, b: User) -> bool:
    return relation(db, a, b)[0] == Relation.FRIENDS


def common_community_ids(db: Session, a: User, b: User) -> list[int]:
    theirs = select(CommunityMember.community_id).where(CommunityMember.user_id == b.id)
    return list(
        db.scalars(
            select(CommunityMember.community_id).where(
                CommunityMember.user_id == a.id, CommunityMember.community_id.in_(theirs)
            )
        )
    )


def friend_count(db: Session, user: User) -> int:
    return db.scalar(select(func.count()).select_from(friend_ids(user.id).subquery())) or 0


def can_see_friends(db: Session, viewer: User, owner: User) -> bool:
    """Réglage « Qui peut voir ma liste d'amis » (écran 05c)."""
    if viewer.id == owner.id or owner.friends_list_audience == Audience.EVERYONE:
        return True
    if owner.friends_list_audience == Audience.FRIENDS:
        return are_friends(db, viewer, owner)
    return False


def can_see_outings(db: Session, viewer: User, owner: User) -> bool:
    """Réglage « Qui peut voir mes sorties à venir » (écran 05c), sur le profil seulement."""
    if viewer.id == owner.id or owner.outings_audience == Audience.EVERYONE:
        return True
    if owner.outings_audience == Audience.FRIENDS:
        return are_friends(db, viewer, owner)
    return False


def can_send_request(db: Session, sender: User, target: User) -> bool:
    """Réglage « Qui peut m'envoyer une demande d'ami » (écran 05c)."""
    if target.friend_requests_from == RequestPolicy.EVERYONE:
        return True
    return bool(common_community_ids(db, sender, target))


def send_request(db: Session, sender: User, target: User) -> Relation:
    """« + Ajouter en ami ». Si `target` nous avait déjà demandé, la demande est acceptée."""
    if sender.id == target.id:
        raise ApiError(422, "invalid_friend", "Vous ne pouvez pas vous ajouter vous-même.")
    if target.status != AccountStatus.ACTIVE:
        raise ApiError(404, "not_found", "Cet utilisateur n'existe pas.")
    current, row = relation(db, sender, target)
    if current in (Relation.FRIENDS, Relation.REQUEST_SENT):
        return current
    if current == Relation.REQUEST_RECEIVED:
        assert row is not None
        return _accept(db, row)
    if not can_send_request(db, sender, target):
        raise ApiError(
            403,
            "requests_restricted",
            f"{target.display_name} n'accepte que les demandes des membres de ses communautés.",
        )
    # Une ancienne demande refusée (dans un sens ou dans l'autre) est remplacée.
    db.execute(delete(Friendship).where(_between(sender.id, target.id)))
    db.add(Friendship(requester_id=sender.id, addressee_id=target.id))
    db.commit()
    return Relation.REQUEST_SENT


def _received(db: Session, viewer: User, requester: User) -> Friendship:
    row = db.scalar(
        select(Friendship).where(
            Friendship.requester_id == requester.id,
            Friendship.addressee_id == viewer.id,
            Friendship.status == FriendshipStatus.PENDING,
        )
    )
    if row is None:
        raise ApiError(404, "no_request", "Aucune demande en attente de cette personne.")
    return row


def _accept(db: Session, row: Friendship) -> Relation:
    row.status = FriendshipStatus.ACCEPTED
    row.responded_at = utcnow()
    db.commit()
    return Relation.FRIENDS


def accept(db: Session, viewer: User, requester: User) -> Relation:
    return _accept(db, _received(db, viewer, requester))


def decline(db: Session, viewer: User, requester: User) -> Relation:
    """« Refuser » : le demandeur n'est pas prévenu, il voit toujours sa demande en attente."""
    row = _received(db, viewer, requester)
    row.status = FriendshipStatus.DECLINED
    row.responded_at = utcnow()
    db.commit()
    return Relation.NONE


def cancel(db: Session, viewer: User, target: User) -> Relation:
    """« Annuler » une demande envoyée (y compris refusée sans qu'on le sache)."""
    db.execute(
        delete(Friendship).where(
            Friendship.requester_id == viewer.id,
            Friendship.addressee_id == target.id,
            Friendship.status != FriendshipStatus.ACCEPTED,
        )
    )
    db.commit()
    return relation(db, viewer, target)[0]


def remove(db: Session, viewer: User, friend: User) -> Relation:
    """Retirer un ami : possible par l'un ou l'autre."""
    db.execute(
        delete(Friendship).where(
            _between(viewer.id, friend.id), Friendship.status == FriendshipStatus.ACCEPTED
        )
    )
    db.commit()
    return relation(db, viewer, friend)[0]
