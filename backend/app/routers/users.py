from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db import DbSession
from app.deps import ActiveUser
from app.errors import ApiError
from app.models import (
    AccountStatus,
    Community,
    CommunityMember,
    Friendship,
    FriendshipStatus,
    Outing,
    OutingParticipant,
    OutingStop,
    Post,
    User,
    utcnow,
)
from app.schemas.communities import AuthorOut, CommunityRef, PostPage
from app.schemas.outings import UserOutings
from app.schemas.users import PrivacySettings, ProfileOut
from app.services import friends, outings, posts
from app.services.friends import Relation
from app.services.visibility import friend_ids, post_visible_to

router = APIRouter(tags=["users"])

FRIENDS_PREVIEW = 8


def get_user(db: Session, username: str) -> User:
    """Compte visible par les autres : les comptes non confirmés ou suspendus n'existent pas."""
    user = db.scalar(
        select(User).where(User.username == username, User.status == AccountStatus.ACTIVE)
    )
    if user is None:
        raise ApiError(404, "not_found", "Cet utilisateur n'existe pas.")
    return user


def _communities(db: Session, ids: list[int]) -> list[CommunityRef]:
    if not ids:
        return []
    rows = db.scalars(select(Community).where(Community.id.in_(ids)).order_by(Community.name))
    return [CommunityRef.model_validate(row) for row in rows]


@router.get("/users/{username}")
def get_profile(username: str, db: DbSession, viewer: ActiveUser) -> ProfileOut:
    owner = get_user(db, username)
    relation, row = friends.relation(db, viewer, owner)
    is_self = relation == Relation.SELF

    post_count = db.scalar(select(func.count()).where(Post.author_id == owner.id)) or 0
    visible_count = (
        db.scalar(
            select(func.count()).where(Post.author_id == owner.id, post_visible_to(viewer))
        )
        or 0
    )
    own_ids = list(
        db.scalars(
            select(CommunityMember.community_id).where(CommunityMember.user_id == owner.id)
        )
    )
    shown_ids = own_ids if is_self else friends.common_community_ids(db, viewer, owner)

    profile = ProfileOut(
        user=AuthorOut.model_validate(owner),
        member_since=owner.created_at,
        relation=relation,
        friends_since=(
            (row.responded_at or row.created_at) if relation == Relation.FRIENDS and row else None
        ),
        post_count=post_count,
        community_count=len(own_ids),
        friend_count=(
            friends.friend_count(db, owner) if friends.can_see_friends(db, viewer, owner) else None
        ),
        communities=_communities(db, shown_ids),
        outing_count=(
            db.scalar(select(func.count()).where(OutingParticipant.user_id == owner.id)) or 0
            if friends.can_see_outings(db, viewer, owner)
            else None
        ),
        hidden_post_count=post_count - visible_count,
        can_send_request=(
            relation == Relation.NONE and friends.can_send_request(db, viewer, owner)
        ),
    )
    if is_self:
        profile.pending_request_count = (
            db.scalar(
                select(func.count()).where(
                    Friendship.addressee_id == owner.id,
                    Friendship.status == FriendshipStatus.PENDING,
                )
            )
            or 0
        )
        preview = db.scalars(
            select(User)
            .where(User.id.in_(friend_ids(owner.id)))
            .order_by(User.display_name)
            .limit(FRIENDS_PREVIEW)
        )
        profile.friends_preview = [AuthorOut.model_validate(user) for user in preview]
    return profile


@router.get("/users/{username}/posts")
def user_posts(
    username: str,
    db: DbSession,
    viewer: ActiveUser,
    before: Annotated[int | None, Query(ge=1)] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = posts.PAGE_SIZE,
) -> PostPage:
    """Posts d'un profil : ceux publiés sur le profil et dans les communautés, si visibles."""
    owner = get_user(db, username)
    return posts.page(db, viewer, select(Post).where(Post.author_id == owner.id), before, limit)


@router.get("/users/{username}/outings")
def user_outings(username: str, db: DbSession, viewer: ActiveUser) -> UserOutings:
    """« Mes / Ses sorties à venir » : sorties où la personne participe, visibles par `viewer`."""
    owner = get_user(db, username)
    if not friends.can_see_outings(db, viewer, owner):
        return UserOutings(items=[], hidden=True)
    rows = db.scalars(
        select(Outing)
        .where(
            outings.is_participant_clause(owner.id),
            outings.outing_visible_to(viewer),
            Outing.starts_at >= utcnow(),
        )
        .order_by(Outing.starts_at)
        .options(
            selectinload(Outing.organizer),
            selectinload(Outing.stops).selectinload(OutingStop.refuge),
            selectinload(Outing.participants).selectinload(OutingParticipant.user),
        )
    ).all()
    return UserOutings(items=[outings.summary(o, viewer) for o in rows], hidden=False)


@router.get("/me/privacy")
def get_privacy(viewer: ActiveUser) -> PrivacySettings:
    return PrivacySettings.model_validate(viewer, from_attributes=True)


@router.put("/me/privacy")
def update_privacy(data: PrivacySettings, db: DbSession, viewer: ActiveUser) -> PrivacySettings:
    """« Enregistrer » (écran 05c). Ne change pas la visibilité des posts déjà publiés."""
    for field, value in data.model_dump().items():
        setattr(viewer, field, value)
    db.commit()
    return PrivacySettings.model_validate(viewer, from_attributes=True)
