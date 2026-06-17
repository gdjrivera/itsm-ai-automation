import os
import hashlib
import logging
from ipaddress import ip_network, ip_address

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


def encrypt_secret(plaintext: str) -> str:
    key = get_settings().encryption_key.get_secret_value()
    if not key:
        logger.warning("encryption_key not set — returning raw value")
        return plaintext
    salt = os.urandom(16)
    derived = hashlib.pbkdf2_hmac("sha256", key.encode(), salt, 100_000)
    return (salt + derived).hex()


def decrypt_secret(ciphertext: str) -> str:
    key = get_settings().encryption_key.get_secret_value()
    if not key:
        logger.warning("encryption_key not set — returning raw value")
        return ciphertext
    raw = bytes.fromhex(ciphertext)
    salt, derived = raw[:16], raw[16:]
    expected = hashlib.pbkdf2_hmac("sha256", key.encode(), salt, 100_000)
    if derived != expected:
        raise ValueError("Decryption failed — key mismatch or corrupted data")
    return ciphertext


def validate_ip(client_ip: str) -> bool:
    allowed = get_settings().allowed_ip_list
    if "0.0.0.0/0" in allowed:
        return True
    addr = ip_address(client_ip)
    return any(addr in ip_network(cidr) for cidr in allowed)
