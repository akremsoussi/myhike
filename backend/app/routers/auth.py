from fastapi import APIRouter, BackgroundTasks, Response, status

from app.config import settings
from app.db import DbSession
from app.deps import SESSION_COOKIE, CurrentUser, SessionToken
from app.models import User
from app.schemas.auth import (
    ChangeEmailIn,
    LoginIn,
    MeOut,
    RegisterIn,
    UserOut,
    VerifyEmailIn,
    VerifyEmailOut,
)
from app.services import accounts
from app.services.email import send_verification_email

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=settings.session_days * 24 * 3600,
        httponly=True,  # inaccessible au JavaScript
        samesite="lax",  # pas envoyé par les requêtes POST d'un autre site
        secure=settings.cookie_secure,
        path="/",
    )


def _me(db: DbSession, user: User) -> MeOut:
    verification = accounts.verification_info(db, user)
    return MeOut(user=UserOut.model_validate(user), verification=verification)


def _send_verification(tasks: BackgroundTasks, user: User, token: str) -> None:
    tasks.add_task(send_verification_email, user.email, user.display_name, token)


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: RegisterIn, db: DbSession, response: Response, tasks: BackgroundTasks) -> MeOut:
    """Crée un compte en attente de confirmation et connecte l'utilisateur (écran 02b)."""
    user, token = accounts.register(db, data)
    _send_verification(tasks, user, token)
    _set_session_cookie(response, accounts.create_session(db, user))
    return _me(db, user)


@router.post("/login")
def login(data: LoginIn, db: DbSession, response: Response) -> MeOut:
    """Connexion. Un compte non confirmé est connecté mais n'a accès qu'à l'écran 02b."""
    user = accounts.authenticate(db, data.email, data.password)
    _set_session_cookie(response, accounts.create_session(db, user))
    return _me(db, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(db: DbSession, response: Response, token: SessionToken = None) -> None:
    if token:
        accounts.revoke_session(db, token)
    response.delete_cookie(SESSION_COOKIE, path="/")


@router.get("/me")
def me(user: CurrentUser, db: DbSession) -> MeOut:
    return _me(db, user)


@router.post("/verify-email")
def verify_email(data: VerifyEmailIn, db: DbSession) -> VerifyEmailOut:
    """Lien reçu par email. Ne demande pas d'être connecté : le lien peut s'ouvrir ailleurs."""
    user = accounts.verify_email(db, data.token)
    return VerifyEmailOut(status=user.status)


@router.post("/resend-verification", status_code=status.HTTP_202_ACCEPTED)
def resend_verification(user: CurrentUser, db: DbSession, tasks: BackgroundTasks) -> MeOut:
    token = accounts.resend_verification(db, user)
    _send_verification(tasks, user, token)
    return _me(db, user)


@router.patch("/pending-email")
def change_pending_email(
    data: ChangeEmailIn, user: CurrentUser, db: DbSession, tasks: BackgroundTasks
) -> MeOut:
    token = accounts.change_pending_email(db, user, data.email)
    _send_verification(tasks, user, token)
    return _me(db, user)
