"""Signalements et écrans de modération (13 à 16)."""

import pytest
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import AccountStatus, Community, CommunityMember, Refuge, RefugeKind, Role, User


@pytest.fixture
def people(active_client, make_client, db: Session):
    """« randonneur » (utilisateur), « modo » (modérateur), « troll » (utilisateur)."""
    clients = {"me": active_client, "modo": make_client("modo"), "troll": make_client("troll")}
    db.execute(update(User).where(User.username == "modo").values(role=Role.MODERATOR))
    db.commit()
    return clients


@pytest.fixture
def ecrins(db: Session) -> Community:
    community = Community(slug="ecrins", name="Écrins", region="Alpes")
    db.add(community)
    db.flush()
    for username in ("randonneur", "troll"):
        user = db.scalar(select(User).where(User.username == username))
        db.add(CommunityMember(community_id=community.id, user_id=user.id))
    db.commit()
    return community


def troll_post(people, visibility="public") -> int:
    body = {"body": "Message insultant", "visibility": visibility, "community_slug": "ecrins"}
    return people["troll"].post("/api/posts", json=body).json()["id"]


# ---------- Accès ----------


@pytest.mark.parametrize(
    "path", ["/api/moderation/summary", "/api/moderation/dashboard", "/api/moderation/users"]
)
def test_moderation_is_reserved_to_moderators(people, path):
    assert people["me"].get(path).status_code == 403
    assert people["modo"].get(path).status_code == 200


# ---------- Signalements ----------


def test_report_post_then_moderator_sees_it(people, ecrins):
    post_id = troll_post(people, visibility="friends")
    # Un post « Amis » de quelqu'un qui n'est pas mon ami : je ne peux pas le signaler.
    assert people["me"].post(
        "/api/reports", json={"post_id": post_id, "reason": "insulting"}
    ).status_code == 404

    public_id = troll_post(people)
    response = people["me"].post(
        "/api/reports", json={"post_id": public_id, "reason": "insulting", "comment": " grossier "}
    )
    assert response.status_code == 204
    # Un doublon encore ouvert n'est pas recréé.
    people["me"].post("/api/reports", json={"post_id": public_id, "reason": "spam"})

    assert people["modo"].get("/api/moderation/summary").json() == {"open_reports": 1}
    report = people["modo"].get("/api/moderation/reports").json()[0]
    assert report["target"]["username"] == "troll"
    assert report["post"]["body"] == "Message insultant"
    assert report["comment"] == "grossier"


def test_moderator_sees_friends_only_post_in_report(people, ecrins, make_client, db):
    post_id = troll_post(people, visibility="friends")
    friend = make_client("ami")
    friend.post("/api/friends/troll")
    people["troll"].post("/api/friends/ami/accept")
    friend.post("/api/reports", json={"post_id": post_id, "reason": "insulting"})

    report = people["modo"].get("/api/moderation/reports").json()[0]

    assert report["post"]["visibility"] == "friends"
    assert report["post"]["body"] == "Message insultant"


def test_cannot_report_yourself(people):
    response = people["me"].post(
        "/api/reports", json={"username": "randonneur", "reason": "spam"}
    )

    assert response.json()["detail"]["code"] == "invalid_report"


def test_resolve_and_delete_reported_post(people, ecrins):
    post_id = troll_post(people)
    people["me"].post("/api/reports", json={"post_id": post_id, "reason": "insulting"})

    assert people["modo"].delete(f"/api/moderation/posts/{post_id}").status_code == 204
    assert people["modo"].get("/api/moderation/summary").json() == {"open_reports": 0}
    activity = people["modo"].get("/api/moderation/dashboard").json()["activity"]
    assert activity[0]["message"] == "Post supprimé dans « Écrins »"
    assert activity[0]["actor"]["username"] == "modo"


# ---------- Tableau de bord ----------


def test_dashboard(people, ecrins):
    people["me"].post("/api/reports", json={"username": "troll", "reason": "fake_profile"})
    people["modo"].post("/api/reports", json={"username": "troll", "reason": "spam"})

    dashboard = people["modo"].get("/api/moderation/dashboard").json()

    assert dashboard["users"] == {"value": 3, "recent": 3}
    assert dashboard["communities"]["value"] == 1
    assert dashboard["reported_accounts"] == 1
    reported = dashboard["reported"][0]
    assert reported["user"]["username"] == "troll" and reported["report_count"] == 2
    assert reported["last_reason"] == "spam"
    assert dashboard["activity"][0]["message"] == "Compte @troll signalé"


# ---------- Communautés ----------


def test_create_update_delete_community(people, db):
    refuge = Refuge(
        external_id=1, name="Refuge de Gève", kind=RefugeKind.GUARDED_HUT,
        latitude=45.03, longitude=5.53,
    )  # fmt: skip
    db.add(refuge)
    db.commit()
    body = {"name": "Écrins & Oisans", "region": "Alpes", "refuge_ids": [refuge.id]}

    created = people["modo"].post("/api/moderation/communities", json=body)
    assert created.status_code == 201
    assert created.json()["slug"] == "ecrins-oisans"
    assert [r["name"] for r in created.json()["refuges"]] == ["Refuge de Gève"]
    # Même nom : identifiant unique.
    again = people["modo"].post("/api/moderation/communities", json=body).json()
    assert again["slug"] == "ecrins-oisans-2"

    updated = people["modo"].put(
        "/api/moderation/communities/ecrins-oisans",
        json={**body, "name": "Oisans", "description": "Nouveau", "refuge_ids": []},
    ).json()
    assert updated["slug"] == "ecrins-oisans"  # l'adresse ne change pas
    assert updated["name"] == "Oisans" and updated["refuges"] == []

    assert people["modo"].delete("/api/moderation/communities/ecrins-oisans").status_code == 204
    assert people["me"].get("/api/communities/ecrins-oisans").status_code == 404
    assert [c["slug"] for c in people["modo"].get("/api/moderation/communities").json()] == [
        "ecrins-oisans-2"
    ]


