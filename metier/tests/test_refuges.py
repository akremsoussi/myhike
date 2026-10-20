"""Refuges : import depuis refuges.info et API de la carte."""

import pytest
from sqlalchemy.orm import Session

from app.models import Massif, Refuge, RefugeKind
from app.services.refuges_info import parse_point


def feature(type_id: int = 10, etat: str = "", **props) -> dict:
    """Point GeoJSON au format de refuges.info (detail=complet)."""
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [6.40054, 44.934]},
        "properties": {
            "id": 1550,
            "nom": " Refuge du Glacier Blanc ",
            "type": {"id": type_id, "valeur": "refuge gardé"},
            "coord": {"alt": 2542},
            "etat": {"valeur": etat},
            "places": {"valeur": 135},
            "acces": {"valeur": "Depuis le Pré de Madame Carle.\r\nSentier balisé."},
            "remarque": {"valeur": ""},
            "proprio": {"valeur": "CAF Briançon\r\nTéléphone : 04 92 23 50 24"},
            "lien": "https://www.refuges.info/point/1550/",
            "date": {"derniere_modif": "2024-06-28 09:08:20.52894+02"},
            **props,
        },
    }


# ---------- Import ----------


def test_parse_point_maps_refuges_info_fields():
    fields = parse_point(feature())

    assert fields["external_id"] == 1550
    assert fields["name"] == "Refuge du Glacier Blanc"
    assert fields["kind"] == RefugeKind.GUARDED_HUT
    assert (fields["latitude"], fields["longitude"]) == (44.934, 6.40054)
    assert fields["altitude"] == 2542 and fields["capacity"] == 135
    assert fields["access"] == "Depuis le Pré de Madame Carle.\nSentier balisé."
    assert fields["remarks"] is None  # texte vide
    assert fields["state"] is None
    assert fields["source_updated_at"].isoformat() == "2024-06-28T07:08:20"  # UTC


@pytest.mark.parametrize(
    ("type_id", "kind"),
    [(7, RefugeKind.UNGUARDED_HUT), (9, RefugeKind.GITE), (10, RefugeKind.GUARDED_HUT)],
)
def test_parse_point_kinds(type_id, kind):
    assert parse_point(feature(type_id=type_id))["kind"] == kind


def test_parse_point_skips_other_types_and_destroyed_buildings():
    assert parse_point(feature(type_id=23)) is None  # point d'eau
    assert parse_point(feature(etat="Détruite")) is None
    assert parse_point(feature(etat="Fermée"))["state"] == "Fermée"


def test_parse_point_tolerates_missing_numbers():
    fields = parse_point(feature(places={"valeur": ""}, coord={"alt": None}))

    assert fields["capacity"] is None and fields["altitude"] is None


# ---------- API ----------


def make_refuge(external_id: int, name: str, kind: RefugeKind, lat: float, lng: float, **extra):
    return Refuge(
        external_id=external_id, name=name, kind=kind, latitude=lat, longitude=lng, **extra
    )


@pytest.fixture
def refuges(db: Session) -> dict[str, int]:
    ecrins = Massif(external_id=18, name="Écrins")
    vanoise = Massif(external_id=9, name="Vanoise")
    db.add_all([ecrins, vanoise])
    db.flush()
    guarded, unguarded = RefugeKind.GUARDED_HUT, RefugeKind.UNGUARDED_HUT
    rows = {
        "glacier_blanc": make_refuge(
            1550, "Refuge du Glacier Blanc", guarded, 44.934, 6.4005,
            altitude=2542, capacity=135, massif_id=ecrins.id,
        ),
        "pelvoux": make_refuge(
            1536, "Refuge du Pelvoux", unguarded, 44.905, 6.419, massif_id=ecrins.id
        ),
        "gite": make_refuge(
            2000, "Gîte d'Ailefroide", RefugeKind.GITE, 44.883, 6.444, massif_id=ecrins.id
        ),
        "vanoise": make_refuge(
            3000, "Refuge de la Dent Parrachée", guarded, 45.27, 6.78, massif_id=vanoise.id
        ),
    }  # fmt: skip
    db.add_all(rows.values())
    db.commit()
    return {key: refuge.id for key, refuge in rows.items()}


