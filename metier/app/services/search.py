"""Recherche texte (barre de navigation, liste des refuges, membres d'une communauté)."""

from sqlalchemy import ColumnElement, or_
from sqlalchemy.orm import InstrumentedAttribute


def contains_pattern(text: str) -> str:
    """Motif LIKE « contient `text` », avec % et _ pris au pied de la lettre."""
    escaped = text.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def matches(text: str, *columns: InstrumentedAttribute) -> ColumnElement[bool]:
    """Une des colonnes contient `text`.

    Collation MySQL utf8mb4_0900_ai_ci : insensible à la casse et aux accents.
    """
    pattern = contains_pattern(text)
    return or_(*(column.like(pattern) for column in columns))
