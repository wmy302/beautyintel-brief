from app.core.config import get_settings
from app.delivery.webhook import WebhookDelivery


class SlackDelivery(WebhookDelivery):
    def __init__(self) -> None:
        super().__init__(get_settings().slack_webhook_url, "slack")

