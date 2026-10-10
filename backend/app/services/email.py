import logging
import smtplib
from email.message import EmailMessage

from app.config import settings

logger = logging.getLogger("refuges.email")


def send_email(to: str, subject: str, body: str) -> None:
    """Envoie un email texte. En développement (EMAIL_BACKEND=console), l'écrit dans les logs."""
    if settings.email_backend == "console":
        logger.warning("Email pour %s — %s\n%s", to, subject, body)
        return

    message = EmailMessage()
    message["From"] = settings.email_from
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            smtp.send_message(message)
    except OSError:
        # Tâche de fond : l'utilisateur peut toujours cliquer sur « Renvoyer l'email ».
        logger.exception("Envoi de l'email à %s impossible", to)


def send_verification_email(to: str, display_name: str, token: str) -> None:
    link = f"{settings.frontend_url}/inscription/confirmer?token={token}"
    send_email(
        to,
        "Confirmez votre adresse email",
        f"Bonjour {display_name},\n\n"
        f"Pour activer votre compte Refuges, ouvrez ce lien :\n{link}\n\n"
        f"Il expire dans {settings.verification_hours} h. "
        "Si vous n'avez pas créé de compte, ignorez cet email.\n",
    )


def send_password_reset_email(to: str, display_name: str, token: str) -> None:
    link = f"{settings.frontend_url}/mot-de-passe/nouveau?token={token}"
    send_email(
        to,
        "Choisissez un nouveau mot de passe",
        f"Bonjour {display_name},\n\n"
        f"Pour choisir un nouveau mot de passe Refuges, ouvrez ce lien :\n{link}\n\n"
        f"Il expire dans {settings.password_reset_minutes} min et ne sert qu'une fois. "
        "Si vous n'avez rien demandé, ignorez cet email : votre mot de passe ne change pas.\n",
    )
