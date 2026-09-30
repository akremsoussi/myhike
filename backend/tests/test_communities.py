"""Communautés, posts et règle de visibilité."""

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AccountStatus,
    Community,
    CommunityMember,
    Friendship,
    FriendshipStatus,
    Massif,
    Post,
    Refuge,
    RefugeKind,
    Role,
    User,
    Visibility,
)


def make_user(db: Session, username: str) -> User:
    user = User(
        username=username,
        email=f"{username}@mail.fr",
        password_hash="x",
        display_name=username.capitalize(),
        status=AccountStatus.ACTIVE,
    )
    db.add(user)
    db.flush()
    return user


def me(db: Session) -> User:
    return db.scalars(select(User).where(User.username == "randonneur")).one()


@pytest.fixture
def world(db: Session, active_client) -> dict:
    """Deux communautés, un ami et un inconnu qui ont publié dans « Écrins »."""
    massif = Massif(external_id=18, name="Écrins")
    db.add(massif)
    db.flush()
    refuge = Refuge(
        external_id=1550, name="Refuge du Glacier Blanc", kind=RefugeKind.GUARDED_HUT,
        latitude=44.934, longitude=6.4005, massif_id=massif.id,
    )  # fmt: skip
    ecrins = Community(
        slug="ecrins", name="Écrins", region="Alpes", massif=massif, refuges=[refuge]
    )
    pyrenees = Community(slug="pyrenees", name="Pyrénées", region="Pyrénées")
    db.add_all([ecrins, pyrenees])

    friend, stranger = make_user(db, "camille"), make_user(db, "lucas")
    db.add(
        Friendship(
            requester_id=me(db).id, addressee_id=friend.id, status=FriendshipStatus.ACCEPTED
        )
    )
    db.flush()
    db.add_all(
        [
            CommunityMember(community_id=ecrins.id, user_id=friend.id),
            CommunityMember(community_id=ecrins.id, user_id=stranger.id),
        ]
    )
    public, friends = Visibility.PUBLIC, Visibility.FRIENDS
    posts = {
        "friend_public": Post(author=friend, community=ecrins, body="a", visibility=public),
        "friend_private": Post(author=friend, community=ecrins, body="b", visibility=friends),
        "stranger_public": Post(author=stranger, community=ecrins, body="c", visibility=public),
        "stranger_private": Post(
            author=stranger, community=ecrins, body="secret", visibility=friends
        ),
    }
    db.add_all(posts.values())
    db.commit()
    return {"posts": {key: post.id for key, post in posts.items()}, "stranger": stranger.id}


def bodies(response) -> list[str]:
    return [post["body"] for post in response.json()["items"]]


# ---------- Communautés ----------


def test_communities_require_active_account(client):
    assert client.get("/api/communities").status_code == 401


def test_list_communities_with_counts(active_client, world):
    response = active_client.get("/api/communities")

    assert response.status_code == 200
    ecrins, pyrenees = response.json()
    assert (ecrins["slug"], pyrenees["slug"]) == ("ecrins", "pyrenees")
    assert ecrins["member_count"] == 2 and ecrins["post_count"] == 4
    assert ecrins["is_member"] is False
    assert ecrins["massif"]["name"] == "Écrins"


def test_join_and_leave_are_idempotent(active_client, world):
    first = active_client.put("/api/communities/ecrins/membership")
    second = active_client.put("/api/communities/ecrins/membership")

    assert first.json()["is_member"] is True
    assert second.json()["member_count"] == 3
    left = active_client.delete("/api/communities/ecrins/membership")
    assert left.json()["is_member"] is False and left.json()["member_count"] == 2
    assert active_client.delete("/api/communities/ecrins/membership").status_code == 200


def test_community_detail(active_client, world):
    response = active_client.get("/api/communities/ecrins")

    assert response.status_code == 200
    detail = response.json()
    assert [m["username"] for m in detail["members"]] == ["lucas", "camille"]
    assert "email" not in detail["members"][0]
    assert [r["name"] for r in detail["refuges"]] == ["Refuge du Glacier Blanc"]
    assert active_client.get("/api/communities/inconnue").status_code == 404


