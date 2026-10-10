import re
from datetime import UTC, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, PlainSerializer, field_validator

from app.models import AccountStatus, Role

USERNAME_RE = re.compile(r"^[a-z0-9_]{3,30}$")
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128

# Les dates sont stockées en UTC sans fuseau : on l'ajoute à la sortie pour que le
# navigateur les convertisse correctement en heure locale.
UtcDatetime = Annotated[
    datetime, PlainSerializer(lambda value: value.replace(tzinfo=UTC).isoformat())
]


def _normalize_email(value: str) -> str:
    return value.strip().lower()


def _check_password(value: str) -> str:
    if not PASSWORD_MIN_LENGTH <= len(value) <= PASSWORD_MAX_LENGTH:
        raise ValueError(f"{PASSWORD_MIN_LENGTH} caractères min.")
    return value


class RegisterIn(BaseModel):
    username: str
    email: EmailStr
    password: str
    accept_terms: bool

    @field_validator("username")
    @classmethod
    def check_username(cls, value: str) -> str:
        value = value.strip().lower()
        if not USERNAME_RE.match(value):
            raise ValueError("3 à 30 caractères : lettres minuscules, chiffres ou « _ ».")
        return value

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return _normalize_email(value)

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str) -> str:
        return _check_password(value)

    @field_validator("accept_terms")
    @classmethod
    def check_terms(cls, value: bool) -> bool:
        if not value:
            raise ValueError("Vous devez accepter les conditions d'utilisation.")
        return value


class LoginIn(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return _normalize_email(value)


class VerifyEmailIn(BaseModel):
    token: str


class ChangeEmailIn(BaseModel):
    email: EmailStr

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return _normalize_email(value)


class PasswordResetRequestIn(BaseModel):
    email: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return _normalize_email(value)


class PasswordResetIn(BaseModel):
    token: str
    password: str

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str) -> str:
        return _check_password(value)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    display_name: str
    email: str
    role: Role
    status: AccountStatus
    created_at: UtcDatetime


class VerificationOut(BaseModel):
    """État du lien de confirmation, pour l'écran 02b."""

    email: str
    sent_at: UtcDatetime
    expires_at: UtcDatetime
    resend_available_at: UtcDatetime


class MeOut(BaseModel):
    user: UserOut
    verification: VerificationOut | None = None


class VerifyEmailOut(BaseModel):
    status: AccountStatus
