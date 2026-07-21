from django.conf import settings
from backends.services import get_backend


def get_encryption_backend():
    config = getattr(settings, "ENCRYPTION_BACKEND", {
        "name": "local_aes256",
        "config": {}
    })

    return get_backend(
        config["name"],
        **config.get("config", {})
    )


def encrypt_value(value: bytes) -> bytes:
    backend = get_encryption_backend()
    return backend.encrypt(value)


def decrypt_value(value: bytes) -> bytes:
    backend = get_encryption_backend()
    return backend.decrypt(value)