from datetime import timedelta

import jwt
import pytest

from core.config import settings
from core.security import (
    create_access_token,
    decode_access_token,
    generate_password_reset_token,
    hash_password,
    hash_reset_token,
    verify_password,
)


def test_hash_password_returns_different_value_than_plain_password():
    hashed = hash_password("Str0ngPassword!")

    assert hashed != "Str0ngPassword!"
    assert hashed.startswith("$2b$")


def test_hash_password_generates_unique_salt_per_call():
    hashed_one = hash_password("Str0ngPassword!")
    hashed_two = hash_password("Str0ngPassword!")

    assert hashed_one != hashed_two


def test_verify_password_succeeds_with_correct_password():
    hashed = hash_password("Str0ngPassword!")

    assert verify_password("Str0ngPassword!", hashed) is True


def test_verify_password_fails_with_incorrect_password():
    hashed = hash_password("Str0ngPassword!")

    assert verify_password("WrongPassword!", hashed) is False


def test_verify_password_fails_with_malformed_hash():
    assert verify_password("Str0ngPassword!", "not-a-valid-hash") is False


def test_verify_password_fails_with_empty_inputs():
    hashed = hash_password("Str0ngPassword!")

    assert verify_password("", hashed) is False
    assert verify_password("Str0ngPassword!", "") is False


def test_hash_password_rejects_empty_password():
    with pytest.raises(ValueError):
        hash_password("")


def test_hash_password_rejects_password_over_72_bytes():
    with pytest.raises(ValueError):
        hash_password("a" * 73)


def test_create_access_token_returns_decodable_jwt():
    token = create_access_token(subject="user-123")

    payload = jwt.decode(
        token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
    )
    assert payload["sub"] == "user-123"
    assert "iat" in payload
    assert "exp" in payload


def test_create_access_token_rejects_empty_subject():
    with pytest.raises(ValueError):
        create_access_token(subject="")


def test_create_access_token_uses_default_expiry_when_not_provided():
    token = create_access_token(subject="user-123")

    payload = jwt.decode(
        token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
    )
    expected_seconds = settings.jwt_access_token_expire_minutes * 60
    assert payload["exp"] - payload["iat"] == expected_seconds


def test_create_access_token_honors_custom_expires_delta():
    token = create_access_token(
        subject="user-123", expires_delta=timedelta(minutes=5)
    )

    payload = jwt.decode(
        token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
    )
    assert payload["exp"] - payload["iat"] == 5 * 60


def test_decode_access_token_returns_original_claims():
    token = create_access_token(subject="user-123")

    payload = decode_access_token(token)

    assert payload["sub"] == "user-123"


def test_decode_access_token_rejects_empty_token():
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token("")


def test_decode_access_token_rejects_tampered_token():
    token = create_access_token(subject="user-123")

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(token + "tampered")


def test_decode_access_token_rejects_wrong_signature():
    token = jwt.encode(
        {"sub": "user-123"}, "a-different-secret-key", algorithm=settings.jwt_algorithm
    )

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(token)


def test_decode_access_token_raises_on_expired_token():
    expired_token = create_access_token(
        subject="user-123", expires_delta=timedelta(seconds=-1)
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(expired_token)


def test_generate_password_reset_token_returns_unique_high_entropy_values():
    token_one = generate_password_reset_token()
    token_two = generate_password_reset_token()

    assert token_one != token_two
    assert len(token_one) >= 32


def test_hash_reset_token_is_deterministic():
    token = generate_password_reset_token()

    assert hash_reset_token(token) == hash_reset_token(token)


def test_hash_reset_token_differs_from_raw_token():
    token = generate_password_reset_token()

    assert hash_reset_token(token) != token


def test_hash_reset_token_rejects_empty_token():
    with pytest.raises(ValueError):
        hash_reset_token("")
