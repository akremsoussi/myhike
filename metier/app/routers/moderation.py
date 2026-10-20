"""Écrans 13 à 16. Toutes les routes sont réservées aux modérateurs."""

import csv
import io
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Query, Response, status
from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db import DbSession
from app.deps import ModeratorUser
from app.errors import ApiError
from app.models import (
    AccountStatus,
    Community,
    CommunityMember,
    Massif,
    ModerationLog,
    Outing,
    OutingParticipant,
    Post,
    Refuge,
    Report,
    Role,
    Upload,
    User,
    UserSession,
    utcnow,
)
from app.schemas.communities import AuthorOut, CommunityRef
from app.schemas.media import UploadOut
from app.schemas.moderation import (
    AccountDetail,
    AccountFilter,
    AccountList,
    AccountRow,
    ActivityItem,
    CommunityIn,
    DashboardOut,
    ModCommunityDetail,
    ModCommunityRow,
    ReportedAccount,
    ReportOut,
    RoleIn,
    Stat,
    SummaryOut,
)
from app.schemas.refuges import MassifOut, RefugeSummary
from app.services import media, moderation

router = APIRouter(prefix="/moderation", tags=["moderation"])

ACTIVITY_SIZE = 8
REPORTED_PREVIEW = 5
ACCOUNTS_LIMIT = 100

ROLE_LABELS = {
    Role.USER: "Utilisateur",
    Role.MODERATOR: "Modérateur",
    Role.SUPER_ADMIN: "Super Admin",
}
_MOD_ROLES = (Role.MODERATOR, Role.SUPER_ADMIN)
STATUS_LABELS = {
    AccountStatus.PENDING_EMAIL: "En attente",
    AccountStatus.ACTIVE: "Actif",
    AccountStatus.SUSPENDED: "Suspendu",
}


def _count(db: Session, query: Select) -> int:
    return db.scalar(select(func.count()).select_from(query.subquery())) or 0


def _open_reports() -> Select:
    return select(Report).where(Report.resolved_at.is_(None))


# ---------- Tableau de bord (écran 13) ----------


@router.get("/summary")
def summary(db: DbSession, _: ModeratorUser) -> SummaryOut:
    return SummaryOut(open_reports=_count(db, _open_reports()))


def _weekend_bounds(now):
    """Samedi 0 h → lundi 0 h du week-end en cours, ou du prochain en semaine."""
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    weekday = today.weekday()  # lundi = 0 … samedi = 5, dimanche = 6
    saturday = today + timedelta(days=5 - weekday)  # négatif le dimanche : la veille
    return saturday, saturday + timedelta(days=2)


def _reported_accounts(db: Session, limit: int | None = None) -> list[ReportedAccount]:
    rows = db.scalars(
        _open_reports()
        .options(joinedload(Report.target), joinedload(Report.post).joinedload(Post.community))
        .order_by(Report.created_at.desc(), Report.id.desc())
    ).all()
    grouped: dict[int, ReportedAccount] = {}
    for report in rows:  # du plus récent au plus ancien
        entry = grouped.get(report.target_id)
        if entry is None:
            community = report.post.community if report.post else None
            grouped[report.target_id] = ReportedAccount(
                user=AuthorOut.model_validate(report.target),
                report_count=1,
                last_reason=report.reason,
                last_community=CommunityRef.model_validate(community) if community else None,
            )
        else:
            entry.report_count += 1
    accounts = list(grouped.values())
    return accounts[:limit] if limit else accounts


