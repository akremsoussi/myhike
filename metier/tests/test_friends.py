"""Amitiés, profils et paramètres de confidentialité (écrans 05, 05b, 05c, 06)."""

import pytest
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import AccountStatus, Community, CommunityMember, User


@pytest.fixture
def people(active_client, make_client):
    """« randonneur » (active_client), « lucas » et « sarah », chacun connecté."""
    return {"me": active_client, "lucas": make_client("lucas"), "sarah": make_client("sarah")}


def relation(client, username: str) -> str:
    return client.get(f"/api/users/{username}").json()["relation"]


def usernames(items) -> list[str]:
    return [item["user"]["username"] for item in items]


def join(db: Session, slug: str, *usernames_: str) -> None:
    community = db.scalar(select(Community).where(Community.slug == slug))
    if community is None:
        community = Community(slug=slug, name=slug.capitalize(), region="Alpes")
        db.add(community)
        db.flush()
    for username in usernames_:
        user = db.scalar(select(User).where(User.username == username))
        db.add(CommunityMember(community_id=community.id, user_id=user.id))
    db.commit()


def befriend(a, b, b_username: str, a_username: str = "randonneur") -> None:
    a.post(f"/api/friends/{b_username}")
    b.post(f"/api/friends/{a_username}/accept")


# ---------- Demandes ----------


def test_request_then_accept(people):
    me, lucas = people["me"], people["lucas"]

    assert me.post("/api/friends/lucas").json() == {"relation": "request_sent"}
    assert relation(lucas, "randonneur") == "request_received"
    assert usernames(lucas.get("/api/friends").json()["received"]) == ["randonneur"]
    assert usernames(me.get("/api/friends").json()["sent"]) == ["lucas"]

    assert lucas.post("/api/friends/randonneur/accept").json() == {"relation": "friends"}
    assert relation(me, "lucas") == "friends"
    profile = me.get("/api/users/lucas").json()
    assert profile["friends_since"] is not None
    assert usernames(me.get("/api/friends").json()["friends"]) == ["lucas"]


def test_crossed_requests_become_friendship(people):
    people["me"].post("/api/friends/lucas")

    assert people["lucas"].post("/api/friends/randonneur").json() == {"relation": "friends"}


def test_decline_is_silent(people):
    me, lucas = people["me"], people["lucas"]
    me.post("/api/friends/lucas")

    assert lucas.post("/api/friends/randonneur/decline").json() == {"relation": "none"}
    # Le demandeur n'est pas prévenu et ne peut pas renvoyer sa demande.
    assert relation(me, "lucas") == "request_sent"
    assert me.post("/api/friends/lucas").json() == {"relation": "request_sent"}
    assert lucas.get("/api/friends").json()["received"] == []
    # Celui qui a refusé peut changer d'avis et demander à son tour.
    assert lucas.post("/api/friends/randonneur").json() == {"relation": "request_sent"}
    assert relation(me, "lucas") == "request_received"


def test_cancel_sent_request(people):
    me = people["me"]
    me.post("/api/friends/lucas")

    assert me.delete("/api/friends/lucas/request").json() == {"relation": "none"}
    assert people["lucas"].get("/api/friends").json()["received"] == []


def test_either_friend_can_remove(people):
    me, lucas = people["me"], people["lucas"]
    befriend(me, lucas, "lucas")

    assert lucas.delete("/api/friends/randonneur").json() == {"relation": "none"}
    assert relation(me, "lucas") == "none"


def test_accept_without_request_fails(people):
    response = people["me"].post("/api/friends/lucas/accept")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "no_request"


def test_cannot_befriend_yourself_or_unknown_user(people):
    assert people["me"].post("/api/friends/randonneur").status_code == 422
    assert people["me"].post("/api/friends/personne").status_code == 404


def test_requests_limited_to_community_members(people, db):
    people["lucas"].put(
        "/api/me/privacy",
        json={
            "default_post_visibility": "public",
            "friends_list_audience": "friends",
            "outings_audience": "everyone",
            "friend_requests_from": "communities",
            "show_in_suggestions": True,
        },
    )

    assert people["me"].get("/api/users/lucas").json()["can_send_request"] is False
    refused = people["me"].post("/api/friends/lucas")
    assert refused.status_code == 403
    assert refused.json()["detail"]["code"] == "requests_restricted"

    join(db, "ecrins", "randonneur", "lucas")
    assert people["me"].post("/api/friends/lucas").json() == {"relation": "request_sent"}


# ---------- Profils ----------


