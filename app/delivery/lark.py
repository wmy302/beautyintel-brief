from app.core.config import get_settings
from app.delivery.webhook import WebhookDelivery


class LarkDelivery(WebhookDelivery):
    def __init__(self) -> None:
        super().__init__(get_settings().lark_webhook_url, "lark")

