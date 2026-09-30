"""Statuts de compte : pending_email → active, suspended, et ce que chacun permet."""

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config import settings
from app.deps import SESSION_COOKIE
from app.models import AccountStatus, EmailToken, Role, User, utcnow

PASSWORD = "motdepasse8"


def register(client: TestClient, username: str = "camille", email: str = "camille@mail.fr"):
    return client.post(
        "/api/auth/register",
        json={"username": username, "email": email, "password": PASSWORD, "accept_terms": True},
    )


def login(client: TestClient, email: str = "camille@mail.fr", password: str = PASSWORD):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def set_user(db: Session, username: str, **values) -> None:
    db.execute(update(User).where(User.username == username).values(**values))
    db.commit()


def age_tokens(db: Session, **delta) -> None:
    """Fait vieillir les liens de confirmation, pour tester le délai et l'expiration."""
    shift = timedelta(**delta)
    for token in db.scalars(select(EmailToken)):
        token.created_at -= shift
        token.expires_at -= shift
    db.commit()


# ---------- Inscription ----------


def test_register_creates_pending_account_and_sends_link(client, db, outbox):
    response = register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["user"]["status"] == "pending_email"
    assert body["user"]["role"] == "user"
    assert body["verification"]["email"] == "camille@mail.fr"
    assert len(outbox) == 1 and outbox[0]["to"] == "camille@mail.fr"
    # L'utilisateur est connecté, pour afficher l'écran 02b.
    assert SESSION_COOKIE in client.cookies

    user = db.scalar(select(User).where(User.username == "camille"))
    assert user.password_hash != PASSWORD and user.password_hash.startswith("$argon2")
    stored = db.scalar(select(EmailToken))
    assert stored.token_hash != outbox[0]["token"]  # seule l'empreinte est stockée


def test_register_normalizes_username_and_email(client):
    response = register(client, username="  Camille_M ", email=" Camille@Mail.FR ")

    assert response.status_code == 201
    assert response.json()["user"]["username"] == "camille_m"
    assert response.json()["user"]["email"] == "camille@mail.fr"


def test_register_rejects_duplicates_per_field(client):
    register(client)
    client.cookies.clear()

    response = register(client, username="camille", email="CAMILLE@mail.fr")

    assert response.status_code == 409
    assert set(response.json()["detail"]["fields"]) == {"username", "email"}


@pytest.mark.parametrize(
    ("field", "value"),
    [("password", "court"), ("username", "a"), ("username", "é!"), ("accept_terms", False)],
)
def test_register_validates_fields(client, field, value):
    payload = {
        "username": "camille",
        "email": "camille@mail.fr",
        "password": PASSWORD,
        "accept_terms": True,
    }
    payload[field] = value

    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 422
    assert field in response.json()["detail"]["fields"]


# ---------- pending_email ----------


def test_pending_account_sees_me_but_not_the_site(client):
    register(client)

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["user"]["status"] == "pending_email"

    blocked = client.get("/api/_test/active")
    assert blocked.status_code == 403
    assert blocked.json()["detail"]["code"] == "account_pending"


def test_pending_account_can_log_in(client):
    register(client)
    client.cookies.clear()

    response = login(client)

    assert response.status_code == 200
    assert response.json()["user"]["status"] == "pending_email"
    assert response.json()["verification"] is not None


def test_verification_link_activates_account(client, db, outbox):
    register(client)

    response = client.post("/api/auth/verify-email", json={"token": outbox[0]["token"]})

    assert response.status_code == 200
    assert response.json()["status"] == "active"
    me = client.get("/api/auth/me").json()
    assert me["user"]["status"] == "active"
    assert me["verification"] is None
    assert client.get("/api/_test/active").status_code == 200
    assert db.scalar(select(User.email_verified_at)) is not None


def test_verification_link_works_without_session(client, outbox):
    register(client)
    client.cookies.clear()  # lien ouvert dans un autre navigateur

    response = client.post("/api/auth/verify-email", json={"token": outbox[0]["token"]})

    assert response.json()["status"] == "active"


def test_verification_link_clicked_twice_is_not_an_error(client, outbox):
    register(client)
    token = outbox[0]["token"]

    client.post("/api/auth/verify-email", json={"token": token})
    response = client.post("/api/auth/verify-email", json={"token": token})

    assert response.status_code == 200
    assert response.json()["status"] == "active"


def test_unknown_verification_link_is_rejected(client):
    register(client)

    response = client.post("/api/auth/verify-email", json={"token": "inconnu"})

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "invalid_token"


def test_expired_verification_link_keeps_account_pending(client, db, outbox):
    register(client)
    age_tokens(db, hours=settings.verification_hours, seconds=1)

    response = client.post("/api/auth/verify-email", json={"token": outbox[0]["token"]})

    assert response.status_code == 410
    assert response.json()["detail"]["code"] == "token_expired"
    assert client.get("/api/auth/me").json()["user"]["status"] == "pending_email"


