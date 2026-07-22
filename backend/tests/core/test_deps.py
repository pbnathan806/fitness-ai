import asyncio
import uuid

import pytest
from fastapi.security import HTTPAuthorizationCredentials
from fastapi import HTTPException

from core.deps import get_current_user
from core.security import create_access_token


def _credentials(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def test_get_current_user_returns_identity_for_valid_token():
    user_id = uuid.uuid4()
    token = create_access_token(subject=str(user_id))

    current_user = asyncio.run(get_current_user(_credentials(token)))

    assert current_user.user_id == user_id
    assert current_user.active_role is None


def test_get_current_user_includes_active_role_when_present():
    user_id = uuid.uuid4()
    token = create_access_token(subject=str(user_id), active_role="TRAINER")

    current_user = asyncio.run(get_current_user(_credentials(token)))

    assert current_user.active_role == "TRAINER"


def test_get_current_user_rejects_missing_credentials():
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(get_current_user(None))

    assert exc_info.value.status_code == 401


def test_get_current_user_rejects_invalid_token():
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(get_current_user(_credentials("not-a-valid-token")))

    assert exc_info.value.status_code == 401


def test_get_current_user_rejects_token_with_non_uuid_subject():
    token = create_access_token(subject="not-a-uuid")

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(get_current_user(_credentials(token)))

    assert exc_info.value.status_code == 401
