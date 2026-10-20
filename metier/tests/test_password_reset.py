"""Mot de passe oublié : lien par email, nouveau mot de passe, sessions fermées."""

from datetime import timedelta

import pytest
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config import settings
from app.models import AccountStatus, EmailToken, TokenPurpose, User

EMAIL = "randonneur@mail.fr"
NEW_PASSWORD = "nouveaumotdepasse"


@pytest.fixture
def reset_outbox(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, str]]:
    sent: list[dict[str, str]] = []

    def fake_send(to: str, display_name: str, token: str) -> None:
        sent.append({"to": to, "token": token})

    monkeypatch.setattr("app.routers.auth.send_password_reset_email", fake_send)
    return sent


def age_resets(db: Session, **delta) -> None:
    shift = timedelta(**delta)
    for token in db.scalars(select(EmailToken).where(EmailToken.purpose == TokenPurpose.RESET)):
        token.created_at -= shift
        token.expires_at -= shift
    db.commit()


def request_reset(client, email: str = EMAIL):
    return client.post("/api/auth/password-reset", json={"email": email})


def confirm(client, token: str, password: str = NEW_PASSWORD):
    return client.post(
        "/api/auth/password-reset/confirm", json={"token": token, "password": password}
    )


def login(client, password: str):
    return client.post("/api/auth/login", json={"email": EMAIL, "password": password})


def test_reset_sends_link_and_changes_password(active_client, reset_outbox):
    response = request_reset(active_client, "  Randonneur@Mail.fr ")

    assert response.status_code == 202
    assert [mail["to"] for mail in reset_outbox] == [EMAIL]
    assert confirm(active_client, reset_outbox[0]["token"]).status_code == 204
    assert login(active_client, "motdepasse8").status_code == 401
    assert login(active_client, NEW_PASSWORD).status_code == 200


def test_unknown_address_gets_same_answer(client, reset_outbox):
    response = request_reset(client, "personne@mail.fr")

    assert response.status_code == 202
    assert reset_outbox == []


def test_reset_closes_every_session(active_client, reset_outbox):
    request_reset(active_client)
    confirm(active_client, reset_outbox[0]["token"])

    assert active_client.get("/api/auth/me").status_code == 401


def test_reset_link_works_once(active_client, reset_outbox):
    request_reset(active_client)
    token = reset_outbox[0]["token"]
    confirm(active_client, token)

    response = confirm(active_client, token, "encoreunautre")

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "invalid_token"


def test_reset_link_expires(active_client, db, reset_outbox):
    request_reset(active_client)
    age_resets(db, minutes=settings.password_reset_minutes, seconds=1)

    response = confirm(active_client, reset_outbox[0]["token"])

    assert response.status_code == 410
    assert login(active_client, "motdepasse8").status_code == 200


def test_new_request_is_limited_and_replaces_old_link(active_client, db, reset_outbox):
    request_reset(active_client)
    request_reset(active_client)
    assert len(reset_outbox) == 1

    age_resets(db, seconds=settings.resend_cooldown_seconds)
    request_reset(active_client)

    assert len(reset_outbox) == 2
    assert confirm(active_client, reset_outbox[0]["token"]).status_code == 400
    assert confirm(active_client, reset_outbox[1]["token"]).status_code == 204


def test_reset_validates_password(active_client, reset_outbox):
    request_reset(active_client)

    response = confirm(active_client, reset_outbox[0]["token"], "court")

    assert response.status_code == 422
    assert "password" in response.json()["detail"]["fields"]


def test_reset_confirms_pending_address(client, db, reset_outbox):
    client.post(
        "/api/auth/register",
        json={"username": "camille", "email": "camille@mail.fr", "password": "motdepasse8",
              "accept_terms": True},
    )  # fmt: skip
    request_reset(client, "camille@mail.fr")
    confirm(client, reset_outbox[0]["token"])

    user = db.scalars(select(User).where(User.username == "camille")).one()
    db.refresh(user)
    assert user.status == AccountStatus.ACTIVE


def test_suspended_account_gets_no_link(active_client, db, reset_outbox):
    db.execute(update(User).values(status=AccountStatus.SUSPENDED))
    db.commit()

    assert request_reset(active_client).status_code == 202
    assert reset_outbox == []
