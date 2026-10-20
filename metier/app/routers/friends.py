from fastapi import APIRouter
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import DbSession
from app.deps import ActiveUser
from app.models import (
    AccountStatus,
    Community,
    CommunityMember,
    Friendship,
    FriendshipStatus,
    User,
)
from app.routers.users import get_user
from app.schemas.communities import AuthorOut, CommunityRef
from app.schemas.users import (
    FriendOut,
    FriendRequestOut,
    FriendsOut,
    RelationOut,
    SuggestionOut,
)
from app.services import friends
from app.services.visibility import friend_ids

router = APIRouter(prefix="/friends", tags=["friends"])

SUGGESTIONS = 5
SUGGESTION_CANDIDATES = 200


def _common_count(db: Session, viewer: User, other_id: int) -> int:
    mine = select(CommunityMember.community_id).where(CommunityMember.user_id == viewer.id)
    return (
        db.scalar(
            select(func.count()).where(
                CommunityMember.user_id == other_id, CommunityMember.community_id.in_(mine)
            )
        )
        or 0
    )


@router.get("")
def list_friends(db: DbSession, viewer: ActiveUser) -> FriendsOut:
    """Écran 05b : amis, demandes reçues (en attente) et envoyées (dont refusées en silence)."""
    rows = db.scalars(
        select(Friendship)
        .where((Friendship.requester_id == viewer.id) | (Friendship.addressee_id == viewer.id))
        .order_by(Friendship.created_at.desc(), Friendship.id.desc())
    ).all()
    users = {
        user.id: user
        for user in db.scalars(
            select(User).where(
                User.id.in_({r.requester_id for r in rows} | {r.addressee_id for r in rows}),
                User.status == AccountStatus.ACTIVE,
            )
        )
    }
    result = FriendsOut(friends=[], received=[], sent=[])
    for row in rows:
        mine = row.requester_id == viewer.id
        other = users.get(row.addressee_id if mine else row.requester_id)
        if other is None:  # compte suspendu ou supprimé
            continue
        author = AuthorOut.model_validate(other)
        if row.status == FriendshipStatus.ACCEPTED:
            result.friends.append(FriendOut(user=author, since=row.responded_at))
            continue
        request = FriendRequestOut(
            user=author,
            created_at=row.created_at,
            common_community_count=_common_count(db, viewer, other.id),
        )
        if mine:
            result.sent.append(request)
        elif row.status == FriendshipStatus.PENDING:
            result.received.append(request)
    result.friends.sort(key=lambda friend: friend.user.display_name.lower())
    return result


@router.get("/suggestions")
def suggestions(db: DbSession, viewer: ActiveUser) -> list[SuggestionOut]:
    """Membres de mes communautés, sans lien avec moi, classés par amis en commun."""
    my_communities = select(CommunityMember.community_id).where(
        CommunityMember.user_id == viewer.id
    )
    linked = select(Friendship.addressee_id).where(Friendship.requester_id == viewer.id).union(
        select(Friendship.requester_id).where(Friendship.addressee_id == viewer.id)
    )
    candidates = db.execute(
        select(User, func.min(CommunityMember.community_id))
        .join(CommunityMember, CommunityMember.user_id == User.id)
        .where(
            CommunityMember.community_id.in_(my_communities),
            User.id != viewer.id,
            User.id.not_in(linked),
            User.status == AccountStatus.ACTIVE,
            User.show_in_suggestions.is_(True),
        )
        .group_by(User.id)
        .limit(SUGGESTION_CANDIDATES)
    ).all()
    if not candidates:
        return []

    my_friends = set(db.scalars(friend_ids(viewer.id)))
    communities = {
        c.id: c
        for c in db.scalars(select(Community).where(Community.id.in_({c for _, c in candidates})))
    }
    scored = [
        SuggestionOut(
            user=AuthorOut.model_validate(user),
            community=CommunityRef.model_validate(communities[community_id]),
            mutual_friend_count=len(my_friends & set(db.scalars(friend_ids(user.id)))),
        )
        for user, community_id in candidates
    ]
    scored.sort(key=lambda s: (-s.mutual_friend_count, s.user.display_name.lower()))
    return scored[:SUGGESTIONS]


@router.post("/{username}")
def send_request(username: str, db: DbSession, viewer: ActiveUser) -> RelationOut:
    """« + Ajouter en ami »."""
    return RelationOut(relation=friends.send_request(db, viewer, get_user(db, username)))


@router.post("/{username}/accept")
def accept(username: str, db: DbSession, viewer: ActiveUser) -> RelationOut:
    return RelationOut(relation=friends.accept(db, viewer, get_user(db, username)))


@router.post("/{username}/decline")
def decline(username: str, db: DbSession, viewer: ActiveUser) -> RelationOut:
    return RelationOut(relation=friends.decline(db, viewer, get_user(db, username)))


@router.delete("/{username}/request")
def cancel(username: str, db: DbSession, viewer: ActiveUser) -> RelationOut:
    """« Annuler » une demande envoyée."""
    return RelationOut(relation=friends.cancel(db, viewer, get_user(db, username)))


@router.delete("/{username}")
def remove(username: str, db: DbSession, viewer: ActiveUser) -> RelationOut:
    """Retirer un ami."""
    return RelationOut(relation=friends.remove(db, viewer, get_user(db, username)))
