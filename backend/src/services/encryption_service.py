from typing import Optional
import keyring
from cryptography.fernet import Fernet

from src.core.config import get_app_settings


class EncryptionService:
    """Service for securing and managing API keys using Fernet symmetric encryption

    and the OS keyring vault for master key management.
    """

    def __init__(self, app_name: Optional[str] = None):
        self.app_name = app_name or get_app_settings().APP_NAME

        # Try to fetch the existing master key from the OS vault
        master_key = keyring.get_password(self.app_name, "master_encryption_key")

        # If it's the first run, generate a secure key and save it to the OS
        if not master_key:
            master_key = Fernet.generate_key().decode()
            keyring.set_password(self.app_name, "master_encryption_key", master_key)

        self._fernet = Fernet(master_key.encode())

    def encrypt_api_key(self, plain_key: str) -> str:
        """Encrypts a plaintext API key string into a base64-encoded encrypted token."""
        return self._fernet.encrypt(plain_key.encode()).decode()

    def decrypt_api_key(self, encrypted_key: str) -> str:
        """Decrypts a Fernet encrypted token back into the original plaintext API key."""
        return self._fernet.decrypt(encrypted_key.encode()).decode()
