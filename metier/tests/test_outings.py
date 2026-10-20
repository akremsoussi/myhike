"""Sorties (écrans 10 à 12) et leurs effets sur la carte, les refuges et les profils."""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models import Massif, Outing, Refuge, RefugeKind


def iso(days: float) -> str:
    """Date de départ dans `days` jours, avec fuseau comme l'envoie le navigateur."""
    return (datetime.now(UTC) + timedelta(days=days)).isoformat()


@pytest.fixture
def refuges(db: Session) -> dict[str, int]:
    massif = Massif(external_id=18, name="Écrins")
    db.add(massif)
    db.flush()
    rows = {
        "glacier_blanc": Refuge(
            external_id=1, name="Refuge du Glacier Blanc", kind=RefugeKind.GUARDED_HUT,
            latitude=44.934, longitude=6.4005, altitude=2542, massif_id=massif.id,
        ),
        "ecrins": Refuge(
            external_id=2, name="Refuge des Écrins", kind=RefugeKind.GUARDED_HUT,
            latitude=44.945, longitude=6.379, altitude=3170, massif_id=massif.id,
        ),
    }  # fmt: skip
    db.add_all(rows.values())
    db.commit()
    return {key: refuge.id for key, refuge in rows.items()}


@pytest.fixture
def people(active_client, make_client):
    return {"me": active_client, "lucas": make_client("lucas"), "sarah": make_client("sarah")}


def outing_body(refuges, **overrides) -> dict:
    body = {
        "title": "Tour du Glacier Blanc",
        "starts_at": iso(5),
        "max_participants": 3,
        "visibility": "public",
        "stops": [
            {"name": "Parking Pré de Madame Carle", "latitude": 44.92, "longitude": 6.42},
            {"refuge_id": refuges["glacier_blanc"]},
            {"refuge_id": refuges["ecrins"]},
        ],
        "path": [],
    }
    return {**body, **overrides}


def create(client, refuges, **overrides) -> dict:
    response = client.post("/api/outings", json=outing_body(refuges, **overrides))
    assert response.status_code == 201, response.json()
    return response.json()


def titles(response) -> list[str]:
    return [outing["title"] for outing in response.json()]


# ---------- Création et détail ----------


def test_create_outing(people, refuges):
    outing = create(people["me"], refuges)

    assert outing["organizer"]["username"] == "randonneur"
    assert outing["is_organizer"] and outing["is_participant"]
    assert outing["participant_count"] == 1 and outing["status"] == "open"
    assert [s["name"] for s in outing["stops"]] == [
        "Parking Pré de Madame Carle",
        "Refuge du Glacier Blanc",
        "Refuge des Écrins",
    ]
    assert outing["stops"][1]["altitude"] == 2542 and outing["stops"][0]["altitude"] is None
    assert outing["elevation_gain_m"] == 3170 - 2542
    assert 3000 < outing["distance_m"] < 5000  # à vol d'oiseau entre les points
    # Heure reçue avec fuseau, renvoyée en UTC.
    assert outing["starts_at"].endswith("+00:00")


def test_drawn_path_is_used_for_distance(people, refuges):
    path = [[44.92, 6.42], [44.93, 6.42]]  # ~1,1 km vers le nord
    outing = create(people["me"], refuges, path=path)

    assert 1000 < outing["distance_m"] < 1200
    assert outing["preview"] == path


@pytest.mark.parametrize(
    ("overrides", "field"),
    [
        ({"title": "ab"}, "title"),
        ({"starts_at": "2030-01-01T08:00:00"}, "starts_at"),  # sans fuseau
        ({"max_participants": 1}, "max_participants"),
        ({"stops": []}, "stops"),
        ({"stops": [{"name": "Nulle part"}]}, "stops"),
    ],
)
def test_invalid_outing_is_rejected(people, refuges, overrides, field):
    response = people["me"].post("/api/outings", json=outing_body(refuges, **overrides))

    assert response.status_code == 422
    assert field in response.json()["detail"]["fields"]


def test_outing_in_the_past_is_rejected(people, refuges):
    response = people["me"].post("/api/outings", json=outing_body(refuges, starts_at=iso(-1)))

    assert response.status_code == 422
    fields = response.json()["detail"]["fields"]
    assert fields == {"starts_at": "La sortie doit être dans le futur."}


def test_unknown_refuge_is_rejected(people, refuges):
    response = people["me"].post(
        "/api/outings", json=outing_body(refuges, stops=[{"refuge_id": 999999}])
    )

    assert response.json()["detail"]["code"] == "unknown_refuge"


# ---------- Participation ----------


def test_join_until_full_then_leave(people, refuges, make_client):
    outing = create(people["me"], refuges, max_participants=2)
    url = f"/api/outings/{outing['id']}/participation"

    joined = people["lucas"].put(url).json()
    assert joined["is_participant"] and joined["status"] == "full"

    refused = people["sarah"].put(url)
    assert refused.status_code == 409 and refused.json()["detail"]["code"] == "outing_full"

    assert people["lucas"].delete(url).json()["participant_count"] == 1
    assert people["sarah"].put(url).json()["is_participant"]


