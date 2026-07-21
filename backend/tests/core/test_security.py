import pytest

from core.security import hash_password, verify_password


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
