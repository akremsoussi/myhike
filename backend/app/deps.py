"""Dépendances d'accès : qui est connecté, et avec quel statut."""

from typing import Annotated

from fastapi import Cookie, Depends

from app.db import DbSession
from app.errors import ApiError
from app.models import AccountStatus, Role, User
from app.services import accounts

SESSION_COOKIE = "refuges_session"

SessionToken = Annotated[str | None, Cookie(alias=SESSION_COOKIE)]


def get_current_user(db: DbSession, token: SessionToken = None) -> User:
    """Utilisateur connecté, quel que soit son statut sauf suspendu."""
    user = accounts.session_user(db, token) if token else None
    if user is None:
        raise ApiError(401, "not_authenticated", "Connectez-vous pour continuer.")
    if user.status == AccountStatus.SUSPENDED:
        raise ApiError(403, "account_suspended", "Ce compte est suspendu.")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_active(user: CurrentUser) -> User:
    """Compte confirmé : tout le site sauf l'écran 02b."""
    if user.status != AccountStatus.ACTIVE:
        raise ApiError(403, "account_pending", "Confirmez d'abord votre adresse email.")
    return user


ActiveUser = Annotated[User, Depends(require_active)]


def require_moderator(user: ActiveUser) -> User:
    if user.role != Role.MODERATOR:
        raise ApiError(403, "forbidden", "Réservé aux modérateurs.")
    return user


ModeratorUser = Annotated[User, Depends(require_moderator)]
