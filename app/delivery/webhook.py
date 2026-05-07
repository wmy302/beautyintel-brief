import logging

import httpx

from app.delivery.base import DeliveryResult, DeliveryService

logger = logging.getLogger(__name__)


class WebhookDelivery(DeliveryService):
    channel = "webhook"

    def __init__(self, url: str | None, channel: str = "webhook") -> None:
        self.url = url
        self.channel = channel

    def send(self, markdown_content: str, html_content: str, title: str, dry_run: bool = False) -> DeliveryResult:
        if dry_run:
            return DeliveryResult(self.channel, "dry_run", "push skipped by dry-run")
        if not self.url:
            return DeliveryResult(self.channel, "skipped", "webhook url not configured")
        try:
            resp = httpx.post(self.url, json={"title": title, "markdown": markdown_content}, timeout=10)
            resp.raise_for_status()
            return DeliveryResult(self.channel, "sent", f"http {resp.status_code}")
        except Exception as exc:  # noqa: BLE001
            logger.exception("webhook_delivery_failed channel=%s", self.channel)
            return DeliveryResult(self.channel, "failed", str(exc))

