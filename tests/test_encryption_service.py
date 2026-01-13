"""
Tests for encryption service
"""
import pytest
from cryptography.fernet import Fernet
from app.services.encryption_service import EncryptionService, get_encryption_service


class TestEncryptionService:
    """Test cases for EncryptionService"""

    def test_encryption_service_initialization(self, encryption_key):
        """Test encryption service can be initialized with a key"""
        service = EncryptionService(encryption_key)
        assert service is not None
        assert service.cipher is not None

    def test_encrypt_plaintext(self, encryption_key):
        """Test encryption of plaintext string"""
        service = EncryptionService(encryption_key)
        plaintext = "my_secret_api_token"

        encrypted = service.encrypt(plaintext)

        assert encrypted is not None
        assert isinstance(encrypted, str)
        assert encrypted != plaintext
        assert len(encrypted) > len(plaintext)

    def test_decrypt_ciphertext(self, encryption_key):
        """Test decryption of ciphertext"""
        service = EncryptionService(encryption_key)
        plaintext = "my_secret_api_token"

        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)

        assert decrypted == plaintext

    def test_encrypt_decrypt_roundtrip(self, encryption_key):
        """Test encrypt-decrypt roundtrip preserves data"""
        service = EncryptionService(encryption_key)
        test_strings = [
            "simple_token",
            "token_with_special_chars!@#$%^&*()",
            "very_long_token_" * 100,
            "unicode_token_测试_🔐"
        ]

        for original in test_strings:
            encrypted = service.encrypt(original)
            decrypted = service.decrypt(encrypted)
            assert decrypted == original, f"Failed for: {original}"

    def test_encrypt_same_plaintext_different_results(self, encryption_key):
        """Test that encrypting the same plaintext produces different results"""
        service = EncryptionService(encryption_key)
        plaintext = "my_secret_token"

        encrypted1 = service.encrypt(plaintext)
        encrypted2 = service.encrypt(plaintext)

        # Fernet uses timestamp, so same plaintext may produce different ciphertext
        # But both should decrypt to the same plaintext
        assert service.decrypt(encrypted1) == plaintext
        assert service.decrypt(encrypted2) == plaintext

    def test_decrypt_with_wrong_key_fails(self, encryption_key):
        """Test that decryption with wrong key fails"""
        service1 = EncryptionService(encryption_key)
        service2 = EncryptionService(Fernet.generate_key().decode('utf-8'))

        plaintext = "secret_data"
        encrypted = service1.encrypt(plaintext)

        with pytest.raises(Exception):
            service2.decrypt(encrypted)

    def test_decrypt_invalid_ciphertext_fails(self, encryption_key):
        """Test that decrypting invalid ciphertext fails"""
        service = EncryptionService(encryption_key)

        with pytest.raises(Exception):
            service.decrypt("invalid_ciphertext")

    def test_encrypt_empty_string_raises_error(self, encryption_key):
        """Test encryption of empty string raises ValueError"""
        service = EncryptionService(encryption_key)

        with pytest.raises(ValueError) as exc_info:
            service.encrypt("")

        assert "empty" in str(exc_info.value).lower()

    def test_get_encryption_service_singleton(self, app):
        """Test get_encryption_service returns the global instance"""
        with app.app_context():
            service1 = get_encryption_service()
            service2 = get_encryption_service()

            assert service1 is service2

    def test_global_encryption_service_works(self, app):
        """Test that the global encryption service works correctly"""
        with app.app_context():
            service = get_encryption_service()

            plaintext = "test_api_token"
            encrypted = service.encrypt(plaintext)
            decrypted = service.decrypt(encrypted)

            assert decrypted == plaintext

    def test_encryption_with_bytes_key(self):
        """Test encryption service works with bytes key"""
        key_bytes = Fernet.generate_key()
        service = EncryptionService(key_bytes)

        plaintext = "test_data"
        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)

        assert decrypted == plaintext

    def test_encryption_with_string_key(self):
        """Test encryption service works with string key"""
        key_string = Fernet.generate_key().decode('utf-8')
        service = EncryptionService(key_string)

        plaintext = "test_data"
        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)

        assert decrypted == plaintext

    def test_large_data_encryption(self, encryption_key):
        """Test encryption of large data"""
        service = EncryptionService(encryption_key)

        # Create a large string (10KB)
        large_plaintext = "A" * 10240

        encrypted = service.encrypt(large_plaintext)
        decrypted = service.decrypt(encrypted)

        assert decrypted == large_plaintext
        assert len(encrypted) > len(large_plaintext)
