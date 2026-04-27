"""Tests for security utilities."""
import pytest
from jose import JWTError

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    encrypt_secret,
    decrypt_secret,
)


class TestPasswordHashing:
    def test_hash_password(self):
        hashed = hash_password("mypassword")
        assert hashed != "mypassword"
        assert len(hashed) > 20

    def test_verify_correct_password(self):
        hashed = hash_password("mypassword")
        assert verify_password("mypassword", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("mypassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_different_hashes_for_same_password(self):
        # bcrypt includes salt, so same password should produce different hashes
        hash1 = hash_password("mypassword")
        hash2 = hash_password("mypassword")
        assert hash1 != hash2


class TestTokens:
    def test_create_access_token(self):
        token = create_access_token({"sub": "123"})
        assert isinstance(token, str)
        assert len(token) > 10

    def test_decode_access_token(self):
        token = create_access_token({"sub": "42"})
        payload = decode_token(token)
        assert payload["sub"] == "42"
        assert payload["type"] == "access"

    def test_create_refresh_token(self):
        token = create_refresh_token({"sub": "123"})
        assert isinstance(token, str)

    def test_decode_refresh_token(self):
        token = create_refresh_token({"sub": "99"})
        payload = decode_token(token)
        assert payload["sub"] == "99"
        assert payload["type"] == "refresh"

    def test_invalid_token_raises(self):
        with pytest.raises(JWTError):
            decode_token("invalid.token.here")


class TestEncryption:
    def test_encrypt_decrypt(self):
        secret = "my-api-key-12345"
        encrypted = encrypt_secret(secret)
        assert encrypted != secret
        decrypted = decrypt_secret(encrypted)
        assert decrypted == secret

    def test_encrypted_is_different_each_time(self):
        # Fernet uses random IV, so same plaintext gives different ciphertext
        encrypted1 = encrypt_secret("secret")
        encrypted2 = encrypt_secret("secret")
        assert encrypted1 != encrypted2

    def test_encrypt_empty_string(self):
        encrypted = encrypt_secret("")
        assert decrypt_secret(encrypted) == ""

    def test_decrypt_wrong_key_fails(self):
        encrypted = encrypt_secret("secret")
        # Modify the encrypted value slightly
        with pytest.raises(Exception):
            # Corrupt the encrypted string
            decrypt_secret(encrypted[:10] + "AAAA" + encrypted[14:])
