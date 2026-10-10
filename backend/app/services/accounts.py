"""Règles métier des comptes : inscription, confirmation d'email, sessions, connexion."""

import math
from datetime import datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config import settings
from app.errors import ApiError
from app.models import AccountStatus, EmailToken, TokenPurpose, User, UserSession, utcnow
from app.schemas.auth import RegisterIn, VerificationOut
from app.services.security import hash_password, hash_token, new_token, verify_password


def _email_taken(db: Session, email: str) -> bool:
    return db.scalar(select(User.id).where(User.email == email)) is not None


def register(db: Session, data: RegisterIn) -> tuple[User, str]:
    """Crée un compte `pending_email` et renvoie le jeton de confirmation à envoyer."""
    fields: dict[str, str] = {}
    if db.scalar(select(User.id).where(User.username == data.username)) is not None:
        fields["username"] = "Ce nom d'utilisateur est déjà pris."
    if _email_taken(db, data.email):
        fields["email"] = "Un compte existe déjà avec cette adresse."
    if fields:
        raise ApiError(409, "conflict", "Ce compte existe déjà.", fields=fields)

    user = User(
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        display_name=data.username,
    )
    db.add(user)
    db.flush()
    token = issue_verification(db, user)
    db.commit()
    return user, token


def issue_verification(db: Session, user: User) -> str:
    """Nouveau lien de confirmation. Les liens précédents cessent de fonctionner."""
    now = utcnow()
    db.execute(
        update(EmailToken)
        .where(
            EmailToken.user_id == user.id,
            EmailToken.purpose == TokenPurpose.VERIFY,
            EmailToken.used_at.is_(None),
        )
        .values(used_at=now)
    )
    token, token_hash = new_token()
    db.add(
        EmailToken(
            user_id=user.id,
            purpose=TokenPurpose.VERIFY,
            token_hash=token_hash,
            email=user.email,
            created_at=now,
            expires_at=now + timedelta(hours=settings.verification_hours),
        )
    )
    return token


def _latest_verification(db: Session, user: User) -> EmailToken | None:
    return db.scalar(
        select(EmailToken)
        .where(
            EmailToken.user_id == user.id,
            EmailToken.purpose == TokenPurpose.VERIFY,
            EmailToken.used_at.is_(None),
        )
        .order_by(EmailToken.created_at.desc(), EmailToken.id.desc())
        .limit(1)
    )


def verification_info(db: Session, user: User) -> VerificationOut | None:
    if user.status != AccountStatus.PENDING_EMAIL:
        return None
    token = _latest_verification(db, user)
    if token is None:
        return None
    return VerificationOut(
        email=token.email,
        sent_at=token.created_at,
        expires_at=token.expires_at,
        resend_available_at=token.created_at + timedelta(seconds=settings.resend_cooldown_seconds),
    )


def verify_email(db: Session, token: str) -> User:
    """Active le compte lié au lien. Cliquer deux fois sur le même lien n'est pas une erreur."""
    row = db.scalar(
        select(EmailToken).where(
            EmailToken.token_hash == hash_token(token),
            EmailToken.purpose == TokenPurpose.VERIFY,
        )
    )
    invalid = ApiError(400, "invalid_token", "Ce lien n'est pas valide. Demandez-en un nouveau.")
    if row is None:
        raise invalid
    user = row.user

    if row.used_at is not None:
        # Lien déjà utilisé : succès si c'est lui qui a confirmé l'adresse actuelle,
        # sinon il a été remplacé par un lien plus récent.
        if user.email_verified_at is not None and row.email == user.email:
            return user
        raise invalid
    if row.email != user.email:
        raise invalid
    if row.expires_at <= utcnow():
        raise ApiError(410, "token_expired", "Ce lien a expiré. Demandez-en un nouveau.")

    now = utcnow()
    row.used_at = now
    user.email_verified_at = now
    # Un compte suspendu entre-temps le reste.
    if user.status == AccountStatus.PENDING_EMAIL:
        user.status = AccountStatus.ACTIVE
    db.commit()
    return user


def _require_pending(user: User) -> None:
    if user.status != AccountStatus.PENDING_EMAIL:
        raise ApiError(409, "already_verified", "Votre adresse est déjà confirmée.")


def resend_verification(db: Session, user: User) -> str:
    _require_pending(user)
    latest = _latest_verification(db, user)
    if latest is not None:
        available_at = latest.created_at + timedelta(seconds=settings.resend_cooldown_seconds)
        wait = (available_at - utcnow()).total_seconds()
        if wait > 0:
            raise ApiError(
                429,
                "resend_too_soon",
                "Patientez avant de renvoyer l'email.",
                retry_after=math.ceil(wait),
            )
    token = issue_verification(db, user)
    db.commit()
    return token