@router.get("/dashboard")
def dashboard(db: DbSession, _: ModeratorUser) -> DashboardOut:
    now = utcnow()
    week_ago, month_ago = now - timedelta(days=7), now - timedelta(days=30)
    weekend_start, weekend_end = _weekend_bounds(now)
    upcoming = select(Outing).where(Outing.starts_at >= now)

    logs = db.scalars(
        select(ModerationLog)
        .options(joinedload(ModerationLog.actor))
        .order_by(ModerationLog.created_at.desc(), ModerationLog.id.desc())
        .limit(ACTIVITY_SIZE)
    ).all()
    reports = db.scalars(
        select(Report)
        .options(joinedload(Report.target))
        .order_by(Report.created_at.desc(), Report.id.desc())
        .limit(ACTIVITY_SIZE)
    ).all()
    activity = [
        ActivityItem(
            message=entry.message,
            actor=AuthorOut.model_validate(entry.actor) if entry.actor else None,
            created_at=entry.created_at,
        )
        for entry in logs
    ] + [
        ActivityItem(
            message=f"Compte @{report.target.username} signalé",
            actor=None,
            created_at=report.created_at,
        )
        for report in reports
    ]
    activity.sort(key=lambda item: item.created_at, reverse=True)

    reported = _reported_accounts(db)
    return DashboardOut(
        users=Stat(
            value=_count(db, select(User.id)),
            recent=_count(db, select(User.id).where(User.created_at >= week_ago)),
        ),
        communities=Stat(
            value=_count(db, select(Community.id)),
            recent=_count(db, select(Community.id).where(Community.created_at >= month_ago)),
        ),
        active_outings=Stat(
            value=_count(db, upcoming),
            recent=_count(
                db,
                upcoming.where(Outing.starts_at >= weekend_start, Outing.starts_at < weekend_end),
            ),
        ),
        reported_accounts=len(reported),
        activity=activity[:ACTIVITY_SIZE],
        reported=reported[:REPORTED_PREVIEW],
    )


# ---------- Signalements ----------


@router.get("/reports")
def list_reports(db: DbSession, _: ModeratorUser) -> list[ReportOut]:
    """Signalements à traiter, du plus récent au plus ancien."""
    rows = db.scalars(
        _open_reports()
        .options(
            joinedload(Report.reporter),
            joinedload(Report.target),
            joinedload(Report.post).joinedload(Post.community),
            joinedload(Report.post).selectinload(Post.photos),
        )
        .order_by(Report.created_at.desc(), Report.id.desc())
    ).all()
    return [moderation.report_out(report) for report in rows]


@router.post("/reports/{report_id}/resolve", status_code=status.HTTP_204_NO_CONTENT)
def resolve_report(report_id: int, db: DbSession, moderator: ModeratorUser) -> None:
    """« Classer » : le signalement est traité (sans autre action)."""
    report = db.get(Report, report_id)
    if report is None:
        raise ApiError(404, "not_found", "Ce signalement n'existe pas.")
    if report.resolved_at is None:
        moderation.resolve(db, moderator, [report])
        moderation.log(db, moderator, f"Signalement de @{report.target.username} classé")
        db.commit()


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: DbSession, moderator: ModeratorUser) -> None:
    """Supprime un post signalé, quelle que soit sa visibilité, et classe ses signalements."""
    post = db.get(Post, post_id, options=[joinedload(Post.community)])
    if post is None:
        raise ApiError(404, "not_found", "Ce post n'existe pas.")
    reports = db.scalars(_open_reports().where(Report.post_id == post.id)).all()
    moderation.resolve(db, moderator, list(reports))
    moderation.log(db, moderator, moderation.post_deleted_message(post))
    db.delete(post)
    db.commit()


# ---------- Communautés (écrans 14 et 15) ----------


def _community_rows(db: Session, where=None) -> list[tuple[Community, int, int]]:
    members = (
        select(func.count())
        .where(CommunityMember.community_id == Community.id)
        .scalar_subquery()
    )
    posts = select(func.count()).where(Post.community_id == Community.id).scalar_subquery()
    query = select(Community, members, posts).options(joinedload(Community.massif))
    if where is not None:
        query = query.where(where)
    return [tuple(row) for row in db.execute(query.order_by(Community.name))]


def _row(community: Community, member_count: int, post_count: int) -> dict:
    return {
        "slug": community.slug,
        "name": community.name,
        "region": community.region,
        "massif": MassifOut.model_validate(community.massif) if community.massif else None,
        "member_count": member_count,
        "post_count": post_count,
        "created_at": community.created_at,
    }