# ---------- Visibilité ----------


def test_feed_hides_friends_only_posts_of_non_friends(active_client, world):
    response = active_client.get("/api/communities/ecrins/posts")

    assert response.status_code == 200
    # Plus récent d'abord ; le post « Amis » de l'inconnu n'est jamais envoyé.
    assert bodies(response) == ["c", "b", "a"]
    assert "secret" not in response.text


def test_author_sees_own_friends_only_posts(active_client, world):
    active_client.put("/api/communities/ecrins/membership")
    active_client.post(
        "/api/posts",
        json={"body": "moi", "visibility": "friends", "community_slug": "ecrins"},
    )

    assert bodies(active_client.get("/api/communities/ecrins/posts"))[0] == "moi"


def test_pending_friend_request_does_not_grant_access(active_client, world, db):
    db.add(
        Friendship(requester_id=world["stranger"], addressee_id=me(db).id)
    )  # status pending
    db.commit()

    assert "secret" not in bodies(active_client.get("/api/communities/ecrins/posts"))


def test_friendship_counts_in_both_directions(active_client, world, db):
    db.add(
        Friendship(
            requester_id=world["stranger"],
            addressee_id=me(db).id,
            status=FriendshipStatus.ACCEPTED,
        )
    )
    db.commit()

    assert "secret" in bodies(active_client.get("/api/communities/ecrins/posts"))


def test_invisible_post_cannot_be_liked(active_client, world):
    post_id = world["posts"]["stranger_private"]

    assert active_client.put(f"/api/posts/{post_id}/like").status_code == 404


def test_feed_pagination(active_client, world):
    url = "/api/communities/ecrins/posts"
    first = active_client.get(url, params={"limit": 2}).json()
    second = active_client.get(url, params={"limit": 2, "before": first["next_before"]}).json()

    assert [p["body"] for p in first["items"]] == ["c", "b"]
    assert [p["body"] for p in second["items"]] == ["a"]
    assert second["next_before"] is None


# ---------- Publication ----------


def test_publish_on_profile_only(active_client, world):
    body = {"body": "  Belle sortie  ", "visibility": "public"}
    response = active_client.post("/api/posts", json=body)

    assert response.status_code == 201
    post = response.json()
    assert post["body"] == "Belle sortie"
    assert post["community"] is None
    assert post["author"]["username"] == "randonneur"
    assert post["can_delete"] is True


def test_publish_in_community_requires_membership(active_client, world):
    body = {"body": "Salut", "visibility": "public", "community_slug": "ecrins"}

    refused = active_client.post("/api/posts", json=body)
    assert refused.status_code == 403
    assert refused.json()["detail"]["code"] == "not_member"

    active_client.put("/api/communities/ecrins/membership")
    created = active_client.post("/api/posts", json=body)
    assert created.status_code == 201
    assert created.json()["community"] == {"slug": "ecrins", "name": "Écrins"}


def test_empty_post_is_rejected(active_client, world):
    response = active_client.post("/api/posts", json={"body": "   ", "visibility": "public"})

    assert response.status_code == 422
    assert response.json()["detail"]["fields"]["body"] == "Écrivez quelques mots."


def test_like_and_unlike(active_client, world):
    post_id = world["posts"]["friend_public"]

    url = f"/api/posts/{post_id}/like"

    assert active_client.put(url).json() == {"like_count": 1, "liked": True}
    assert active_client.put(url).json()["like_count"] == 1
    assert active_client.delete(url).json() == {"like_count": 0, "liked": False}


def test_only_author_or_moderator_can_delete(active_client, world, db):
    post_id = world["posts"]["stranger_public"]
    assert active_client.delete(f"/api/posts/{post_id}").status_code == 403

    me(db).role = Role.MODERATOR
    db.commit()
    assert active_client.delete(f"/api/posts/{post_id}").status_code == 204
    db.expire_all()
    assert db.get(Post, post_id) is None