def test_organizer_cannot_leave(people, refuges):
    outing = create(people["me"], refuges)

    response = people["me"].delete(f"/api/outings/{outing['id']}/participation")

    assert response.json()["detail"]["code"] == "organizer_cannot_leave"


def test_past_outing_cannot_be_joined(people, refuges, db):
    outing = create(people["me"], refuges)
    db.execute(
        update(Outing)
        .where(Outing.id == outing["id"])
        .values(starts_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(days=1))
    )
    db.commit()

    response = people["lucas"].put(f"/api/outings/{outing['id']}/participation")

    assert response.json()["detail"]["code"] == "outing_past"
    assert titles(people["me"].get("/api/outings", params={"scope": "past"})) == [
        "Tour du Glacier Blanc"
    ]
    assert people["me"].get("/api/outings").json() == []


# ---------- Visibilité « Sur invitation » ----------


def test_invitation_only_outing_is_hidden_until_invited(people, refuges):
    me, lucas, sarah = people["me"], people["lucas"], people["sarah"]
    outing = create(me, refuges, visibility="invitation", title="Entre amis")
    url = f"/api/outings/{outing['id']}"

    assert lucas.get(url).status_code == 404
    assert titles(lucas.get("/api/outings")) == []
    assert lucas.put(f"{url}/participation").status_code == 404

    assert me.post(f"{url}/invitations", json={"username": "lucas"}).status_code == 204
    detail = lucas.get(url).json()
    assert detail["is_invited"] and detail["can_join"]
    assert lucas.put(f"{url}/participation").json()["is_participant"]
    assert sarah.get(url).status_code == 404


def test_only_organizer_can_invite_edit_or_delete(people, refuges):
    outing = create(people["me"], refuges)
    url = f"/api/outings/{outing['id']}"

    invitation = {"username": "sarah"}
    assert people["lucas"].post(f"{url}/invitations", json=invitation).status_code == 403
    assert people["lucas"].put(url, json=outing_body(refuges)).status_code == 403
    assert people["lucas"].delete(url).status_code == 403
    assert people["me"].delete(url).status_code == 204
    assert people["me"].get(url).status_code == 404


# ---------- Modification ----------


def test_update_replaces_stops(people, refuges):
    outing = create(people["me"], refuges)
    body = outing_body(
        refuges, title="Dôme des Écrins", stops=[{"refuge_id": refuges["ecrins"]}]
    )

    updated = people["me"].put(f"/api/outings/{outing['id']}", json=body).json()

    assert updated["title"] == "Dôme des Écrins"
    assert [s["position"] for s in updated["stops"]] == [1]
    assert updated["elevation_gain_m"] is None


def test_places_cannot_drop_below_participants(people, refuges):
    outing = create(people["me"], refuges, max_participants=3)
    people["lucas"].put(f"/api/outings/{outing['id']}/participation")
    people["sarah"].put(f"/api/outings/{outing['id']}/participation")

    response = people["me"].put(
        f"/api/outings/{outing['id']}", json=outing_body(refuges, max_participants=2)
    )

    assert "max_participants" in response.json()["detail"]["fields"]


# ---------- Onglets, refuges, carte et profils ----------


def test_tabs(people, refuges):
    me, lucas = people["me"], people["lucas"]
    create(me, refuges, title="La mienne", starts_at=iso(3))
    theirs = create(lucas, refuges, title="Celle de Lucas", starts_at=iso(2))
    me.put(f"/api/outings/{theirs['id']}/participation")

    assert titles(me.get("/api/outings")) == ["Celle de Lucas", "La mienne"]
    assert titles(me.get("/api/outings", params={"scope": "mine"})) == ["La mienne"]
    assert titles(me.get("/api/outings", params={"scope": "joined"})) == ["Celle de Lucas"]


def test_refuge_outings_and_map_filter(people, refuges):
    create(people["me"], refuges, stops=[{"refuge_id": refuges["glacier_blanc"]}])
    create(people["me"], refuges, visibility="invitation", stops=[{"refuge_id": refuges["ecrins"]}])

    here = people["lucas"].get("/api/outings", params={"refuge_id": refuges["glacier_blanc"]})
    assert len(here.json()) == 1
    # La sortie sur invitation ne signale pas son refuge aux autres.
    with_outing = people["lucas"].get("/api/refuges", params={"with_outing": "true"}).json()
    assert [r["name"] for r in with_outing["items"]] == ["Refuge du Glacier Blanc"]
    mine = people["me"].get("/api/refuges", params={"with_outing": "true"}).json()
    assert mine["total"] == 2


def test_profile_outings_respect_privacy(people, refuges):
    me, lucas = people["me"], people["lucas"]
    create(me, refuges)

    assert me.get("/api/users/randonneur").json()["outing_count"] == 1
    assert len(lucas.get("/api/users/randonneur/outings").json()["items"]) == 1

    settings = me.get("/api/me/privacy").json()
    me.put("/api/me/privacy", json={**settings, "outings_audience": "friends"})
    hidden = lucas.get("/api/users/randonneur/outings").json()
    assert hidden == {"items": [], "hidden": True}
    assert lucas.get("/api/users/randonneur").json()["outing_count"] is None
    # Les sorties publiques restent dans l'onglet Sorties.
    assert len(lucas.get("/api/outings").json()) == 1
