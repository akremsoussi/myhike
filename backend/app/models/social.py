import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow
from app.models.refuge import Massif, Refuge
from app.models.user import User, Visibility


def _values(enum_class: type[enum.Enum]) -> list[str]:
    return [member.value for member in enum_class]


class FriendshipStatus(enum.StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


# Refuges rattachés à une communauté (écrans 08 et 15).
community_refuges = Table(
    "community_refuges",
    Base.metadata,
    Column(
        "community_id", ForeignKey("communities.id", ondelete="CASCADE"), primary_key=True
    ),
    Column("refuge_id", ForeignKey("refuges.id", ondelete="CASCADE"), primary_key=True),
)


class Community(Base):
    __tablename__ = "communities"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(Text, default="")
    # Grande région des filtres de l'écran 07 (Alpes, Pyrénées, Préalpes…).
    region: Mapped[str] = mapped_column(String(40), index=True)
    massif_id: Mapped[int | None] = mapped_column(
        ForeignKey("massifs.id", ondelete="SET NULL"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    massif: Mapped[Massif | None] = relationship()
    refuges: Mapped[list[Refuge]] = relationship(
        secondary=community_refuges, order_by=Refuge.name
    )
    memberships: Mapped[list["CommunityMember"]] = relationship(
        back_populates="community", cascade="all, delete-orphan", passive_deletes=True
    )


class CommunityMember(Base):
    __tablename__ = "community_members"

    community_id: Mapped[int] = mapped_column(
        ForeignKey("communities.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    community: Mapped[Community] = relationship(back_populates="memberships")
    user: Mapped[User] = relationship()


class Friendship(Base):
    """Demande d'ami. Une fois acceptée, la relation vaut dans les deux sens."""

    __tablename__ = "friendships"
    __table_args__ = (UniqueConstraint("requester_id", "addressee_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    addressee_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[FriendshipStatus] = mapped_column(
        Enum(FriendshipStatus, values_callable=_values, name="friendship_status"),
        default=FriendshipStatus.PENDING,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime)


class Post(Base):
    """Publication sur le profil de l'auteur, et aussi dans une communauté si `community_id`."""

    __tablename__ = "posts"
    __table_args__ = (Index("ix_posts_community_created", "community_id", "created_at"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    community_id: Mapped[int | None] = mapped_column(
        ForeignKey("communities.id", ondelete="CASCADE")
    )
    body: Mapped[str] = mapped_column(Text)
    visibility: Mapped[Visibility] = mapped_column(
        Enum(Visibility, values_callable=_values, name="visibility")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    author: Mapped[User] = relationship()
    community: Mapped[Community | None] = relationship()


class PostLike(Base):
    __tablename__ = "post_likes"

    post_id: Mapped[int] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
