from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/.env, quel que soit le dossier depuis lequel on lance l'API.
BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8")

    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "refuges"
    db_user: str = "refuges"
    # Pas de valeur par défaut : l'API refuse de démarrer si le mot de passe manque.
    db_password: str
    # Base utilisée par pytest, jamais la base de développement.
    db_name_test: str = "refuges_test"

    # Adresse du site, pour les liens envoyés par email.
    frontend_url: str = "http://localhost:5173"

    # « console » : l'email est écrit dans les logs de l'API.
    # « smtp » : il est envoyé au serveur SMTP (Mailpit en développement).
    email_backend: Literal["console", "smtp"] = "console"
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    email_from: str = "Refuges <no-reply@refuges.local>"

    # Cookie de session : à passer à true derrière HTTPS.
    cookie_secure: bool = False
    session_days: int = 30

    verification_hours: int = 24
    # Lien « Mot de passe oublié » : court, il permet de prendre la main sur le compte.
    password_reset_minutes: int = 60
    resend_cooldown_seconds: int = 60

    # Images envoyées (photos des posts, bannières et icônes des communautés).
    # Par défaut backend/uploads, ignoré par git. Un chemin relatif part de backend/.
    media_dir: Path = BACKEND_DIR / "uploads"
    upload_max_mb: int = 10

    @field_validator("media_dir")
    @classmethod
    def resolve_media_dir(cls, value: Path) -> Path:
        return value if value.is_absolute() else BACKEND_DIR / value


settings = Settings()
