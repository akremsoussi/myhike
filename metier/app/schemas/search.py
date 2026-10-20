from pydantic import BaseModel

from app.schemas.communities import AuthorOut, CommunityOut, PostOut
from app.schemas.outings import OutingSummary
from app.schemas.refuges import RefugeSummary


class SearchOut(BaseModel):
    """Résultats de la recherche globale (barre de navigation), par catégorie."""

    refuges: list[RefugeSummary]
    communities: list[CommunityOut]
    users: list[AuthorOut]
    outings: list[OutingSummary]
    posts: list[PostOut]
