from datetime import UTC, datetime

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Noms de contraintes stables, pour que les migrations Alembic restent lisibles.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def utcnow() -> datetime:
    """Date UTC sans fuseau, à la seconde : c'est ce que stocke une colonne DATETIME de MySQL.

    Sans troncature, MySQL arrondirait les microsecondes et pourrait placer une date
    jusqu'à une demi-seconde dans le futur.
    """
    return datetime.now(UTC).replace(tzinfo=None, microsecond=0)
