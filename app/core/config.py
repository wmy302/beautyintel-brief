from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/beautyintel.db"
    brief_timezone: str = "Asia/Shanghai"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    lark_webhook_url: str | None = None
    slack_webhook_url: str | None = None
    generic_webhook_url: str | None = None
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    email_from: str | None = None
    email_to: str | None = None
    ingest_cron: str = "30 7 * * *"
    process_cron: str = "0 8 * * *"
    deliver_cron: str = "30 8 * * *"
    enable_background_scheduler: bool = False
    xhs_search_api_url: str | None = None
    xhs_search_api_token: str | None = None
    xhs_search_keywords: str = "美妆,护肤,彩妆,香水,防晒,小红书美妆"
    xhs_search_page_size: int = 20

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def root_path(*parts: str) -> Path:
    return ROOT_DIR.joinpath(*parts)
