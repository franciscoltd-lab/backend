from email.message import EmailMessage
import smtplib

from app.core.config import settings


def send_password_reset_code(to_email: str, code: str) -> None:
    if not settings.SMTP_HOST or not settings.SMTP_FROM:
        raise RuntimeError("SMTP settings are not configured")

    message = EmailMessage()
    message["Subject"] = "Codigo de recuperacion Quetzart"
    message["From"] = settings.SMTP_FROM
    message["To"] = to_email
    message.set_content(
        "Hola,\n\n"
        f"Tu codigo para recuperar tu contrasena en Quetzart es: {code}\n\n"
        "Este codigo vence en 10 minutos. Si no solicitaste este cambio, ignora este correo.\n"
    )

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:
        if settings.SMTP_USE_TLS:
            smtp.starttls()
        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(message)
