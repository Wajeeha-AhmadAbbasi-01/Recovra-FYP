import smtplib
from email.message import EmailMessage

from app.core.config import Settings


def send_invitation_email(settings: Settings, *, to_email: str, invite_url: str) -> None:
    if not settings.is_test_recipient_allowed(to_email):
        raise ValueError("Recipient not allowed in this environment")

    message = EmailMessage()
    message["Subject"] = "You're invited to Recovra"
    message["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
    message["To"] = to_email
    message.set_content(
        f"You have been invited to join a Recovra workspace.\n\n"
        f"Open this link to accept (single use):\n{invite_url}\n\n"
        f"If you did not expect this invitation, ignore this email."
    )

    if settings.smtp_tls:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
            smtp.starttls()
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(message)
    else:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(message)