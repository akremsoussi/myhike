from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.db import DbSession
from app.deps import ActiveUser
from app.models import AccountStatus, Community, Massif, Outing, Post, Refuge, User, utcnow
from app.routers.communities import community_out, counts_query
from app.routers.outings import LOAD as OUTING_LOAD
from app.schemas.communities import AuthorOut, CommunityOut
from app.schemas.refuges import RefugeSummary
from app.schemas.search import SearchOut
from app.services import outings, posts, search
from app.services.outings import outing_visible_to

router = APIRouter(tags=["search"])

# Résultats par catégorie : la page montre les premiers, la recherche s'affine ensuite.
PER_CATEGORY = 8


@router.get("/search")
def global_search(
    db: DbSession, viewer: ActiveUser, q: Annotated[str, Query(min_length=2, max_length=100)]
) -> SearchOut:
    """Refuges, communautés, randonneurs, sorties à venir et posts contenant `q`.

    Chaque catégorie applique ses règles habituelles : sorties « Sur invitation » et posts
    « Amis uniquement » seulement pour ceux qui peuvent les voir, comptes actifs seulement.
    """
    refuges = db.scalars(
        select(Refuge)
        .outerjoin(Refuge.massif)
        .where(search.matches(q, Refuge.name, Massif.name))
        .options(joinedload(Refuge.massif))
        .order_by(Refuge.name, Refuge.id)
        .limit(PER_CATEGORY)
    ).all()
    communities = db.execute(
        counts_query(viewer)
        .where(search.matches(q, Community.name, Community.region, Community.description))
        .order_by(Community.name)
        .limit(PER_CATEGORY)
    ).all()
    users = db.scalars(
        select(User)
        .where(
            User.status == AccountStatus.ACTIVE,
            search.matches(q, User.display_name, User.username),
        )
        .order_by(User.display_name, User.id)
        .limit(PER_CATEGORY)
    ).all()
    upcoming = db.scalars(
        select(Outing)
        .where(
            search.matches(q, Outing.title),
            Outing.starts_at >= utcnow(),
            outing_visible_to(viewer),
        )
        .options(*OUTING_LOAD)
        .order_by(Outing.starts_at)
        .limit(PER_CATEGORY)
    ).all()
    found_posts = posts.page(
        db, viewer, select(Post).where(search.matches(q, Post.body)), None, PER_CATEGORY
    )
    return SearchOut(
        refuges=[RefugeSummary.model_validate(refuge) for refuge in refuges],
        communities=[CommunityOut(**community_out(*row)) for row in communities],
        users=[AuthorOut.model_validate(user) for user in users],
        outings=[outings.summary(outing, viewer) for outing in upcoming],
        posts=found_posts.items,
    )
