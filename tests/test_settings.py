from pydantic import SecretStr

from src.config.settings import Settings


def test_settings_defaults() -> None:
    s = Settings()
    assert s.ollama_base_url == "http://localhost:11434"
    assert s.ollama_model == "llama3"
    assert s.log_level == "INFO"
    assert s.freshservice_base_url == "https://.freshservice.com"
    assert s.zendesk_base_url == "https://.zendesk.com"


def test_settings_freshservice_url() -> None:
    s = Settings(freshservice_domain="mycompany")
    assert s.freshservice_base_url == "https://mycompany.freshservice.com"


def test_secret_str() -> None:
    s = Settings(freshservice_api_key=SecretStr("supersecret"))
    assert s.freshservice_api_key.get_secret_value() == "supersecret"
    # Ensure it's not printed in repr
    assert "supersecret" not in repr(s)
