"""Chemins des posts, posts liés à un refuge, membres, recherche globale et profil modifiable."""

from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import CommunityMember, Outing, OutingParticipant, OutingVisibility, Refuge, utcnow
from app.services import geo
from tests.test_communities import me, world  # noqa: F401  (fixture partagée)

# Deux points à ~1,1 km l'un de l'autre (0,01° de latitude).
PATH = [[44.90, 6.40], [44.91, 6.40]]


def publish(client, **fields):
    return client.post("/api/posts", json={"visibility": "public", **fields})


# ---------- Chemins ----------


def test_post_with_drawn_path_has_distance_but_no_elevation(active_client):
    response = publish(active_client, path=PATH)

    assert response.status_code == 201
    post = response.json()
    assert post["body"] == "" and post["path"] == PATH
    assert 1100 <= post["distance_m"] <= 1125
    assert post["elevation_gain_m"] is None


def test_gpx_path_elevation_gain_ignores_noise(active_client):
    path = [[44.90, 6.40, 1000], [44.901, 6.40, 1002], [44.902, 6.40, 1100], [44.903, 6.40, 1050],
            [44.904, 6.40, 1120]]  # fmt: skip

    post = publish(active_client, path=path).json()

    # +100 puis +70 ; la variation de 2 m est sous le seuil.
    assert post["elevation_gain_m"] == 170
    assert post["path"][0] == [44.90, 6.40]


def test_path_must_be_valid(active_client):
    assert publish(active_client, path=[[44.9, 6.4]]).status_code == 422
    assert publish(active_client, path=[[95, 6.4], [44.9, 6.4]]).status_code == 422
    too_long = [[44.9, 6.4 + i / 10000] for i in range(2001)]
    assert publish(active_client, path=too_long).status_code == 422


def test_preview_is_simplified():
    from app.services.posts import PREVIEW_POINTS, preview

    path = [[44.9 + i / 10000, 6.4] for i in range(1999)]
    points = preview(path)

    assert points is not None and len(points) <= PREVIEW_POINTS + 1
    assert points[0] == (path[0][0], path[0][1]) and points[-1] == (path[-1][0], path[-1][1])


def test_elevation_gain_threshold():
    assert geo.elevation_gain_m([1000, 1004, 1000, 1004]) == 0
    assert geo.elevation_gain_m([1000, 1010, 1006, 1020]) == 20


# ---------- Posts liés à un refuge ----------


def test_refuge_posts_follow_visibility(active_client, db: Session, world):  # noqa: F811
    refuge = db.scalars(select(Refuge)).one()
    mine = publish(active_client, body="au refuge", refuge_id=refuge.id).json()
    assert mine["refuge"] == {"id": refuge.id, "name": refuge.name}

    response = active_client.get(f"/api/refuges/{refuge.id}/posts")

    assert [post["body"] for post in response.json()["items"]] == ["au refuge"]
    assert active_client.get("/api/refuges/999999/posts").status_code == 404
    assert publish(active_client, body="x", refuge_id=999999).status_code == 422


def test_friends_only_refuge_post_hidden_from_strangers(active_client, make_client, db, world):  # noqa: F811
    refuge = db.scalars(select(Refuge)).one()
    publish(active_client, body="privé", visibility="friends", refuge_id=refuge.id)
    other = make_client("inconnu")

    response = other.get(f"/api/refuges/{refuge.id}/posts")

    assert response.json()["items"] == []


# ---------- Membres d'une communauté ----------


def test_member_list_with_search_and_pages(active_client, db: Session, world):  # noqa: F811
    active_client.put("/api/communities/ecrins/membership")
    # Arrivée plus tardive que les membres du jeu de données (même seconde sinon).
    db.execute(
        update(CommunityMember)
        .where(CommunityMember.user_id == me(db).id)
        .values(joined_at=utcnow() + timedelta(minutes=1))
    )
    db.commit()

    everyone = active_client.get("/api/communities/ecrins/members").json()
    assert everyone["total"] == 3
    assert [m["user"]["username"] for m in everyone["items"]] == ["randonneur", "lucas", "camille"]
    assert "email" not in everyone["items"][0]["user"]

    found = active_client.get("/api/communities/ecrins/members", params={"q": "CAM"}).json()
    assert found["total"] == 1 and found["items"][0]["user"]["username"] == "camille"

    second = active_client.get("/api/communities/ecrins/members", params={"offset": 2}).json()
    assert [m["user"]["username"] for m in second["items"]] == ["camille"]
    assert active_client.get("/api/communities/inconnue/members").status_code == 404


# ---------- Modifier le profil ----------


def test_edit_profile(active_client):
    response = active_client.put(
        "/api/me/profile", json={"display_name": "  Camille   Martin ", "bio": " Grimpeuse. "}
    )

    assert response.status_code == 200
    assert response.json() == {"display_name": "Camille Martin", "bio": "Grimpeuse."}
    profile = active_client.get("/api/users/randonneur").json()
    assert profile["user"]["display_name"] == "Camille Martin"
    assert profile["bio"] == "Grimpeuse."
    assert active_client.get("/api/auth/me").json()["user"]["display_name"] == "Camille Martin"


def test_edit_profile_validates(active_client):
    response = active_client.put("/api/me/profile", json={"display_name": "A", "bio": "x" * 301})

    assert response.status_code == 422
    assert set(response.json()["detail"]["fields"]) == {"display_name", "bio"}


# ---------- Recherche globale ----------


def test_search_finds_each_category(active_client, db: Session, world):  # noqa: F811
    organizer = me(db)
    outing = Outing(
        title="Traversée du Glacier Blanc",
        starts_at=utcnow().replace(year=utcnow().year + 1),
        max_participants=4,
        visibility=OutingVisibility.PUBLIC,
        organizer_id=organizer.id,
    )
    db.add(outing)
    db.flush()
    db.add(OutingParticipant(outing_id=outing.id, user_id=organizer.id))
    db.commit()
    publish(active_client, body="Nuit au glacier blanc")

    results = active_client.get("/api/search", params={"q": "glacier"}).json()

    assert [r["name"] for r in results["refuges"]] == ["Refuge du Glacier Blanc"]
    assert [o["title"] for o in results["outings"]] == ["Traversée du Glacier Blanc"]
    assert [p["body"] for p in results["posts"]] == ["Nuit au glacier blanc"]
    by_name = active_client.get("/api/search", params={"q": "écrins"}).json()
    assert [c["slug"] for c in by_name["communities"]] == ["ecrins"]
    users = active_client.get("/api/search", params={"q": "luc"}).json()["users"]
    assert [u["username"] for u in users] == ["lucas"]


def test_search_respects_visibility(active_client, world):  # noqa: F811
    results = active_client.get("/api/search", params={"q": "secret"}).json()

    assert results["posts"] == []


def test_search_needs_two_characters(active_client):
    assert active_client.get("/api/search", params={"q": "a"}).status_code == 422
