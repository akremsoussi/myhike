import enum
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Enum, ForeignKey, String, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow


def _values(enum_class: type[enum.Enum]) -> list[str]:
    return [member.value for member in enum_class]


class Role(enum.StrEnum):
    USER = "user"
    MODERATOR = "moderator"


class AccountStatus(enum.StrEnum):
    PENDING_EMAIL = "pending_email"
    ACTIVE = "active"
    SUSPENDED = "suspended"


class Visibility(enum.StrEnum):
    """Visibilité d'un post."""

    PUBLIC = "public"
    FRIENDS = "friends"


class Audience(enum.StrEnum):
    """Qui peut voir une partie du profil (liste d'amis, sorties à venir)."""

    EVERYONE = "everyone"
    FRIENDS = "friends"
    ME = "me"


class RequestPolicy(enum.StrEnum):
    """Qui peut m'envoyer une demande d'ami."""

    EVERYONE = "everyone"
    COMMUNITIES = "communities"  # membres d'une de mes communautés


class TokenPurpose(enum.StrEnum):
    VERIFY = "verify"
    RESET = "reset"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String(30), unique=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(60))
    # Présentation affichée sous le nom (écran 05, « Modifier le profil »).
    bio: Mapped[str] = mapped_column(String(300), default="", server_default="")
    role: Mapped[Role] = mapped_column(
        Enum(Role, values_callable=_values, name="role"), default=Role.USER
    )
    status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus, values_callable=_values, name="status"),
        default=AccountStatus.PENDING_EMAIL,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime)
    suspended_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Paramètres de confidentialité (écran 05c). `server_default` : valeurs des comptes existants.
    default_post_visibility: Mapped[Visibility] = mapped_column(
        Enum(Visibility, values_callable=_values, name="default_post_visibility"),
        default=Visibility.PUBLIC,
        server_default=Visibility.PUBLIC.value,
    )
    friends_list_audience: Mapped[Audience] = mapped_column(
        Enum(Audience, values_callable=_values, name="friends_list_audience"),
        default=Audience.FRIENDS,
        server_default=Audience.FRIENDS.value,
    )
    outings_audience: Mapped[Audience] = mapped_column(
        Enum(Audience, values_callable=_values, name="outings_audience"),
        default=Audience.EVERYONE,
        server_default=Audience.EVERYONE.value,
    )
    friend_requests_from: Mapped[RequestPolicy] = mapped_column(
        Enum(RequestPolicy, values_callable=_values, name="friend_requests_from"),
        default=RequestPolicy.EVERYONE,
        server_default=RequestPolicy.EVERYONE.value,
    )
    show_in_suggestions: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())

    email_tokens: Mapped[list["EmailToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )


class EmailToken(Base):
    """Lien envoyé par email : confirmation d'adresse ou mot de passe oublié.

    Seule l'empreinte SHA-256 du jeton est stockée : une fuite de la base ne permet pas
    de confirmer un compte.
    """

    __tablename__ = "email_tokens"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    purpose: Mapped[TokenPurpose] = mapped_column(
        Enum(TokenPurpose, values_callable=_values, name="purpose")
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    # Adresse visée par le lien : un lien envoyé avant « Modifier l'email » ne vaut plus rien.
    email: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used_at: Mapped[datetime | None] = mapped_column(DateTime)

    user: Mapped[User] = relationship(back_populates="email_tokens")


class UserSession(Base):
    """Session de connexion. Le cookie contient le jeton, la base son empreinte."""

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime)

    user: Mapped[User] = relationship()