def change_pending_email(db: Session, user: User, email: str) -> str:
    """« Modifier l'email » de l'écran 02b : seulement tant que l'adresse n'est pas confirmée."""
    _require_pending(user)
    if email == user.email:
        message = "C'est déjà votre adresse."
        raise ApiError(409, "conflict", message, fields={"email": message})
    if _email_taken(db, email):
        message = "Un compte existe déjà avec cette adresse."
        raise ApiError(409, "conflict", message, fields={"email": message})
    user.email = email
    token = issue_verification(db, user)
    db.commit()
    return token


def request_password_reset(db: Session, email: str) -> tuple[User, str] | None:
    """Jeton « Mot de passe oublié » à envoyer, ou None s'il n'y a rien à envoyer.

    None sans erreur : pas de compte (ou compte suspendu), ou un lien vient déjà d'être
    envoyé. La réponse de l'API est la même dans tous les cas, pour ne pas révéler quelles
    adresses ont un compte.
    """
    user = db.scalar(select(User).where(User.email == email))
    if user is None or user.status == AccountStatus.SUSPENDED:
        return None
    now = utcnow()
    recent = db.scalar(
        select(EmailToken.id).where(
            EmailToken.user_id == user.id,
            EmailToken.purpose == TokenPurpose.RESET,
            EmailToken.created_at > now - timedelta(seconds=settings.resend_cooldown_seconds),
        )
    )
    if recent is not None:
        return None
    _invalidate_resets(db, user, now)
    token, token_hash = new_token()
    db.add(
        EmailToken(
            user_id=user.id,
            purpose=TokenPurpose.RESET,
            token_hash=token_hash,
            email=user.email,
            created_at=now,
            expires_at=now + timedelta(minutes=settings.password_reset_minutes),
        )
    )
    db.commit()
    return user, token


def _invalidate_resets(db: Session, user: User, now: datetime) -> None:
    db.execute(
        update(EmailToken)
        .where(
            EmailToken.user_id == user.id,
            EmailToken.purpose == TokenPurpose.RESET,
            EmailToken.used_at.is_(None),
        )
        .values(used_at=now)
    )


def reset_password(db: Session, token: str, password: str) -> User:
    """Nouveau mot de passe depuis le lien reçu. Toutes les sessions ouvertes sont fermées."""
    row = db.scalar(
        select(EmailToken).where(
            EmailToken.token_hash == hash_token(token),
            EmailToken.purpose == TokenPurpose.RESET,
        )
    )
    if row is None or row.used_at is not None or row.email != row.user.email:
        raise ApiError(400, "invalid_token", "Ce lien n'est pas valide. Demandez-en un nouveau.")
    if row.expires_at <= utcnow():
        raise ApiError(410, "token_expired", "Ce lien a expiré. Demandez-en un nouveau.")
    user = row.user
    if user.status == AccountStatus.SUSPENDED:
        raise ApiError(403, "account_suspended", "Ce compte est suspendu.")

    now = utcnow()
    _invalidate_resets(db, user, now)
    user.password_hash = hash_password(password)
    # Le lien est arrivé dans la boîte de l'adresse du compte : elle est donc confirmée.
    if user.status == AccountStatus.PENDING_EMAIL:
        user.status = AccountStatus.ACTIVE
        user.email_verified_at = now
    db.execute(
        update(UserSession)
        .where(UserSession.user_id == user.id, UserSession.revoked_at.is_(None))
        .values(revoked_at=now)
    )
    db.commit()
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if not verify_password(password, user.password_hash if user else None):
        raise ApiError(401, "invalid_credentials", "Email ou mot de passe incorrect.")
    assert user is not None
    if user.status == AccountStatus.SUSPENDED:
        raise ApiError(403, "account_suspended", "Ce compte est suspendu.")
    return user


def create_session(db: Session, user: User) -> str:
    token, token_hash = new_token()
    now = utcnow()
    db.add(
        UserSession(
            user_id=user.id,
            token_hash=token_hash,
            created_at=now,
            expires_at=now + timedelta(days=settings.session_days),
        )
    )
    db.commit()
    return token


def session_user(db: Session, token: str) -> User | None:
    session = db.scalar(
        select(UserSession).where(
            UserSession.token_hash == hash_token(token),
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > utcnow(),
        )
    )
    return session.user if session else None


def revoke_session(db: Session, token: str) -> None:
    db.execute(
        update(UserSession)
        .where(UserSession.token_hash == hash_token(token), UserSession.revoked_at.is_(None))
        .values(revoked_at=utcnow())
    )
    db.commit()
