import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from app.core.config import root_path


def load_yaml(path: str | Path) -> dict[str, Any]:
    full_path = Path(path)
    if not full_path.is_absolute():
        full_path = root_path(str(full_path))
    with full_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def dumps(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False)


def loads_list(value: str | None) -> list[Any]:
    if not value:
        return []
    try:
        data = json.loads(value)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            dt = datetime.strptime(value, "%Y-%m-%d")
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