# ---------- Renvoi et changement d'adresse ----------


def test_resend_is_limited_in_time(client, outbox):
    register(client)

    response = client.post("/api/auth/resend-verification")

    assert response.status_code == 429
    detail = response.json()["detail"]
    assert detail["code"] == "resend_too_soon"
    assert 0 < detail["retry_after"] <= settings.resend_cooldown_seconds
    assert len(outbox) == 1


def test_resend_after_delay_replaces_previous_link(client, db, outbox):
    register(client)
    age_tokens(db, seconds=settings.resend_cooldown_seconds)

    response = client.post("/api/auth/resend-verification")

    assert response.status_code == 202
    assert len(outbox) == 2
    old = client.post("/api/auth/verify-email", json={"token": outbox[0]["token"]})
    assert old.status_code == 400
    new = client.post("/api/auth/verify-email", json={"token": outbox[1]["token"]})
    assert new.json()["status"] == "active"


def test_change_pending_email_sends_new_link(client, outbox):
    register(client)

    response = client.patch("/api/auth/pending-email", json={"email": "camille@autre.fr"})

    assert response.status_code == 200
    assert response.json()["user"]["email"] == "camille@autre.fr"
    assert outbox[-1]["to"] == "camille@autre.fr"
    # Le lien envoyé à l'ancienne adresse ne fonctionne plus.
    old = client.post("/api/auth/verify-email", json={"token": outbox[0]["token"]})
    assert old.status_code == 400


def test_change_pending_email_rejects_taken_address(client):
    register(client, username="lucas", email="lucas@mail.fr")
    client.cookies.clear()
    register(client)

    response = client.patch("/api/auth/pending-email", json={"email": "lucas@mail.fr"})

    assert response.status_code == 409
    assert "email" in response.json()["detail"]["fields"]


def test_active_account_cannot_resend_or_change_pending_email(client, outbox):
    register(client)
    client.post("/api/auth/verify-email", json={"token": outbox[0]["token"]})

    resend = client.post("/api/auth/resend-verification")
    change = client.patch("/api/auth/pending-email", json={"email": "camille@autre.fr"})

    assert resend.status_code == 409 and resend.json()["detail"]["code"] == "already_verified"
    assert change.status_code == 409 and change.json()["detail"]["code"] == "already_verified"


# ---------- Connexion ----------


@pytest.mark.parametrize(
    ("email", "password"), [("camille@mail.fr", "mauvais-mdp"), ("inconnu@mail.fr", PASSWORD)]
)
def test_login_failure_does_not_say_which_field_is_wrong(client, email, password):
    register(client)
    client.cookies.clear()

    response = login(client, email=email, password=password)

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "invalid_credentials"
    assert SESSION_COOKIE not in client.cookies


def test_login_is_case_insensitive_on_email(client):
    register(client)
    client.cookies.clear()

    assert login(client, email="  CAMILLE@mail.fr").status_code == 200


def test_logout_revokes_session(client):
    register(client)
    token = client.cookies[SESSION_COOKIE]

    assert client.post("/api/auth/logout").status_code == 204

    client.cookies.set(SESSION_COOKIE, token)  # rejouer l'ancien cookie ne suffit pas
    assert client.get("/api/auth/me").status_code == 401


def test_anonymous_visitor_is_not_authenticated(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "not_authenticated"


# ---------- suspended ----------


def test_suspended_account_cannot_log_in(client, db):
    register(client)
    client.cookies.clear()
    set_user(db, "camille", status=AccountStatus.SUSPENDED, suspended_at=utcnow())

    response = login(client)

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "account_suspended"
    assert SESSION_COOKIE not in client.cookies


def test_suspension_cuts_existing_sessions(client, db, outbox):
    register(client)
    client.post("/api/auth/verify-email", json={"token": outbox[0]["token"]})
    set_user(db, "camille", status=AccountStatus.SUSPENDED, suspended_at=utcnow())

    assert client.get("/api/auth/me").status_code == 403
    assert client.get("/api/_test/active").status_code == 403


def test_suspended_account_stays_suspended_after_verification(client, db, outbox):
    register(client)
    set_user(db, "camille", status=AccountStatus.SUSPENDED)

    response = client.post("/api/auth/verify-email", json={"token": outbox[0]["token"]})

    assert response.json()["status"] == "suspended"


# ---------- Rôles ----------


def test_moderation_requires_moderator_role(client, db, outbox):
    register(client)
    client.post("/api/auth/verify-email", json={"token": outbox[0]["token"]})

    assert client.get("/api/_test/moderator").status_code == 403

    set_user(db, "camille", role=Role.MODERATOR)
    assert client.get("/api/_test/moderator").status_code == 200


def test_pending_moderator_is_still_blocked(client, db):
    register(client)
    set_user(db, "camille", role=Role.MODERATOR)

    response = client.get("/api/_test/moderator")

    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "account_pending"
