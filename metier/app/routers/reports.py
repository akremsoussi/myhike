from fastapi import APIRouter, status
from sqlalchemy import select

from app.db import DbSession
from app.deps import ActiveUser
from app.errors import ApiError
from app.models import Post, Report
from app.routers.users import get_user
from app.schemas.moderation import ReportIn
from app.services.visibility import post_visible_to

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", status_code=status.HTTP_204_NO_CONTENT)
def create_report(data: ReportIn, db: DbSession, viewer: ActiveUser) -> None:
    """« Signaler » un post ou un compte. Un doublon encore ouvert n'est pas recréé."""
    post = None
    if data.post_id is not None:
        # On ne signale que ce qu'on peut lire.
        post = db.scalar(select(Post).where(Post.id == data.post_id, post_visible_to(viewer)))
        if post is None:
            raise ApiError(404, "not_found", "Ce post n'existe pas.")
        target_id = post.author_id
    elif data.username is not None:
        target_id = get_user(db, data.username).id
    else:
        raise ApiError(422, "validation_error", "Indiquez un post ou un compte.")
    if target_id == viewer.id:
        raise ApiError(422, "invalid_report", "Vous ne pouvez pas vous signaler vous-même.")

    same_post = Report.post_id == post.id if post else Report.post_id.is_(None)
    duplicate = db.scalar(
        select(Report.id).where(
            Report.reporter_id == viewer.id,
            Report.target_id == target_id,
            same_post,
            Report.resolved_at.is_(None),
        )
    )
    if duplicate is None:
        db.add(
            Report(
                reporter_id=viewer.id,
                target_id=target_id,
                post_id=post.id if post else None,
                reason=data.reason,
                comment=data.comment,
            )
        )
        db.commit()
