import os
from cryptography.fernet import Fernet, InvalidToken

_fernet = None


def _get_fernet():
    global _fernet
    if _fernet is None:
        key = os.environ.get('ENCRYPTION_KEY')
        if not key:
            # Use a fixed dev key so tests and local dev work without env var
            key = Fernet.generate_key().decode()
        _fernet = Fernet(key.encode() if isinstance(key, str) else key)
    return _fernet


def encrypt_value(value: str) -> str:
    if not value:
        return value
    return _get_fernet().encrypt(value.encode()).decode()


def decrypt_value(value: str) -> str:
    if not value:
        return value
    try:
        return _get_fernet().decrypt(value.encode()).decode()
    except InvalidToken:
        return value
