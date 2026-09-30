"""Outils de modération : journal, identifiants de communauté, signalements."""

import re
import unicodedata

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Community, ModerationLog, Post, Report, User, utcnow
from app.schemas.communities import AuthorOut, CommunityRef
from app.schemas.moderation import ReportedPost, ReportOut


def log(db: Session, actor: User | None, message: str) -> None:
    """Ajoute une ligne à l'« Activité récente » (validée avec le reste de la transaction)."""
    db.add(ModerationLog(actor_id=actor.id if actor else None, message=message[:255]))


def post_deleted_message(post: Post) -> str:
    """« Post supprimé dans « Vanoise » », ou « de @lucas » pour un post de profil."""
    where = f"dans « {post.community.name} »" if post.community else f"de @{post.author.username}"
    return f"Post supprimé {where}"


def slugify(name: str) -> str:
    """« Écrins & Oisans » → « ecrins-oisans »."""
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")[:70] or "communaute"


def unique_slug(db: Session, name: str) -> str:
    base = slugify(name)
    slug, suffix = base, 2
    while db.scalar(select(Community.id).where(Community.slug == slug)) is not None:
        slug, suffix = f"{base}-{suffix}", suffix + 1
    return slug


def open_report_counts(db: Session, user_ids: list[int]) -> dict[int, int]:
    if not user_ids:
        return {}
    rows = db.execute(
        select(Report.target_id, func.count())
        .where(Report.target_id.in_(user_ids), Report.resolved_at.is_(None))
        .group_by(Report.target_id)
    )
    return {target_id: count for target_id, count in rows}


def report_out(report: Report) -> ReportOut:
    post = report.post
    return ReportOut(
        id=report.id,
        reporter=AuthorOut.model_validate(report.reporter),
        target=AuthorOut.model_validate(report.target),
        post=(
            ReportedPost(
                id=post.id,
                body=post.body,
                visibility=post.visibility,
                community=CommunityRef.model_validate(post.community) if post.community else None,
            )
            if post
            else None
        ),
        reason=report.reason,
        comment=report.comment,
        created_at=report.created_at,
        resolved_at=report.resolved_at,
    )


def resolve(db: Session, moderator: User, reports: list[Report]) -> None:
    now = utcnow()
    for report in reports:
        report.resolved_at = now
        report.resolved_by_id = moderator.id
