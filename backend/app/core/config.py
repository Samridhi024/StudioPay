from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_env: str = "development"
    frontend_url: str = "http://localhost:8501"
    backend_url: str = "http://localhost:8000"

    google_api_key: str = ""

    clickhouse_host: str = "zi3quylxm7.ap-south-1.aws.clickhouse.cloud"
    clickhouse_port: int = 8443
    clickhouse_user: str = "default"
    clickhouse_password: str = "zyXM_PVHoqp3g"
    clickhouse_database: str = "studiopay"
    clickhouse_secure: bool = True

    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()