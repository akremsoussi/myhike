"""Modèles SQLAlchemy. Tous importés ici pour qu'Alembic les voie."""

from app.models.base import Base, utcnow
from app.models.media import Upload
from app.models.moderation import ModerationLog, Report, ReportReason
from app.models.outing import (
    Outing,
    OutingInvitation,
    OutingParticipant,
    OutingStop,
    OutingVisibility,
)
from app.models.refuge import GUARDED_KINDS, Massif, Refuge, RefugeKind, RefugePhoto
from app.models.social import (
    Community,
    CommunityMember,
    Friendship,
    FriendshipStatus,
    Post,
    PostLike,
    community_refuges,
)
from app.models.user import (
    AccountStatus,
    Audience,
    EmailToken,
    RequestPolicy,
    Role,
    TokenPurpose,
    User,
    UserSession,
    Visibility,
)

__all__ = [
    "AccountStatus",
    "Audience",
    "Base",
    "Community",
    "CommunityMember",
    "EmailToken",
    "Friendship",
    "FriendshipStatus",
    "GUARDED_KINDS",
    "Massif",
    "ModerationLog",
    "Outing",
    "OutingInvitation",
    "OutingParticipant",
    "OutingStop",
    "OutingVisibility",
    "Post",
    "PostLike",
    "Refuge",
    "RefugeKind",
    "RefugePhoto",
    "Report",
    "ReportReason",
    "RequestPolicy",
    "Role",
    "Visibility",
    "community_refuges",
    "TokenPurpose",
    "Upload",
    "User",
    "UserSession",
    "utcnow",
]