def test_community_validation(people):
    response = people["modo"].post(
        "/api/moderation/communities", json={"name": "A", "region": "Alpes", "refuge_ids": [999]}
    )

    assert response.status_code == 422
    assert "name" in response.json()["detail"]["fields"]


# ---------- Comptes ----------


def test_accounts_list_and_filters(people):
    people["me"].post("/api/reports", json={"username": "troll", "reason": "spam"})
    modo = people["modo"]

    listing = modo.get("/api/moderation/users").json()
    assert listing["total"] == 3 and listing["moderator_count"] == 1
    assert {u["username"]: u["open_report_count"] for u in listing["items"]}["troll"] == 1

    def usernames(**params):
        items = modo.get("/api/moderation/users", params=params).json()["items"]
        return [u["username"] for u in items]

    assert usernames(filter="moderators") == ["modo"]
    assert usernames(filter="reported") == ["troll"]
    assert usernames(q="randonneur@") == ["randonneur"]  # recherche par email


def test_account_detail(people, ecrins):
    troll_post(people)
    people["me"].post("/api/reports", json={"username": "troll", "reason": "spam"})

    detail = people["modo"].get("/api/moderation/users/troll").json()

    assert detail["community_count"] == 1 and detail["post_count"] == 1
    assert detail["outing_count"] == 0
    assert [r["reason"] for r in detail["reports"]] == ["spam"]

    resolved = people["modo"].post("/api/moderation/users/troll/reports/resolve").json()
    assert resolved["reports"] == [] and resolved["open_report_count"] == 0


def test_promote_and_demote(people, make_client, db: Session):
    url = "/api/moderation/users/randonneur/role"
    # Un administrateur classique (moderator) ne peut pas modifier les rôles.
    assert people["modo"].put(url, json={"role": "moderator"}).status_code == 403

    super_client = make_client("chef")
    db.execute(update(User).where(User.username == "chef").values(role=Role.SUPER_ADMIN))
    db.commit()

    promoted = super_client.put(url, json={"role": "moderator"})
    assert promoted.status_code == 200
    assert promoted.json()["role"] == "moderator"
    assert people["me"].get("/api/moderation/summary").status_code == 200
    activity = super_client.get("/api/moderation/dashboard").json()["activity"]
    # Nom affiché = pseudo tant que le profil n'est pas modifié.
    assert activity[0]["message"] == "randonneur promu modérateur"

    # Un modérateur classique ne peut pas suspendre ou supprimer un autre modérateur.
    assert people["modo"].post("/api/moderation/users/randonneur/suspend").status_code == 403
    assert people["modo"].delete("/api/moderation/users/randonneur").status_code == 403
    # Ni agir sur le Super Admin.
    assert people["modo"].post("/api/moderation/users/chef/suspend").status_code == 403

    assert super_client.put(url, json={"role": "user"}).json()["role"] == "user"
    assert people["me"].get("/api/moderation/summary").status_code == 403


def test_suspend_revokes_access_then_reactivate(people):
    modo, troll = people["modo"], people["troll"]

    assert modo.post("/api/moderation/users/troll/suspend").json()["status"] == "suspended"
    assert troll.get("/api/communities").status_code in (401, 403)
    assert modo.get("/api/moderation/users", params={"filter": "suspended"}).json()["total"] == 1

    assert modo.post("/api/moderation/users/troll/reactivate").json()["status"] == "active"


def test_moderator_cannot_act_on_self(people):
    modo = people["modo"]

    for response in (
        modo.post("/api/moderation/users/modo/suspend"),
        modo.put("/api/moderation/users/modo/role", json={"role": "user"}),
        modo.delete("/api/moderation/users/modo"),
    ):
        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "self_action"


def test_delete_account(people, ecrins, db):
    troll_post(people)

    assert people["modo"].delete("/api/moderation/users/troll").status_code == 204
    assert people["modo"].get("/api/moderation/users/troll").status_code == 404
    assert people["me"].get("/api/communities/ecrins/posts").json()["items"] == []


def test_export_csv(people):
    response = people["modo"].get("/api/moderation/users/export")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    lines = response.text.lstrip("﻿").splitlines()
    assert lines[0] == "Pseudo;Nom;Email;Rôle;Statut;Inscrit le;Signalements"
    assert any(line.startswith("modo;") and ";Modérateur;Actif;" in line for line in lines)
    assert people["me"].get("/api/moderation/users/export").status_code == 403


def test_pending_account_is_listed_as_pending(people, db):
    db.execute(
        update(User).where(User.username == "troll").values(status=AccountStatus.PENDING_EMAIL)
    )
    db.commit()

    row = people["modo"].get("/api/moderation/users", params={"q": "troll"}).json()["items"][0]

    assert row["status"] == "pending_email"
