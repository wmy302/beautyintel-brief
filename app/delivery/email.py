import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import get_settings
from app.delivery.base import DeliveryResult, DeliveryService

logger = logging.getLogger(__name__)


class EmailDelivery(DeliveryService):
    channel = "email"

    def send(self, markdown_content: str, html_content: str, title: str, dry_run: bool = False) -> DeliveryResult:
        settings = get_settings()
        if dry_run:
            return DeliveryResult(self.channel, "dry_run", "email skipped by dry-run")
        required = [settings.smtp_host, settings.email_from, settings.email_to]
        if not all(required):
            return DeliveryResult(self.channel, "skipped", "smtp/email env not configured")
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = title
            msg["From"] = settings.email_from or ""
            msg["To"] = settings.email_to or ""
            msg.attach(MIMEText(markdown_content, "plain", "utf-8"))
            msg.attach(MIMEText(html_content, "html", "utf-8"))
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
                smtp.starttls()
                if settings.smtp_user and settings.smtp_password:
                    smtp.login(settings.smtp_user, settings.smtp_password)
                smtp.sendmail(settings.email_from, [settings.email_to], msg.as_string())
            return DeliveryResult(self.channel, "sent", "email sent")
        except Exception as exc:  # noqa: BLE001
            logger.exception("email_delivery_failed")
            return DeliveryResult(self.channel, "failed", str(exc))

