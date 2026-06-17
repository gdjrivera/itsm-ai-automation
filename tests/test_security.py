from src.core.security import validate_ip


def test_validate_ip_allows_all() -> None:
    assert validate_ip("10.0.0.1") is True


def test_validate_ip_restricted() -> None:
    from src.config.settings import get_settings
    from unittest.mock import patch

    with patch.object(get_settings(), "allowed_ips", "192.168.1.0/24"):
        assert validate_ip("192.168.1.100") is True
        assert validate_ip("10.0.0.1") is False
