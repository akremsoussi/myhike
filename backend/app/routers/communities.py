from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db import DbSession
from app.deps import ActiveUser
from app.errors import ApiError
from app.models import Community, CommunityMember, Post, Refuge, User
from app.schemas.communities import AuthorOut, CommunityDetail, CommunityOut, PostPage
from app.schemas.refuges import MassifOut, RefugeSummary
from app.services import posts

router = APIRouter(prefix="/communities", tags=["communities"])

MEMBERS_PREVIEW = 8


def _counts_query(viewer: User):
    member_count = (
        select(func.count())
        .where(CommunityMember.community_id == Community.id)
        .scalar_subquery()
    )
    post_count = select(func.count()).where(Post.community_id == Community.id).scalar_subquery()
    is_member = exists().where(
        CommunityMember.community_id == Community.id, CommunityMember.user_id == viewer.id
    )
    return select(Community, member_count, post_count, is_member).options(
        joinedload(Community.massif)
    )


def _out(community: Community, member_count: int, post_count: int, is_member: bool) -> dict:
    return {
        "id": community.id,
        "slug": community.slug,
        "name": community.name,
        "description": community.description,
        "region": community.region,
        "massif": MassifOut.model_validate(community.massif) if community.massif else None,
        "member_count": member_count,
        "post_count": post_count,
        "is_member": bool(is_member),
    }


def _get(db: Session, slug: str) -> Community:
    community = db.scalar(select(Community).where(Community.slug == slug))
    if community is None:
        raise ApiError(404, "not_found", "Cette communauté n'existe pas.")
    return community


def _summary(db: Session, viewer: User, slug: str) -> CommunityOut:
    row = db.execute(_counts_query(viewer).where(Community.slug == slug)).one()
    return CommunityOut(**_out(*row))


@router.get("")
def list_communities(db: DbSession, viewer: ActiveUser) -> list[CommunityOut]:
    """Toutes les communautés (écran 07). Il y en a peu : le front filtre et cherche."""
    rows = db.execute(_counts_query(viewer).order_by(Community.name)).all()
    return [CommunityOut(**_out(*row)) for row in rows]


@router.get("/{slug}")
def get_community(slug: str, db: DbSession, viewer: ActiveUser) -> CommunityDetail:
    row = db.execute(
        _counts_query(viewer)
        .where(Community.slug == slug)
        .options(selectinload(Community.refuges).joinedload(Refuge.massif))
    ).one_or_none()
    if row is None:
        raise ApiError(404, "not_found", "Cette communauté n'existe pas.")
    community = row[0]
    members = db.scalars(
        select(User)
        .join(CommunityMember, CommunityMember.user_id == User.id)
        .where(CommunityMember.community_id == community.id)
        .order_by(CommunityMember.joined_at.desc(), User.id.desc())
        .limit(MEMBERS_PREVIEW)
    ).all()
    return CommunityDetail(
        **_out(*row),
        members=[AuthorOut.model_validate(user) for user in members],
        refuges=[RefugeSummary.model_validate(refuge) for refuge in community.refuges],
    )


@router.put("/{slug}/membership")
def join(slug: str, db: DbSession, viewer: ActiveUser) -> CommunityOut:
    """Rejoindre (« Rejoindre » → « Inscrit ✓ »). Sans effet si déjà membre."""
    community = _get(db, slug)
    if db.get(CommunityMember, (community.id, viewer.id)) is None:
        db.add(CommunityMember(community_id=community.id, user_id=viewer.id))
        db.commit()
    return _summary(db, viewer, slug)


@router.delete("/{slug}/membership")
def leave(slug: str, db: DbSession, viewer: ActiveUser) -> CommunityOut:
    """« Quitter la communauté ». Les posts déjà publiés restent."""
    community = _get(db, slug)
    membership = db.get(CommunityMember, (community.id, viewer.id))
    if membership is not None:
        db.delete(membership)
        db.commit()
    return _summary(db, viewer, slug)


@router.get("/{slug}/posts")
def community_posts(
    slug: str,
    db: DbSession,
    viewer: ActiveUser,
    before: Annotated[int | None, Query(ge=1)] = None,
    limit: Annotated[int, Query(ge=1, le=50)] = posts.PAGE_SIZE,
) -> PostPage:
    """Fil de la communauté : seulement les posts que `viewer` a le droit de voir."""
    community = _get(db, slug)
    query = select(Post).where(Post.community_id == community.id)
    return posts.page(db, viewer, query, before, limit)
