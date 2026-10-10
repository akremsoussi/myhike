"""Client de l'API publique refuges.info (lecture seule, sans clé).

Les données de refuges.info sont sous licence CC BY-SA 2.0 : le site doit les citer.
Documentation : https://www.refuges.info/api/doc/
"""

import json
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from typing import Any

from app.models import RefugeKind

SITE_URL = "https://www.refuges.info"
API_URL = f"{SITE_URL}/api"
USER_AGENT = "Refuges-projet-scolaire/0.1 (import ponctuel)"

# Types de points refuges.info importés (identifiants de l'API).
KIND_BY_TYPE_ID = {
    7: RefugeKind.UNGUARDED_HUT,
    9: RefugeKind.GITE,
    10: RefugeKind.GUARDED_HUT,
}
POLYGON_TYPE_MASSIF = 1

# France métropolitaine et massifs frontaliers : ouest, sud, est, nord.
DEFAULT_BBOX = "-5.5,41.3,10.0,51.2"


def _get(path: str, **params: Any) -> dict[str, Any]:
    url = f"{API_URL}/{path}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.load(response)


def fetch_massifs(bbox: str = DEFAULT_BBOX) -> list[dict[str, Any]]:
    """Massifs (polygones de type 1) : [{"external_id", "name"}]."""
    data = _get("polygones", type_polygon=POLYGON_TYPE_MASSIF, bbox=bbox, format="geojson")
    return [
        {"external_id": int(feature["properties"]["id"]), "name": feature["properties"]["nom"]}
        for feature in data["features"]
    ]


def fetch_photos(point_external_id: int) -> list[dict[str, Any]]:
    """Photos des commentaires d'un point, de la plus récente à la plus ancienne.

    [{"external_id", "url", "author", "caption", "taken_at"}] ; les commentaires sans
    photo sont ignorés.
    """
    data = _get("commentaires", id_point=point_external_id, format_texte="texte")
    photos = []
    for key, comment in data.items():
        if not key.isdigit() or not isinstance(comment, dict):
            continue  # « copyright »
        path = comment.get("photo-reduite") or comment.get("photo-originale")
        if not isinstance(path, str) or not path.startswith("/photos_points/"):
            continue
        photos.append(
            {
                "external_id": int(comment["id_commentaire"]),
                "url": SITE_URL + _fix_photo_path(path),
                "author": (comment.get("auteur_commentaire") or "").strip()[:120],
                "caption": " ".join((comment.get("texte_commentaire") or "").split())[:300],
                "taken_at": _date(comment.get("date_commentaire")),
            }
        )
    photos.sort(key=lambda photo: photo["taken_at"] or datetime.min, reverse=True)
    return photos


def _fix_photo_path(path: str) -> str:
    """L'API colle l'empreinte au nom (« 51684-reduite.jpegmd=f9dd0f ») : il manque le « ? »."""
    name, separator, digest = path.partition("md=")
    return f"{name}?md={digest}" if separator and not name.endswith("?") else path


def fetch_image(url: str, max_bytes: int) -> bytes:
    """Contenu d'une image de refuges.info ; ValueError si elle dépasse `max_bytes`."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        data = response.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ValueError("image trop lourde")
    return data


def fetch_massif_points(massif_external_id: int) -> list[dict[str, Any]]:
    """Points GeoJSON d'un massif, avec tous les détails, texte brut."""
    data = _get(
        "massif",
        massif=massif_external_id,
        type_points=",".join(str(type_id) for type_id in KIND_BY_TYPE_ID),
        nb_points="all",
        detail="complet",
        format="geojson",
        format_texte="texte",
    )
    return data["features"]


def _text(field: Any) -> str | None:
    value = field.get("valeur") if isinstance(field, dict) else None
    if not isinstance(value, str):
        return None
    value = value.replace("\r\n", "\n").strip()
    return value or None


def _int(value: Any) -> int | None:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _date(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed.astimezone(UTC).replace(tzinfo=None, microsecond=0)


def parse_point(feature: dict[str, Any]) -> dict[str, Any] | None:
    """Convertit un point GeoJSON de refuges.info en champs de Refuge.

    Renvoie None pour un type non importé ou un bâtiment détruit.
    """
    props = feature["properties"]
    kind = KIND_BY_TYPE_ID.get(props.get("type", {}).get("id"))
    if kind is None:
        return None
    state = _text(props.get("etat"))
    if state and state.lower().startswith("détruit"):
        return None
    longitude, latitude = feature["geometry"]["coordinates"][:2]
    return {
        "external_id": int(props["id"]),
        "name": props["nom"].strip()[:200],
        "kind": kind,
        "latitude": round(float(latitude), 6),
        "longitude": round(float(longitude), 6),
        "altitude": _int(props.get("coord", {}).get("alt")),
        "capacity": _int(props.get("places", {}).get("valeur")),
        "state": state[:80] if state else None,
        "access": _text(props.get("acces")),
        "remarks": _text(props.get("remarque")),
        "owner_info": _text(props.get("proprio")),
        "source_url": (props.get("lien") or None),
        "source_updated_at": _date(props.get("date", {}).get("derniere_modif")),
    }
