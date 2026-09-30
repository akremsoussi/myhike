from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models import OutingVisibility
from app.schemas.auth import UtcDatetime
from app.schemas.communities import AuthorOut

MAX_STOPS = 15
MAX_PATH_POINTS = 500
MIN_PLACES, MAX_PLACES = 2, 50

LatLng = tuple[float, float]


def _check_latlng(point: LatLng) -> LatLng:
    lat, lng = point
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        raise ValueError("Coordonnées hors limites.")
    return point


class StopIn(BaseModel):
    """Un refuge (`refuge_id`), ou un point libre (`name`, `latitude`, `longitude`)."""

    refuge_id: int | None = None
    name: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    @model_validator(mode="after")
    def check_kind(self) -> "StopIn":
        if self.refuge_id is not None:
            return self
        if self.latitude is None or self.longitude is None:
            raise ValueError("Un point libre doit être placé sur la carte.")
        _check_latlng((self.latitude, self.longitude))
        self.name = (self.name or "").strip()[:200] or "Point libre"
        return self


class OutingIn(BaseModel):
    """Écran 12 (création et modification)."""

    title: str
    # Date et heure de départ avec fuseau (le navigateur envoie l'heure locale + décalage).
    starts_at: datetime
    max_participants: int = Field(ge=MIN_PLACES, le=MAX_PLACES)
    visibility: OutingVisibility
    stops: list[StopIn]
    path: list[LatLng] = []

    @field_validator("title")
    @classmethod
    def check_title(cls, value: str) -> str:
        value = value.strip()
        if not 3 <= len(value) <= 80:
            raise ValueError("3 à 80 caractères.")
        return value

    @field_validator("starts_at")
    @classmethod
    def to_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Fuseau horaire manquant.")
        return value.astimezone(UTC).replace(tzinfo=None, second=0, microsecond=0)

    @field_validator("stops")
    @classmethod
    def check_stops(cls, value: list[StopIn]) -> list[StopIn]:
        if not 1 <= len(value) <= MAX_STOPS:
            raise ValueError(f"Entre 1 et {MAX_STOPS} points de stop.")
        return value

    @field_validator("path")
    @classmethod
    def check_path(cls, value: list[LatLng]) -> list[LatLng]:
        if len(value) > MAX_PATH_POINTS:
            raise ValueError(f"{MAX_PATH_POINTS} points au plus.")
        return [_check_latlng(point) for point in value]


class StopOut(BaseModel):
    position: int
    name: str
    latitude: float
    longitude: float
    refuge_id: int | None
    # Altitude du refuge, inconnue pour un point libre.
    altitude: int | None


OutingStatus = Literal["open", "full"]


class OutingSummary(BaseModel):
    """Carte de l'écran 10."""

    id: int
    title: str
    starts_at: UtcDatetime
    organizer: AuthorOut
    visibility: OutingVisibility
    status: OutingStatus
    participant_count: int
    max_participants: int
    stop_count: int
    # Trois premiers participants (avatars de la carte).
    participants_preview: list[AuthorOut]
    # Tracé à dessiner dans la vignette : le chemin, ou à défaut les points de stop.
    preview: list[LatLng]
    is_participant: bool


class OutingDetail(OutingSummary):
    """Écran 11."""

    stops: list[StopOut]
    participants: list[AuthorOut]
    path: list[LatLng]
    distance_m: int
    # Somme des montées entre points de stop d'altitude connue (refuges) : approximation.
    elevation_gain_m: int | None
    is_organizer: bool
    is_invited: bool
    can_join: bool


class InvitationIn(BaseModel):
    username: str


class UserOutings(BaseModel):
    """Sorties à venir d'un profil. `hidden` : le réglage de confidentialité les masque."""

    items: list[OutingSummary]
    hidden: bool
