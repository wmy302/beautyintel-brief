from dataclasses import dataclass


@dataclass
class DeliveryResult:
    channel: str
    status: str
    message: str = ""


class DeliveryService:
    channel = "base"

    def send(self, markdown_content: str, html_content: str, title: str, dry_run: bool = False) -> DeliveryResult:
        raise NotImplementedError