def _detail(db: Session, slug: str) -> ModCommunityDetail:
    rows = _community_rows(db, Community.slug == slug)
    if not rows:
        raise ApiError(404, "not_found", "Cette communauté n'existe pas.")
    community, members, posts = rows[0]
    refuges = db.scalars(
        select(Refuge)
        .join(Community.refuges)
        .where(Community.id == community.id)
        .options(joinedload(Refuge.massif))
        .order_by(Refuge.name)
    ).all()
    return ModCommunityDetail(
        **_row(community, members, posts),
        description=community.description,
        refuges=[RefugeSummary.model_validate(refuge) for refuge in refuges],
        banner=UploadOut.model_validate(community.banner) if community.banner else None,
        icon=UploadOut.model_validate(community.icon) if community.icon else None,
    )


def _visual(
    db: Session, moderator: User, current: Upload | None, upload_id: int | None, field: str
) -> Upload | None:
    """Bannière ou icône : l'actuelle, ou une image tout juste envoyée par ce modérateur."""
    if upload_id is None:
        return None
    if current is not None and current.id == upload_id:
        return current
    return media.claim(db, moderator, [upload_id], field)[0]


def _apply(db: Session, moderator: User, community: Community, data: CommunityIn) -> None:
    if data.massif_id is not None and db.get(Massif, data.massif_id) is None:
        raise ApiError(422, "unknown_massif", "Ce massif n'existe pas.")
    refuges = list(db.scalars(select(Refuge).where(Refuge.id.in_(data.refuge_ids))))
    if len(refuges) != len(data.refuge_ids):
        raise ApiError(422, "unknown_refuge", "Un des refuges choisis n'existe pas.")
    community.name = data.name
    community.description = data.description
    community.region = data.region
    community.massif_id = data.massif_id
    community.refuges = sorted(refuges, key=lambda refuge: refuge.name)
    if data.banner_id is not None and data.banner_id == data.icon_id:
        raise ApiError(
            422, "validation_error", "Certains champs sont invalides.",
            fields={"icon_id": "Choisissez une autre image que la bannière."},
        )  # fmt: skip
    community.banner = _visual(db, moderator, community.banner, data.banner_id, "banner_id")
    community.icon = _visual(db, moderator, community.icon, data.icon_id, "icon_id")


@router.get("/communities")
def list_communities(db: DbSession, _: ModeratorUser) -> list[ModCommunityRow]:
    return [ModCommunityRow(**_row(*row)) for row in _community_rows(db)]


@router.get("/communities/{slug}")
def get_community(slug: str, db: DbSession, _: ModeratorUser) -> ModCommunityDetail:
    return _detail(db, slug)


@router.post("/communities", status_code=status.HTTP_201_CREATED)
def create_community(
    data: CommunityIn, db: DbSession, moderator: ModeratorUser
) -> ModCommunityDetail:
    community = Community(slug=moderation.unique_slug(db, data.name))
    _apply(db, moderator, community, data)
    db.add(community)
    moderation.log(db, moderator, f"Communauté « {community.name} » créée")
    db.commit()
    return _detail(db, community.slug)


@router.put("/communities/{slug}")
def update_community(
    slug: str, data: CommunityIn, db: DbSession, moderator: ModeratorUser
) -> ModCommunityDetail:
    """Le slug (adresse de la page) ne change pas quand on renomme la communauté."""
    community = db.scalar(select(Community).where(Community.slug == slug))
    if community is None:
        raise ApiError(404, "not_found", "Cette communauté n'existe pas.")
    _apply(db, moderator, community, data)
    moderation.log(db, moderator, f"Communauté « {community.name} » modifiée")
    db.commit()
    return _detail(db, slug)


@router.delete("/communities/{slug}", status_code=status.HTTP_204_NO_CONTENT)
def delete_community(slug: str, db: DbSession, moderator: ModeratorUser) -> None:
    """Zone de danger : supprime la communauté, ses posts et ses inscriptions."""
    community = db.scalar(select(Community).where(Community.slug == slug))
    if community is None:
        raise ApiError(404, "not_found", "Cette communauté n'existe pas.")
    moderation.log(db, moderator, f"Communauté « {community.name} » supprimée")
    db.delete(community)
    db.commit()


# ---------- Comptes (écran 16) ----------


