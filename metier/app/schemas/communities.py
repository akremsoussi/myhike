from pydantic import BaseModel, ConfigDict, field_validator

from app.models import Visibility
from app.schemas.auth import UtcDatetime
from app.schemas.media import PhotoOut
from app.schemas.refuges import MassifOut, RefugeSummary

POST_MAX_LENGTH = 5000
POST_MAX_PHOTOS = 4
# Un GPX est simplifié par le navigateur avant l'envoi.
POST_MAX_PATH_POINTS = 2000

# [latitude, longitude], ou [latitude, longitude, altitude] pour un chemin importé (GPX).
PathPoint = tuple[float, float] | tuple[float, float, float]


class AuthorOut(BaseModel):
    """Ce qu'on montre d'un utilisateur à côté de son contenu (jamais son email)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    display_name: str


class CommunityOut(BaseModel):
    """Carte de l'écran 07."""

    id: int
    slug: str
    name: str
    description: str
    region: str
    massif: MassifOut | None
    member_count: int
    post_count: int
    is_member: bool
    banner: PhotoOut | None
    icon: PhotoOut | None


class CommunityDetail(CommunityOut):
    """Écran 08 : bannière et colonne latérale (le fil est chargé à part)."""

    # Quelques membres pour la colonne latérale, les plus récents en premier.
    members: list[AuthorOut]
    refuges: list[RefugeSummary]


class MemberOut(BaseModel):
    user: AuthorOut
    joined_at: UtcDatetime


class MemberPage(BaseModel):
    """Liste complète des membres (« Tout voir », écran 08)."""

    # Nombre de membres correspondant à la recherche.
    total: int
    items: list[MemberOut]


class CommunityRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str


class RefugeRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class PostOut(BaseModel):
    id: int
    author: AuthorOut
    community: CommunityRef | None
    refuge: RefugeRef | None
    body: str
    photos: list[PhotoOut]
    # Chemin simplifié pour l'aperçu, en [latitude, longitude] ; null sans chemin.
    path: list[tuple[float, float]] | None
    distance_m: int | None
    # Calculé à partir des altitudes du GPX ; null pour un chemin tracé sur la carte.
    elevation_gain_m: int | None
    visibility: Visibility
    created_at: UtcDatetime
    like_count: int
    liked: bool
    # L'auteur (ou un modérateur) peut supprimer le post depuis le menu « ⋯ ».
    can_delete: bool


class PostPage(BaseModel):
    items: list[PostOut]
    # À passer en `before` pour la page suivante ; null s'il n'y en a plus.
    next_before: int | None


class PostIn(BaseModel):
    body: str = ""
    visibility: Visibility
    # Absent : publié seulement sur le profil de l'auteur.
    community_slug: str | None = None
    # Images envoyées avant (POST /api/uploads), dans l'ordre d'affichage.
    photo_ids: list[int] = []
    path: list[PathPoint] | None = None
    refuge_id: int | None = None

    @field_validator("body")
    @classmethod
    def check_body(cls, value: str) -> str:
        value = value.strip()
        if len(value) > POST_MAX_LENGTH:
            raise ValueError(f"{POST_MAX_LENGTH} caractères max.")
        return value

    @field_validator("photo_ids")
    @classmethod
    def check_photos(cls, value: list[int]) -> list[int]:
        value = list(dict.fromkeys(value))  # sans doublons, dans l'ordre
        if len(value) > POST_MAX_PHOTOS:
            raise ValueError(f"{POST_MAX_PHOTOS} photos au plus.")
        return value

    @field_validator("path")
    @classmethod
    def check_path(cls, value: list[PathPoint] | None) -> list[PathPoint] | None:
        if not value:
            return None
        if len(value) < 2:
            raise ValueError("Un chemin a au moins deux points.")
        if len(value) > POST_MAX_PATH_POINTS:
            raise ValueError(f"{POST_MAX_PATH_POINTS} points au plus.")
        for point in value:
            if not (-90 <= point[0] <= 90 and -180 <= point[1] <= 180):
                raise ValueError("Coordonnées hors limites.")
            if len(point) == 3 and not -500 <= point[2] <= 9000:
                raise ValueError("Altitude hors limites.")
        return value


class LikeOut(BaseModel):
    like_count: int
    liked: bool
