from pathlib import Path

from app.core.config import root_path


def load_prompt(name: str) -> str:
    path = root_path("prompts", name)
    return Path(path).read_text(encoding="utf-8")

