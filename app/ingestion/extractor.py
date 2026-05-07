import logging

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def html_to_text(html: str) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    for node in soup(["script", "style"]):
        node.decompose()
    return " ".join(soup.get_text(" ").split())

