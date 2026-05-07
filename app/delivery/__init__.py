from app.core.config import get_settings
from app.delivery.email import EmailDelivery
from app.delivery.lark import LarkDelivery
from app.delivery.slack import SlackDelivery
from app.delivery.webhook import WebhookDelivery


def get_delivery_services(channels: list[str] | None = None):
    settings = get_settings()
    all_services = {
        "lark": LarkDelivery(),
        "slack": SlackDelivery(),
        "email": EmailDelivery(),
        "webhook": WebhookDelivery(settings.generic_webhook_url, "webhook"),
    }
    selected = channels or list(all_services)
    return [all_services[ch] for ch in selected if ch in all_services]