ECRINS_BBOX = "6.3,44.85,6.5,44.95"


def names(response) -> list[str]:
    return [item["name"] for item in response.json()["items"]]


def test_refuges_require_active_account(client, refuges):
    assert client.get("/api/refuges").status_code == 401
    account = {"username": "pending", "email": "p@mail.fr", "password": "motdepasse8"}
    client.post("/api/auth/register", json={**account, "accept_terms": True})
    assert client.get("/api/refuges").json()["detail"]["code"] == "account_pending"


def test_bbox_returns_only_visible_refuges(active_client, refuges):
    response = active_client.get("/api/refuges", params={"bbox": ECRINS_BBOX})

    assert response.status_code == 200
    assert response.json()["total"] == 3
    assert names(response) == ["Gîte d'Ailefroide", "Refuge du Glacier Blanc", "Refuge du Pelvoux"]
    first = response.json()["items"][1]
    assert first["massif"] == {"id": first["massif"]["id"], "name": "Écrins"}
    assert first["is_guarded"] is True


def test_guarded_filter_counts_gites_as_guarded(active_client, refuges):
    guarded = active_client.get("/api/refuges", params={"bbox": ECRINS_BBOX, "guarded": "true"})
    unguarded = active_client.get("/api/refuges", params={"bbox": ECRINS_BBOX, "guarded": "false"})

    assert names(guarded) == ["Gîte d'Ailefroide", "Refuge du Glacier Blanc"]
    assert names(unguarded) == ["Refuge du Pelvoux"]


def test_search_ignores_case_and_accents_and_matches_massif(active_client, refuges):
    by_name = active_client.get("/api/refuges", params={"q": "glacier BLANC"})
    by_massif = active_client.get("/api/refuges", params={"q": "ecrins"})
    wildcard = active_client.get("/api/refuges", params={"q": "%%"})

    assert names(by_name) == ["Refuge du Glacier Blanc"]
    assert by_massif.json()["total"] == 3
    assert wildcard.json()["total"] == 0  # « % » est cherché littéralement


def test_limit_truncates_items_but_not_total(active_client, refuges):
    response = active_client.get("/api/refuges", params={"limit": 2})

    assert response.json()["total"] == 4
    assert len(response.json()["items"]) == 2


def test_invalid_bbox_is_rejected(active_client, refuges):
    response = active_client.get("/api/refuges", params={"bbox": "6.5,44.8,6.3"})

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_bbox"


def test_refuge_detail(active_client, refuges):
    response = active_client.get(f"/api/refuges/{refuges['glacier_blanc']}")

    assert response.status_code == 200
    assert response.json()["capacity"] == 135
    assert "access" in response.json()
    assert active_client.get("/api/refuges/999999").status_code == 404


@pytest.mark.parametrize(
    ("owner_info", "phone"),
    [
        ("Téléphone du refuge : 04 92 23 50 24\nGardien 06 83 05 71 04", "04 92 23 50 24"),
        ("Tél. 04.76.80.12.34", "04 76 80 12 34"),
        ("+33 6 12 34 56 78", "06 12 34 56 78"),
        ("Commune de Vallouise", None),
        (None, None),
    ],
)
def test_phone_is_extracted_from_owner_info(owner_info, phone):
    refuge = Refuge(owner_info=owner_info)

    assert refuge.phone == phone


def test_refuge_detail_includes_phone(active_client, refuges):
    response = active_client.get(f"/api/refuges/{refuges['glacier_blanc']}")

    assert response.json()["phone"] is None  # pas de texte « Propriétaires » dans le fixture


def test_massifs_are_sorted_by_name(active_client, refuges):
    response = active_client.get("/api/massifs")

    assert [m["name"] for m in response.json()] == ["Écrins", "Vanoise"]