def _account_query(q: str | None, filter_: AccountFilter) -> Select:
    query = select(User)
    if q:
        pattern = f"%{q.strip()}%"
        query = query.where(
            or_(
                User.display_name.like(pattern),
                User.username.like(pattern),
                User.email.like(pattern),
            )
        )
    if filter_ == "moderators":
        query = query.where(User.role.in_(_MOD_ROLES))
    elif filter_ == "suspended":
        query = query.where(User.status == AccountStatus.SUSPENDED)
    elif filter_ == "reported":
        reported = select(Report.target_id).where(Report.resolved_at.is_(None))
        query = query.where(User.id.in_(reported))
    return query


def _account_rows(db: Session, users: list[User]) -> list[AccountRow]:
    counts = moderation.open_report_counts(db, [user.id for user in users])
    return [
        AccountRow(
            id=user.id,
            username=user.username,
            display_name=user.display_name,
            email=user.email,
            role=user.role,
            status=user.status,
            created_at=user.created_at,
            open_report_count=counts.get(user.id, 0),
        )
        for user in users
    ]


def _get_account(db: Session, username: str) -> User:
    user = db.scalar(select(User).where(User.username == username))
    if user is None:
        raise ApiError(404, "not_found", "Ce compte n'existe pas.")
    return user


def _not_self(moderator: User, user: User, message: str) -> None:
    if moderator.id == user.id:
        raise ApiError(409, "self_action", message)


def _check_hierarchy(moderator: User, target: User, message: str) -> None:
    if target.role == Role.SUPER_ADMIN:
        raise ApiError(
            403, "forbidden", "Impossible de modifier ou sanctionner un Super Administrateur."
        )
    if moderator.role != Role.SUPER_ADMIN and target.role in _MOD_ROLES:
        raise ApiError(403, "forbidden", message)


@router.get("/users")
def list_accounts(
    db: DbSession,
    _: ModeratorUser,
    q: Annotated[str | None, Query(max_length=100)] = None,
    filter: AccountFilter = "all",  # noqa: A002 - nom du paramètre de l'URL
) -> AccountList:
    query = _account_query(q, filter)
    users = db.scalars(query.order_by(User.created_at, User.id).limit(ACCOUNTS_LIMIT)).all()
    return AccountList(
        total=_count(db, query),
        moderator_count=_count(db, select(User.id).where(User.role.in_(_MOD_ROLES))),
        items=_account_rows(db, list(users)),
    )


@router.get("/users/export")
def export_accounts(db: DbSession, moderator: ModeratorUser) -> Response:
    """« Exporter (CSV) » : tous les comptes, séparateur « ; » pour Excel en français."""
    users = list(db.scalars(select(User).order_by(User.created_at, User.id)))
    counts = moderation.open_report_counts(db, [user.id for user in users])
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=";")
    writer.writerow(["Pseudo", "Nom", "Email", "Rôle", "Statut", "Inscrit le", "Signalements"])
    for user in users:
        writer.writerow(
            [
                user.username,
                user.display_name,
                user.email,
                ROLE_LABELS[user.role],
                STATUS_LABELS[user.status],
                user.created_at.strftime("%d/%m/%Y"),
                counts.get(user.id, 0),
            ]
        )
    moderation.log(db, moderator, "Export CSV des comptes")
    db.commit()
    # BOM : Excel reconnaît l'UTF-8 (accents).
    return Response(
        content="﻿" + buffer.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="comptes-refuges.csv"'},
    )


@router.get("/users/{username}")
def get_account(username: str, db: DbSession, _: ModeratorUser) -> AccountDetail:
    user = _get_account(db, username)
    reports = db.scalars(
        _open_reports()
        .where(Report.target_id == user.id)
        .options(
            selectinload(Report.reporter),
            selectinload(Report.target),
            selectinload(Report.post).selectinload(Post.community),
        )
        .order_by(Report.created_at.desc(), Report.id.desc())
    ).all()
    return AccountDetail(
        **_account_rows(db, [user])[0].model_dump(),
        community_count=_count(
            db, select(CommunityMember.community_id).where(CommunityMember.user_id == user.id)
        ),
        post_count=_count(db, select(Post.id).where(Post.author_id == user.id)),
        outing_count=_count(
            db, select(OutingParticipant.outing_id).where(OutingParticipant.user_id == user.id)
        ),
        reports=[moderation.report_out(report) for report in reports],
    )


