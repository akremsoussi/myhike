from typing import Literal

from pydantic import BaseModel, field_validator

from app.models import AccountStatus, ReportReason, Role, Visibility
from app.schemas.auth import UtcDatetime
from app.schemas.communities import AuthorOut, CommunityRef
from app.schemas.refuges import MassifOut, RefugeSummary

COMMENT_MAX_LENGTH = 500


# ---------- Signalements ----------


class ReportIn(BaseModel):
    """Signaler un post (`post_id`) ou un compte (`username`)."""

    post_id: int | None = None
    username: str | None = None
    reason: ReportReason
    comment: str = ""

    @field_validator("comment")
    @classmethod
    def check_comment(cls, value: str) -> str:
        return value.strip()[:COMMENT_MAX_LENGTH]


class ReportedPost(BaseModel):
    """Post signalé, montré aux modérateurs même s'il est « Amis uniquement »."""

    id: int
    body: str
    visibility: Visibility
    community: CommunityRef | None


class ReportOut(BaseModel):
    id: int
    reporter: AuthorOut
    target: AuthorOut
    post: ReportedPost | None
    reason: ReportReason
    comment: str
    created_at: UtcDatetime
    resolved_at: UtcDatetime | None


class ReportedAccount(BaseModel):
    """Ligne « Signalements à traiter » (écran 13) : un compte et ses signalements ouverts."""

    user: AuthorOut
    report_count: int
    # Motif et communauté du dernier signalement (« Spam dans « Vanoise » »).
    last_reason: ReportReason
    last_community: CommunityRef | None


# ---------- Tableau de bord ----------


class Stat(BaseModel):
    value: int
    # Évolution récente : nouveaux cette semaine, ce mois-ci, ce week-end.
    recent: int


class ActivityItem(BaseModel):
    message: str
    # Modérateur à l'origine de l'action, absent pour un signalement ou une inscription.
    actor: AuthorOut | None
    created_at: UtcDatetime


class DashboardOut(BaseModel):
    """Écran 13."""

    users: Stat  # recent : inscrits cette semaine
    communities: Stat  # recent : créées ce mois-ci
    active_outings: Stat  # sorties à venir ; recent : ce week-end
    reported_accounts: int
    activity: list[ActivityItem]
    reported: list[ReportedAccount]


class SummaryOut(BaseModel):
    """Compteur rouge de la barre latérale."""

    open_reports: int


# ---------- Communautés ----------


class ModCommunityRow(BaseModel):
    """Ligne du tableau de l'écran 14."""

    slug: str
    name: str
    region: str
    massif: MassifOut | None
    member_count: int
    post_count: int
    created_at: UtcDatetime


class ModCommunityDetail(ModCommunityRow):
    """Formulaire de l'écran 15."""

    description: str
    refuges: list[RefugeSummary]


class CommunityIn(BaseModel):
    name: str
    description: str = ""
    region: str
    massif_id: int | None = None
    refuge_ids: list[int] = []

    @field_validator("name")
    @classmethod
    def check_name(cls, value: str) -> str:
        value = value.strip()
        if not 3 <= len(value) <= 80:
            raise ValueError("3 à 80 caractères.")
        return value

    @field_validator("region")
    @classmethod
    def check_region(cls, value: str) -> str:
        value = value.strip()
        if not 2 <= len(value) <= 40:
            raise ValueError("Choisissez une région.")
        return value

    @field_validator("description")
    @classmethod
    def check_description(cls, value: str) -> str:
        value = value.strip()
        if len(value) > 2000:
            raise ValueError("2 000 caractères max.")
        return value

    @field_validator("refuge_ids")
    @classmethod
    def check_refuges(cls, value: list[int]) -> list[int]:
        if len(value) > 30:
            raise ValueError("30 refuges au plus.")
        return list(dict.fromkeys(value))  # sans doublons, dans l'ordre


# ---------- Comptes ----------

AccountFilter = Literal["all", "moderators", "reported", "suspended"]


class AccountRow(BaseModel):
    """Ligne du tableau de l'écran 16."""

    id: int
    username: str
    display_name: str
    email: str
    role: Role
    status: AccountStatus
    created_at: UtcDatetime
    open_report_count: int


class AccountList(BaseModel):
    total: int
    moderator_count: int
    items: list[AccountRow]


class AccountDetail(AccountRow):
    """Panneau de détail de l'écran 16."""

    community_count: int
    post_count: int
    outing_count: int
    reports: list[ReportOut]


class RoleIn(BaseModel):
    role: Role
