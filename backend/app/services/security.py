import hashlib
import secrets

from pwdlib import PasswordHash

# Argon2id avec les paramètres recommandés par pwdlib.
_hasher = PasswordHash.recommended()
# Empreinte d'un mot de passe quelconque : vérifiée quand l'email est inconnu, pour que la
# réponse prenne le même temps qu'avec un vrai compte.
_DUMMY_HASH = _hasher.hash("mot de passe factice")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    if password_hash is None:
        _hasher.verify(password, _DUMMY_HASH)
        return False
    return _hasher.verify(password, password_hash)


def new_token() -> tuple[str, str]:
    """Jeton aléatoire à envoyer, et son empreinte à stocker."""
    token = secrets.token_urlsafe(32)
    return token, hash_token(token)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
