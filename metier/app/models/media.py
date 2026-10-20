from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utcnow


class Upload(Base):
    """Image envoyée par un utilisateur, enregistrée sur le disque (`settings.media_dir`).

    Elle est d'abord envoyée seule, puis rattachée : à un post (`post_id`), ou à une
    communauté comme bannière ou icône (`communities.banner_id` / `icon_id`). Une image
    jamais rattachée est supprimée par `app.scripts.clean_uploads`.
    """

    __tablename__ = "uploads"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    # Nom du fichier, aléatoire : ne révèle ni l'auteur ni l'ordre d'envoi.
    key: Mapped[str] = mapped_column(String(32), unique=True)
    # Sans propriétaire si son compte est supprimé (la bannière d'une communauté reste).
    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    post_id: Mapped[int | None] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"), index=True
    )
    # Ordre des photos dans le post.
    position: Mapped[int] = mapped_column(SmallInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    @property
    def url(self) -> str:
        return f"/api/media/{self.key}.webp"