def test_non_friend_sees_public_posts_and_hidden_count(people):
    me, lucas = people["me"], people["lucas"]
    lucas.post("/api/posts", json={"body": "public", "visibility": "public"})
    lucas.post("/api/posts", json={"body": "privé 1", "visibility": "friends"})
    lucas.post("/api/posts", json={"body": "privé 2", "visibility": "friends"})

    profile = me.get("/api/users/lucas").json()
    posts = me.get("/api/users/lucas/posts").json()["items"]

    assert profile["post_count"] == 3 and profile["hidden_post_count"] == 2
    assert [post["body"] for post in posts] == ["public"]
    assert "privé" not in me.get("/api/users/lucas/posts").text

    befriend(me, lucas, "lucas")
    assert me.get("/api/users/lucas").json()["hidden_post_count"] == 0
    assert len(me.get("/api/users/lucas/posts").json()["items"]) == 3


def test_friend_count_respects_friends_list_audience(people):
    me, lucas, sarah = people["me"], people["lucas"], people["sarah"]
    befriend(me, lucas, "lucas")

    # Par défaut, seuls les amis voient la liste d'amis.
    assert me.get("/api/users/lucas").json()["friend_count"] == 1
    assert sarah.get("/api/users/lucas").json()["friend_count"] is None

    settings = lucas.get("/api/me/privacy").json()
    lucas.put("/api/me/privacy", json={**settings, "friends_list_audience": "me"})
    assert me.get("/api/users/lucas").json()["friend_count"] is None
    assert lucas.get("/api/users/lucas").json()["friend_count"] == 1


def test_own_profile_has_requests_and_friends_preview(people, db):
    me, lucas, sarah = people["me"], people["lucas"], people["sarah"]
    befriend(me, lucas, "lucas")
    sarah.post("/api/friends/randonneur")
    join(db, "ecrins", "randonneur", "sarah")

    profile = me.get("/api/users/randonneur").json()

    assert profile["relation"] == "self"
    assert profile["pending_request_count"] == 1
    assert [friend["username"] for friend in profile["friends_preview"]] == ["lucas"]
    assert profile["communities"] == [{"slug": "ecrins", "name": "Ecrins"}]
    # Les champs réservés au propriétaire ne sont pas remplis pour les autres.
    assert lucas.get("/api/users/randonneur").json()["pending_request_count"] is None


def test_other_profile_lists_common_communities_only(people, db):
    join(db, "ecrins", "randonneur", "lucas")
    join(db, "vanoise", "lucas")

    profile = people["me"].get("/api/users/lucas").json()

    assert profile["communities"] == [{"slug": "ecrins", "name": "Ecrins"}]
    assert profile["community_count"] == 2


def test_suspended_accounts_are_hidden(people, db):
    db.execute(
        update(User).where(User.username == "lucas").values(status=AccountStatus.SUSPENDED)
    )
    db.commit()

    assert people["me"].get("/api/users/lucas").status_code == 404
    assert people["me"].post("/api/friends/lucas").status_code == 404


# ---------- Suggestions ----------


def test_suggestions_come_from_communities(people, make_client, db):
    me, lucas, sarah = people["me"], people["lucas"], people["sarah"]
    hugo = make_client("hugo")
    make_client("paul")
    join(db, "ecrins", "randonneur", "lucas", "sarah", "hugo")
    # Paul n'est dans aucune communauté commune : jamais suggéré.
    # Hugo est ami avec Lucas, qui est mon ami : 1 ami en commun, il passe en tête.
    befriend(me, lucas, "lucas")
    befriend(hugo, lucas, "lucas", a_username="hugo")

    suggestions = me.get("/api/friends/suggestions").json()

    assert usernames(suggestions) == ["hugo", "sarah"]  # pas Lucas, déjà ami
    assert suggestions[0]["mutual_friend_count"] == 1
    assert suggestions[0]["community"]["slug"] == "ecrins"

    settings = sarah.get("/api/me/privacy").json()
    sarah.put("/api/me/privacy", json={**settings, "show_in_suggestions": False})
    me.post("/api/friends/hugo")
    assert me.get("/api/friends/suggestions").json() == []


# ---------- Confidentialité ----------


def test_privacy_defaults_and_update(people):
    me = people["me"]

    assert me.get("/api/me/privacy").json() == {
        "default_post_visibility": "public",
        "friends_list_audience": "friends",
        "outings_audience": "everyone",
        "friend_requests_from": "everyone",
        "show_in_suggestions": True,
    }
    updated = {
        "default_post_visibility": "friends",
        "friends_list_audience": "everyone",
        "outings_audience": "me",
        "friend_requests_from": "communities",
        "show_in_suggestions": False,
    }
    assert me.put("/api/me/privacy", json=updated).json() == updated
    assert me.get("/api/me/privacy").json() == updated


def test_invalid_privacy_value_is_rejected(people):
    settings = people["me"].get("/api/me/privacy").json()

    response = people["me"].put("/api/me/privacy", json={**settings, "outings_audience": "moi"})

    assert response.status_code == 422
