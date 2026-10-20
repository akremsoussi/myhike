from fastapi import APIRouter, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import DbSession
from app.deps import ActiveUser
from app.errors import ApiError
from app.models import Community, CommunityMember, Post, PostLike, Refuge, Role, User
from app.schemas.communities import LikeOut, PostIn, PostOut
from app.services import media, moderation, posts
from app.services.visibility import post_visible_to

router = APIRouter(prefix="/posts", tags=["posts"])


def _visible_post(db: Session, viewer: User, post_id: int) -> Post:
    """Post lisible par `viewer`. Un post invisible répond 404, comme s'il n'existait pas."""
    post = db.scalar(select(Post).where(Post.id == post_id, post_visible_to(viewer)))
    if post is None:
        raise ApiError(404, "not_found", "Ce post n'existe pas.")
    return post


@router.post("", status_code=status.HTTP_201_CREATED)
def create_post(data: PostIn, db: DbSession, viewer: ActiveUser) -> PostOut:
    """Écran 09. Dans une communauté, il faut en être membre."""
    # Une photo ou un chemin seul suffit (« Partager une photo ou un chemin… »).
    if not data.body and not data.photo_ids and not data.path:
        raise ApiError(
            422,
            "validation_error",
            "Certains champs sont invalides.",
            fields={"body": "Écrivez quelques mots, ajoutez une photo ou un chemin."},
        )
    refuge = None
    if data.refuge_id is not None:
        refuge = db.get(Refuge, data.refuge_id)
        if refuge is None:
            raise ApiError(
                422,
                "validation_error",
                "Certains champs sont invalides.",
                fields={"refuge_id": "Ce refuge n'existe pas."},
            )
    community = None
    if data.community_slug is not None:
        community = db.scalar(select(Community).where(Community.slug == data.community_slug))
        if community is None:
            raise ApiError(404, "not_found", "Cette communauté n'existe pas.")
        if db.get(CommunityMember, (community.id, viewer.id)) is None:
            raise ApiError(403, "not_member", "Rejoignez la communauté pour y publier.")
    post = Post(
        author=viewer,
        community=community,
        refuge=refuge,
        body=data.body,
        visibility=data.visibility,
    )
    posts.set_path(post, data.path)
    for position, photo in enumerate(media.claim(db, viewer, data.photo_ids, "photo_ids")):
        photo.position = position
        post.photos.append(photo)
    db.add(post)
    db.commit()
    return posts.to_out(db, viewer, [post])[0]


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: DbSession, viewer: ActiveUser) -> None:
    post = _visible_post(db, viewer, post_id)
    if post.author_id != viewer.id and viewer.role not in (Role.MODERATOR, Role.SUPER_ADMIN):
        raise ApiError(403, "forbidden", "Seul l'auteur peut supprimer ce post.")
    if post.author_id != viewer.id:
        moderation.log(db, viewer, moderation.post_deleted_message(post))
    db.delete(post)
    db.commit()


def _likes(db: Session, viewer: User, post: Post) -> LikeOut:
    count = db.scalar(select(func.count()).where(PostLike.post_id == post.id)) or 0
    liked = db.get(PostLike, (post.id, viewer.id)) is not None
    return LikeOut(like_count=count, liked=liked)


@router.put("/{post_id}/like")
def like(post_id: int, db: DbSession, viewer: ActiveUser) -> LikeOut:
    post = _visible_post(db, viewer, post_id)
    if db.get(PostLike, (post.id, viewer.id)) is None:
        db.add(PostLike(post_id=post.id, user_id=viewer.id))
        db.commit()
    return _likes(db, viewer, post)


@router.delete("/{post_id}/like")
def unlike(post_id: int, db: DbSession, viewer: ActiveUser) -> LikeOut:
    post = _visible_post(db, viewer, post_id)
    existing = db.get(PostLike, (post.id, viewer.id))
    if existing is not None:
        db.delete(existing)
        db.commit()
    return _likes(db, viewer, post)
