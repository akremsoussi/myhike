from pydantic import BaseModel, ConfigDict

from app.models import RefugeKind
from app.schemas.auth import UtcDatetime


class MassifOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class RefugeSummary(BaseModel):
    """Ce qu'il faut pour la carte et la liste (écran 03)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    kind: RefugeKind
    is_guarded: bool
    latitude: float
    longitude: float
    altitude: int | None
    capacity: int | None
    state: str | None
    massif: MassifOut | None


class RefugeDetail(RefugeSummary):
    """Fiche refuge (écran 04). Textes issus de refuges.info (CC BY-SA 2.0)."""

    access: str | None
    remarks: str | None
    owner_info: str | None
    # Extrait de `owner_info` (premier numéro trouvé).
    phone: str | None
    source_url: str | None
    source_updated_at: UtcDatetime | None


class RefugeList(BaseModel):
    # Nombre total de refuges correspondant aux filtres, même si `items` est tronqué.
    total: int
    items: list[RefugeSummary]
