import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow
from app.models.refuge import Refuge
from app.models.user import User


class OutingVisibility(enum.StrEnum):
    PUBLIC = "public"  # « Publique » : visible et ouverte à tous
    INVITATION = "invitation"  # « Sur invitation » : organisateur, participants et invités


class Outing(Base):
    """Sortie organisée entre utilisateurs (écrans 10 à 12)."""

    __tablename__ = "outings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(String(80))
    organizer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    # Date et heure de départ, en UTC.
    starts_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    max_participants: Mapped[int] = mapped_column(Integer)
    visibility: Mapped[OutingVisibility] = mapped_column(
        Enum(
            OutingVisibility,
            values_callable=lambda e: [m.value for m in e],
            name="outing_visibility",
        )
    )
    # Chemin tracé sur la carte : [[lat, lng], …], vide si non tracé.
    path: Mapped[list[list[float]]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    organizer: Mapped[User] = relationship()
    stops: Mapped[list["OutingStop"]] = relationship(
        back_populates="outing",
        order_by="OutingStop.position",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    participants: Mapped[list["OutingParticipant"]] = relationship(
        back_populates="outing",
        order_by="OutingParticipant.joined_at, OutingParticipant.user_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class OutingStop(Base):
    """Point de stop : un refuge, ou un point libre placé sur la carte."""

    __tablename__ = "outing_stops"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    outing_id: Mapped[int] = mapped_column(
        ForeignKey("outings.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer)
    refuge_id: Mapped[int | None] = mapped_column(
        ForeignKey("refuges.id", ondelete="SET NULL"), index=True
    )
    # Nom affiché : celui du refuge au moment de l'ajout, ou celui donné au point libre.
    name: Mapped[str] = mapped_column(String(200))
    latitude: Mapped[Decimal] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal] = mapped_column(Numeric(9, 6))

    outing: Mapped[Outing] = relationship(back_populates="stops")
    refuge: Mapped[Refuge | None] = relationship()


class OutingParticipant(Base):
    __tablename__ = "outing_participants"

    outing_id: Mapped[int] = mapped_column(
        ForeignKey("outings.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    outing: Mapped[Outing] = relationship(back_populates="participants")
    user: Mapped[User] = relationship()


class OutingInvitation(Base):
    """Invitation à une sortie « Sur invitation » (« Inviter à une sortie », écran 06)."""

    __tablename__ = "outing_invitations"

    outing_id: Mapped[int] = mapped_column(
        ForeignKey("outings.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    invited_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
