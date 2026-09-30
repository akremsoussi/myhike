"""Qui voit quels posts.

Règle unique, appliquée partout (profil, fil de communauté, posts liés à un refuge) :
un post est visible s'il est public, si on en est l'auteur, ou si on est ami avec l'auteur.
"""

from sqlalchemy import ColumnElement, Select, or_, select, union

from app.models import Friendship, FriendshipStatus, Post, User, Visibility


def friend_ids(user_id: int) -> Select:
    """Identifiants des amis (demande acceptée, dans un sens ou dans l'autre)."""
    accepted = Friendship.status == FriendshipStatus.ACCEPTED
    sent = select(Friendship.addressee_id.label("id")).where(
        Friendship.requester_id == user_id, accepted
    )
    received = select(Friendship.requester_id.label("id")).where(
        Friendship.addressee_id == user_id, accepted
    )
    return select(union(sent, received).subquery().c.id)


def post_visible_to(viewer: User) -> ColumnElement[bool]:
    """Condition SQL à ajouter à toute requête qui renvoie des posts."""
    return or_(
        Post.visibility == Visibility.PUBLIC,
        Post.author_id == viewer.id,
        Post.author_id.in_(friend_ids(viewer.id)),
    )
