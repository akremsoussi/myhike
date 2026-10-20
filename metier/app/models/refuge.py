import enum
import re
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow


class RefugeKind(enum.StrEnum):
    """Types de points importés depuis refuges.info (id du type entre parenthèses)."""

    UNGUARDED_HUT = "unguarded_hut"  # cabane non gardée (7)
    GITE = "gite"  # gîte d'étape (9)
    GUARDED_HUT = "guarded_hut"  # refuge gardé (10)


GUARDED_KINDS = (RefugeKind.GUARDED_HUT, RefugeKind.GITE)

# Numéro français (« 04 92 23 50 24 », « 04.92.23.50.24 », « +33 4 92 23 50 24 »).
PHONE_RE = re.compile(r"(?:\+33\s?|0)([1-9])(?:[\s.-]?(\d{2})){4}")


class Massif(Base):
    __tablename__ = "massifs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    # Identifiant du polygone sur refuges.info.
    external_id: Mapped[int] = mapped_column(Integer, unique=True)
    name: Mapped[str] = mapped_column(String(120))

    refuges: Mapped[list["Refuge"]] = relationship(back_populates="massif")


class Refuge(Base):
    """Hébergement de montagne. Données refuges.info, licence CC BY-SA 2.0 (à citer)."""

    __tablename__ = "refuges"
    __table_args__ = (Index("ix_refuges_lat_lng", "latitude", "longitude"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    external_id: Mapped[int] = mapped_column(Integer, unique=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    kind: Mapped[RefugeKind] = mapped_column(
        Enum(RefugeKind, values_callable=lambda e: [m.value for m in e], name="kind")
    )
    latitude: Mapped[Decimal] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal] = mapped_column(Numeric(9, 6))
    altitude: Mapped[int | None] = mapped_column(Integer)
    capacity: Mapped[int | None] = mapped_column(Integer)
    massif_id: Mapped[int | None] = mapped_column(
        ForeignKey("massifs.id", ondelete="SET NULL"), index=True
    )
    # État brut de refuges.info (« Fermée », « Clés à récupérer »…), vide si ouvert.
    state: Mapped[str | None] = mapped_column(String(80))
    access: Mapped[str | None] = mapped_column(Text)
    remarks: Mapped[str | None] = mapped_column(Text)
    owner_info: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(String(255))
    source_updated_at: Mapped[datetime | None] = mapped_column(DateTime)
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    # Dernière lecture des photos sur refuges.info (`app.scripts.import_refuge_photos`).
    photos_checked_at: Mapped[datetime | None] = mapped_column(DateTime)

    massif: Mapped[Massif | None] = relationship(back_populates="refuges")
    photos: Mapped[list["RefugePhoto"]] = relationship(
        back_populates="refuge",
        order_by="RefugePhoto.position",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def is_guarded(self) -> bool:
        return self.kind in GUARDED_KINDS

    @property
    def phone(self) -> str | None:
        """Premier numéro du texte « Propriétaires », au format « 04 92 23 50 24 »."""
        match = PHONE_RE.search(self.owner_info or "")
        if match is None:
            return None
        digits = re.sub(r"\D", "", match.group(0))
        digits = "0" + digits[2:] if digits.startswith("33") else digits
        return " ".join(digits[i : i + 2] for i in range(0, 10, 2))


class RefugePhoto(Base):
    """Photo d'un commentaire refuges.info (CC BY-SA 2.0 : auteur et source à citer).

    Copiée une fois dans `MEDIA_DIR` (table `uploads`) : le navigateur ne charge jamais
    d'image depuis refuges.info.
    """

    __tablename__ = "refuge_photos"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    refuge_id: Mapped[int] = mapped_column(ForeignKey("refuges.id", ondelete="CASCADE"), index=True)
    upload_id: Mapped[int] = mapped_column(
        ForeignKey("uploads.id", ondelete="CASCADE"), unique=True
    )
    # Identifiant du commentaire sur refuges.info : une photo n'est copiée qu'une fois.
    external_id: Mapped[int] = mapped_column(Integer, unique=True)
    # Vide quand le commentaire est anonyme.
    author: Mapped[str] = mapped_column(String(120), default="")
    caption: Mapped[str] = mapped_column(String(300), default="")
    taken_at: Mapped[datetime | None] = mapped_column(DateTime)
    # Ordre d'affichage : la plus récente d'abord.
    position: Mapped[int] = mapped_column(Integer, default=0)

    refuge: Mapped[Refuge] = relationship(back_populates="photos")
    upload: Mapped["Upload"] = relationship()  # noqa: F821

    # Pour l'API (même forme que les autres images).
    @property
    def url(self) -> str:
        return self.upload.url

    @property
    def width(self) -> int:
        return self.upload.width

    @property
    def height(self) -> int:
        return self.upload.height
