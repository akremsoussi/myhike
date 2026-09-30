from pydantic import BaseModel, ConfigDict, field_validator

from app.models import Visibility
from app.schemas.auth import UtcDatetime
from app.schemas.refuges import MassifOut, RefugeSummary

POST_MAX_LENGTH = 5000


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


class CommunityDetail(CommunityOut):
    """Écran 08 : bannière et colonne latérale (le fil est chargé à part)."""

    # Quelques membres pour la colonne latérale, les plus récents en premier.
    members: list[AuthorOut]
    refuges: list[RefugeSummary]


class CommunityRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str


class PostOut(BaseModel):
    id: int
    author: AuthorOut
    community: CommunityRef | None
    body: str
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
    body: str
    visibility: Visibility
    # Absent : publié seulement sur le profil de l'auteur.
    community_slug: str | None = None

    @field_validator("body")
    @classmethod
    def check_body(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Écrivez quelques mots.")
        if len(value) > POST_MAX_LENGTH:
            raise ValueError(f"{POST_MAX_LENGTH} caractères max.")
        return value


class LikeOut(BaseModel):
    like_count: int
    liked: bool
