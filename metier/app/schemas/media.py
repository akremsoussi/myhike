from typing import Literal

from pydantic import BaseModel, ConfigDict

# photo : photo d'un post ; banner / icon : visuels d'une communauté (écran 15).
UploadKind = Literal["photo", "banner", "icon"]


class PhotoOut(BaseModel):
    """Image affichable : `url` n'est servie qu'à ceux qui ont le droit de la voir."""

    model_config = ConfigDict(from_attributes=True)

    url: str
    width: int
    height: int


class UploadOut(PhotoOut):
    """Image tout juste envoyée : `id` sert à la rattacher (post ou communauté)."""

    id: int
