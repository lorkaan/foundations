from base.fields import SensitiveFieldMixin
from encryption.services import decrypt_value, encrypt_value


class EncryptedFieldMixin(SensitiveFieldMixin):
    
    def get_prep_value(self, value):
        value = super().get_prep_value(value)

        if value is None or not self.encrypt:
            return value

        # Normalize to bytes
        if isinstance(value, str):
            value = value.encode()

        encrypted = encrypt_value(value)

        # Store as hex or base64 (hex for simplicity)
        return encrypted.hex()

    def from_db_value(self, value, expression, connection):
        if value is None or not self.encrypt:
            return value

        decrypted = decrypt_value(bytes.fromhex(value))

        try:
            return decrypted.decode()
        except Exception:
            return decrypted