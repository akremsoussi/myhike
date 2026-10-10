from pydantic import BaseModel, field_validator

from app.models import Audience, RequestPolicy, Visibility
from app.schemas.auth import UtcDatetime
from app.schemas.communities import AuthorOut, CommunityRef
from app.services.friends import Relation


class ProfileOut(BaseModel):
    """Écrans 05 (soi-même) et 06 / 06b (quelqu'un d'autre)."""

    user: AuthorOut
    bio: str
    member_since: UtcDatetime
    relation: Relation
    # Date où l'amitié a été acceptée (« Ami depuis mars 2026 »).
    friends_since: UtcDatetime | None
    post_count: int
    community_count: int
    # Sorties où la personne a participé (organisées comprises) ; null si masquées (écran 05c).
    outing_count: int | None
    # null si le réglage « Qui peut voir ma liste d'amis » ne l'autorise pas.
    friend_count: int | None
    # Soi-même : ses communautés. Quelqu'un d'autre : les communautés en commun.
    communities: list[CommunityRef]
    # Posts « Amis uniquement » cachés au visiteur (« 9 publications réservées aux amis »).
    hidden_post_count: int
    # « + Ajouter en ami » possible (réglage « Qui peut m'envoyer une demande d'ami »).
    can_send_request: bool
    # Soi-même seulement : demandes reçues en attente et aperçu des amis (carte « Mes amis »).
    pending_request_count: int | None = None
    friends_preview: list[AuthorOut] | None = None


class RelationOut(BaseModel):
    relation: Relation


class FriendOut(BaseModel):
    user: AuthorOut
    since: UtcDatetime | None


class FriendRequestOut(BaseModel):
    user: AuthorOut
    created_at: UtcDatetime
    common_community_count: int


class FriendsOut(BaseModel):
    """Écran 05b."""

    friends: list[FriendOut]
    received: list[FriendRequestOut]
    sent: list[FriendRequestOut]


class SuggestionOut(BaseModel):
    user: AuthorOut
    # Une communauté partagée, pour la ligne « Écrins & Oisans · 4 amis en commun ».
    community: CommunityRef
    mutual_friend_count: int


class PrivacySettings(BaseModel):
    """Écran 05c."""

    default_post_visibility: Visibility
    friends_list_audience: Audience
    outings_audience: Audience
    friend_requests_from: RequestPolicy
    show_in_suggestions: bool


DISPLAY_NAME_MAX_LENGTH = 60
BIO_MAX_LENGTH = 300


class ProfileIn(BaseModel):
    """« Modifier le profil » (écran 05)."""

    display_name: str
    bio: str = ""

    @field_validator("display_name")
    @classmethod
    def check_display_name(cls, value: str) -> str:
        value = " ".join(value.split())
        if not 2 <= len(value) <= DISPLAY_NAME_MAX_LENGTH:
            raise ValueError(f"2 à {DISPLAY_NAME_MAX_LENGTH} caractères.")
        return value

    @field_validator("bio")
    @classmethod
    def check_bio(cls, value: str) -> str:
        value = value.strip()
        if len(value) > BIO_MAX_LENGTH:
            raise ValueError(f"{BIO_MAX_LENGTH} caractères max.")
        return value


class EditableProfile(BaseModel):
    display_name: str
    bio: str