@router.put("/users/{username}/role")
def set_role(username: str, data: RoleIn, db: DbSession, moderator: ModeratorUser) -> AccountDetail:
    """« Promouvoir modérateur » / « Retirer le rôle de modérateur » (réservé au Super Admin)."""
    user = _get_account(db, username)
    _not_self(moderator, user, "Vous ne pouvez pas changer votre propre rôle.")
    if moderator.role != Role.SUPER_ADMIN:
        raise ApiError(
            403, "forbidden", "Seul le Super Administrateur peut modifier le rôle d'un compte."
        )
    if user.role == Role.SUPER_ADMIN or data.role == Role.SUPER_ADMIN:
        raise ApiError(
            403, "forbidden", "Le rôle de Super Administrateur ne peut pas être attribué ou retiré."
        )
    if user.role != data.role:
        user.role = data.role
        verb = "promu modérateur" if data.role == Role.MODERATOR else "n'est plus modérateur"
        moderation.log(db, moderator, f"{user.display_name} {verb}")
        db.commit()
    return get_account(username, db, moderator)


@router.post("/users/{username}/suspend")
def suspend(username: str, db: DbSession, moderator: ModeratorUser) -> AccountDetail:
    """Suspendre : connexion impossible et sessions en cours refusées (voir deps)."""
    user = _get_account(db, username)
    _not_self(moderator, user, "Vous ne pouvez pas suspendre votre propre compte.")
    _check_hierarchy(
        moderator,
        user,
        "Un administrateur classique ne peut pas suspendre un autre administrateur.",
    )
    if user.status != AccountStatus.SUSPENDED:
        user.status = AccountStatus.SUSPENDED
        user.suspended_at = utcnow()
        # Les sessions sont aussi révoquées : rien ne reste ouvert si le compte est réactivé.
        for session in db.scalars(
            select(UserSession).where(
                UserSession.user_id == user.id, UserSession.revoked_at.is_(None)
            )
        ):
            session.revoked_at = utcnow()
        moderation.log(db, moderator, f"Compte @{user.username} suspendu")
        db.commit()
    return get_account(username, db, moderator)


@router.post("/users/{username}/reactivate")
def reactivate(username: str, db: DbSession, moderator: ModeratorUser) -> AccountDetail:
    """Lève la suspension ; un compte jamais confirmé redevient « en attente »."""
    user = _get_account(db, username)
    _check_hierarchy(
        moderator,
        user,
        "Un administrateur classique ne peut pas réactiver un autre administrateur.",
    )
    if user.status == AccountStatus.SUSPENDED:
        user.status = (
            AccountStatus.ACTIVE if user.email_verified_at else AccountStatus.PENDING_EMAIL
        )
        user.suspended_at = None
        moderation.log(db, moderator, f"Compte @{user.username} réactivé")
        db.commit()
    return get_account(username, db, moderator)


@router.post("/users/{username}/reports/resolve")
def resolve_account_reports(
    username: str, db: DbSession, moderator: ModeratorUser
) -> AccountDetail:
    """Classe tous les signalements ouverts d'un compte."""
    user = _get_account(db, username)
    reports = list(db.scalars(_open_reports().where(Report.target_id == user.id)))
    if reports:
        moderation.resolve(db, moderator, reports)
        moderation.log(db, moderator, f"Signalements de @{user.username} classés")
        db.commit()
    return get_account(username, db, moderator)


@router.delete("/users/{username}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(username: str, db: DbSession, moderator: ModeratorUser) -> None:
    """Supprime le compte et tout ce qui lui appartient (posts, sorties organisées…)."""
    user = _get_account(db, username)
    _not_self(moderator, user, "Vous ne pouvez pas supprimer votre propre compte.")
    _check_hierarchy(
        moderator,
        user,
        "Un administrateur classique ne peut pas supprimer un autre administrateur.",
    )
    moderation.log(db, moderator, f"Compte @{user.username} supprimé")
    db.delete(user)
    db.commit()
