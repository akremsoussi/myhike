from collections.abc import Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, joinedload

from app.models import Post, PostLike, Role, User
from app.schemas.communities import AuthorOut, CommunityRef, PostOut, PostPage
from app.services.visibility import post_visible_to

PAGE_SIZE = 20


def to_out(db: Session, viewer: User, posts: Sequence[Post]) -> list[PostOut]:
    """Posts prêts à envoyer, avec j'aime comptés en deux requêtes pour toute la page."""
    ids = [post.id for post in posts]
    counts: dict[int, int] = {}
    liked: set[int] = set()
    if ids:
        rows = db.execute(
            select(PostLike.post_id, func.count())
            .where(PostLike.post_id.in_(ids))
            .group_by(PostLike.post_id)
        )
        counts = {post_id: count for post_id, count in rows}
        liked = set(
            db.scalars(
                select(PostLike.post_id).where(
                    PostLike.post_id.in_(ids), PostLike.user_id == viewer.id
                )
            )
        )
    return [
        PostOut(
            id=post.id,
            author=AuthorOut.model_validate(post.author),
            community=CommunityRef.model_validate(post.community) if post.community else None,
            body=post.body,
            visibility=post.visibility,
            created_at=post.created_at,
            like_count=counts.get(post.id, 0),
            liked=post.id in liked,
            can_delete=post.author_id == viewer.id or viewer.role == Role.MODERATOR,
        )
        for post in posts
    ]


def page(
    db: Session, viewer: User, query: Select, before: int | None, limit: int = PAGE_SIZE
) -> PostPage:
    """Page de posts visibles par `viewer`, du plus récent au plus ancien.

    Pagination par identifiant (croissant avec la date de création) : stable même si
    d'autres posts sont publiés pendant la lecture.
    """
    query = query.where(post_visible_to(viewer))
    if before is not None:
        query = query.where(Post.id < before)
    rows = db.scalars(
        query.options(joinedload(Post.author), joinedload(Post.community))
        .order_by(Post.id.desc())
        .limit(limit + 1)
    ).all()
    has_more = len(rows) > limit
    rows = rows[:limit]
    return PostPage(
        items=to_out(db, viewer, rows), next_before=rows[-1].id if has_more else None
    )
