import enum
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow
from app.models.social import Post
from app.models.user import User


def _values(enum_class: type[enum.Enum]) -> list[str]:
    return [member.value for member in enum_class]


class ReportReason(enum.StrEnum):
    INSULTING = "insulting"  # « Propos insultants »
    SPAM = "spam"
    FAKE_PROFILE = "fake_profile"  # « Faux profil »
    OTHER = "other"


class Report(Base):
    """Signalement d'un compte, éventuellement à propos d'un de ses posts."""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    reporter_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    # Compte visé (l'auteur du post quand un post est signalé).
    target_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    post_id: Mapped[int | None] = mapped_column(ForeignKey("posts.id", ondelete="SET NULL"))
    reason: Mapped[ReportReason] = mapped_column(
        Enum(ReportReason, values_callable=_values, name="reason")
    )
    comment: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    # Classé par un modérateur (« à traiter » tant que null).
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    resolved_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )

    reporter: Mapped[User] = relationship(foreign_keys=[reporter_id])
    target: Mapped[User] = relationship(foreign_keys=[target_id])
    post: Mapped[Post | None] = relationship()


class ModerationLog(Base):
    """Journal des actions de modération (« Activité récente », écran 13).

    Le libellé est figé au moment de l'action : il reste lisible même si la communauté
    ou le compte concerné est supprimé ensuite.
    """

    __tablename__ = "moderation_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    # « Communauté « Vercors » créée », « Lucas Durand promu modérateur »…
    message: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

    actor: Mapped[User | None] = relationship()
