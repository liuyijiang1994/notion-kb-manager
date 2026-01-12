"""
Encryption service for secure storage of sensitive data
Uses Fernet symmetric encryption from cryptography library
"""
from cryptography.fernet import Fernet, InvalidToken
from typing import Optional
import logging
import os

logger = logging.getLogger(__name__)


class EncryptionService:
    """
    Service for encrypting and decrypting sensitive data

    Uses Fernet symmetric encryption which guarantees that a message encrypted
    using it cannot be manipulated or read without the key.
    """

    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize encryption service

        Args:
            encryption_key: Base64-encoded Fernet key. If None, reads from environment

        Raises:
            ValueError: If encryption key is not provided or invalid
        """
        key = encryption_key or os.getenv('ENCRYPTION_KEY')

        if not key:
            raise ValueError(
                "Encryption key not provided. Generate one with: "
                "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
            )

        try:
            self.cipher = Fernet(key.encode() if isinstance(key, str) else key)
            logger.info("Encryption service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize encryption service: {e}")
            raise ValueError(f"Invalid encryption key: {e}")

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a string

        Args:
            plaintext: String to encrypt

        Returns:
            Base64-encoded encrypted string

        Raises:
            ValueError: If plaintext is empty or encryption fails
        """
        if not plaintext:
            raise ValueError("Cannot encrypt empty string")

        try:
            encrypted_bytes = self.cipher.encrypt(plaintext.encode('utf-8'))
            encrypted_str = encrypted_bytes.decode('utf-8')
            logger.debug("Data encrypted successfully")
            return encrypted_str
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise ValueError(f"Encryption failed: {e}")

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt a string

        Args:
            ciphertext: Base64-encoded encrypted string

        Returns:
            Decrypted plaintext string

        Raises:
            ValueError: If ciphertext is empty, invalid, or decryption fails
        """
        if not ciphertext:
            raise ValueError("Cannot decrypt empty string")

        try:
            decrypted_bytes = self.cipher.decrypt(ciphertext.encode('utf-8'))
            decrypted_str = decrypted_bytes.decode('utf-8')
            logger.debug("Data decrypted successfully")
            return decrypted_str
        except InvalidToken:
            logger.error("Decryption failed: Invalid token or key")
            raise ValueError("Decryption failed: Invalid or corrupted data")
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise ValueError(f"Decryption failed: {e}")

    @staticmethod
    def generate_key() -> str:
        """
        Generate a new Fernet encryption key

        Returns:
            Base64-encoded encryption key as string
        """
        key = Fernet.generate_key()
        return key.decode('utf-8')


# Global instance (initialized in app factory)
encryption_service: Optional[EncryptionService] = None


def get_encryption_service() -> EncryptionService:
    """Get the global encryption service instance"""
    if encryption_service is None:
        raise RuntimeError("Encryption service not initialized. Call init_app() first.")
    return encryption_service


def init_app(app):
    """Initialize encryption service with Flask app"""
    global encryption_service
    encryption_service = EncryptionService(app.config.get('ENCRYPTION_KEY'))
    logger.info("Encryption service initialized for application")
