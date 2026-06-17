from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr, computed_field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── ITSM Connectors ──────────────────────────────────────────
    freshservice_domain: str = ""
    freshservice_api_key: SecretStr = Field(default=SecretStr(""))
    freshservice_page_size: int = 50

    zendesk_domain: str = ""
    zendesk_email: str = ""
    zendesk_api_token: SecretStr = Field(default=SecretStr(""))
    zendesk_page_size: int = 50

    # ── AI / Ollama ──────────────────────────────────────────────
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    ollama_timeout: int = 120

    # ── Workers (RQ / Redis) ─────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    worker_queue: str = "itsm-tickets"
    worker_max_retries: int = 3

    # ── Core ─────────────────────────────────────────────────────
    log_level: str = "INFO"
    log_format: str = "json"

    # ── Security ─────────────────────────────────────────────────
    encryption_key: SecretStr = Field(default=SecretStr(""))
    allowed_ips: str = "0.0.0.0/0"

    @computed_field
    @property
    def allowed_ip_list(self) -> list[str]:
        return [ip.strip() for ip in self.allowed_ips.split(",") if ip.strip()]

    @property
    def freshservice_base_url(self) -> str:
        return f"https://{self.freshservice_domain}.freshservice.com"

    @property
    def zendesk_base_url(self) -> str:
        return f"https://{self.zendesk_domain}.zendesk.com"


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
