from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: Literal["development", "test", "staging", "production"] = "development"
    app_base_url: str = "http://localhost:3000"
    api_base_url: str = "http://localhost:8000"
    cors_origins: str = "http://localhost:3000"

    database_url: str = "sqlite+pysqlite:///./data/recovra.db"
    test_database_url: str | None = None

    session_secret: str = Field(default="dev-only-change-me-32-chars-min!!", min_length=16)
    session_cookie_name: str = "recovra_session"
    session_max_age_seconds: int = 604800
    session_secure_cookie: bool = False

    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_tls: bool = False
    smtp_from_name: str = "Recovra"
    smtp_from_email: str = "noreply@recovra.test"

    pdf_max_files: int = 10
    pdf_max_bytes: int = 10_485_760
    pdf_max_pages: int = 10
    upload_storage_dir: str = "./data/uploads"

    invitation_expiry_hours: int = 72

    @field_validator("session_secure_cookie", mode="before")
    @classmethod
    def default_secure_cookie(cls, v, info):
        if v is not None and v != "":
            return bool(v) if not isinstance(v, str) else v.lower() in ("1", "true", "yes")
        data = info.data if hasattr(info, "data") else {}
        return data.get("app_env") == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    def validate_mail_config(self) -> None:
        if self.app_env == "production":
            if self.smtp_host in ("localhost", "127.0.0.1", "mailpit"):
                raise RuntimeError("Production must not use Mailpit or localhost SMTP")
            if not self.app_base_url.startswith("https://"):
                raise RuntimeError("Production APP_BASE_URL must be HTTPS")

    def is_test_recipient_allowed(self, email: str) -> bool:
        if self.app_env in ("development", "test"):
            return True
        domain = email.rsplit("@", 1)[-1].lower()
        return domain != "test"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()  # type: ignore[call-arg]
    if settings.app_env == "production":
        settings.validate_mail_config()
    return settings