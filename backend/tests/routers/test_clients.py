import uuid

from fastapi.testclient import TestClient

from core.constants import RoleName
from core.deps import CurrentUser, get_current_user
from main import app
from routers.clients import get_client_repository, get_role_repository, get_user_repository
from tests.services.test_client_service import (
    FakeClientRepository,
    FakeRoleRepository,
    FakeUserRepository,
    _make_client,
)


def _override_dependencies(
    client_repository: FakeClientRepository,
    user_repository: FakeUserRepository,
    role_repository: FakeRoleRepository,
    user_id: uuid.UUID,
    active_role: str | None,
) -> None:
    app.dependency_overrides[get_client_repository] = lambda: client_repository
    app.dependency_overrides[get_user_repository] = lambda: user_repository
    app.dependency_overrides[get_role_repository] = lambda: role_repository
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        user_id=user_id, active_role=active_role
    )


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_create_client_succeeds_for_super_admin():
    client_repository = FakeClientRepository()
    user_repository = FakeUserRepository()
    role_repository = FakeRoleRepository()
    _override_dependencies(
        client_repository, user_repository, role_repository, uuid.uuid4(), RoleName.SUPER_ADMIN
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/clients",
        json={
            "email": "client@example.com",
            "password": "Str0ngPassword!",
            "first_name": "Jane",
            "last_name": "Doe",
            "phone_number": "+1-555-0100",
            "timezone": "America/New_York",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "client@example.com"
    assert body["first_name"] == "Jane"
    assert "password" not in body


def test_create_client_rejects_trainer():
    client_repository = FakeClientRepository()
    user_repository = FakeUserRepository()
    role_repository = FakeRoleRepository()
    _override_dependencies(
        client_repository, user_repository, role_repository, uuid.uuid4(), RoleName.TRAINER
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/clients",
        json={
            "email": "client@example.com",
            "password": "Str0ngPassword!",
            "first_name": "Jane",
            "last_name": "Doe",
            "timezone": "America/New_York",
        },
    )

    assert response.status_code == 403


def test_create_client_rejects_invalid_timezone():
    client_repository = FakeClientRepository()
    user_repository = FakeUserRepository()
    role_repository = FakeRoleRepository()
    _override_dependencies(
        client_repository, user_repository, role_repository, uuid.uuid4(), RoleName.SUPER_ADMIN
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/clients",
        json={
            "email": "client@example.com",
            "password": "Str0ngPassword!",
            "first_name": "Jane",
            "last_name": "Doe",
            "timezone": "Not/AZone",
        },
    )

    assert response.status_code == 422


def test_create_client_requires_authentication():
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/clients",
        json={
            "email": "client@example.com",
            "password": "Str0ngPassword!",
            "first_name": "Jane",
            "last_name": "Doe",
            "timezone": "America/New_York",
        },
    )

    assert response.status_code == 401


def test_get_client_succeeds_for_super_admin():
    client_repository = FakeClientRepository()
    client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    user_repository = FakeUserRepository()
    role_repository = FakeRoleRepository()
    _override_dependencies(
        client_repository, user_repository, role_repository, uuid.uuid4(), RoleName.SUPER_ADMIN
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/clients/{client.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(client.id)


def test_get_client_succeeds_for_owning_client():
    client_repository = FakeClientRepository()
    user_id = uuid.uuid4()
    client = _make_client(user_id=user_id)
    client_repository.seed(client, "client@example.com")
    user_repository = FakeUserRepository()
    role_repository = FakeRoleRepository()
    _override_dependencies(
        client_repository, user_repository, role_repository, user_id, RoleName.CLIENT
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/clients/{client.id}")

    assert response.status_code == 200


def test_get_client_rejects_other_client():
    client_repository = FakeClientRepository()
    client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    user_repository = FakeUserRepository()
    role_repository = FakeRoleRepository()
    _override_dependencies(
        client_repository, user_repository, role_repository, uuid.uuid4(), RoleName.CLIENT
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/clients/{client.id}")

    assert response.status_code == 403


def test_get_client_rejects_trainer():
    client_repository = FakeClientRepository()
    client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    user_repository = FakeUserRepository()
    role_repository = FakeRoleRepository()
    _override_dependencies(
        client_repository, user_repository, role_repository, uuid.uuid4(), RoleName.TRAINER
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/clients/{client.id}")

    assert response.status_code == 403


def test_get_client_returns_404_for_missing_client():
    client_repository = FakeClientRepository()
    user_repository = FakeUserRepository()
    role_repository = FakeRoleRepository()
    _override_dependencies(
        client_repository, user_repository, role_repository, uuid.uuid4(), RoleName.SUPER_ADMIN
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/clients/{uuid.uuid4()}")

    assert response.status_code == 404


def test_get_client_rejects_invalid_uuid():
    client_repository = FakeClientRepository()
    user_repository = FakeUserRepository()
    role_repository = FakeRoleRepository()
    _override_dependencies(
        client_repository, user_repository, role_repository, uuid.uuid4(), RoleName.SUPER_ADMIN
    )
    test_client = TestClient(app)

    response = test_client.get("/api/v1/clients/not-a-uuid")

    assert response.status_code == 422


def test_update_client_succeeds_for_owning_client():
    client_repository = FakeClientRepository()
    user_id = uuid.uuid4()
    client = _make_client(user_id=user_id, first_name="Jane")
    client_repository.seed(client, "client@example.com")
    user_repository = FakeUserRepository()
    role_repository = FakeRoleRepository()
    _override_dependencies(
        client_repository, user_repository, role_repository, user_id, RoleName.CLIENT
    )
    test_client = TestClient(app)

    response = test_client.put(
        f"/api/v1/clients/{client.id}", json={"first_name": "Janet"}
    )

    assert response.status_code == 200
    assert response.json()["first_name"] == "Janet"


def test_update_client_rejects_other_client():
    client_repository = FakeClientRepository()
    client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    user_repository = FakeUserRepository()
    role_repository = FakeRoleRepository()
    _override_dependencies(
        client_repository, user_repository, role_repository, uuid.uuid4(), RoleName.CLIENT
    )
    test_client = TestClient(app)

    response = test_client.put(
        f"/api/v1/clients/{client.id}", json={"first_name": "Hacker"}
    )

    assert response.status_code == 403


def test_update_client_rejects_empty_body():
    client_repository = FakeClientRepository()
    client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    user_repository = FakeUserRepository()
    role_repository = FakeRoleRepository()
    _override_dependencies(
        client_repository, user_repository, role_repository, uuid.uuid4(), RoleName.SUPER_ADMIN
    )
    test_client = TestClient(app)

    response = test_client.put(f"/api/v1/clients/{client.id}", json={})

    assert response.status_code == 422


def test_list_clients_succeeds_for_super_admin_with_pagination():
    client_repository = FakeClientRepository()
    for _ in range(3):
        client_repository.seed(_make_client(user_id=uuid.uuid4()), "client@example.com")
    user_repository = FakeUserRepository()
    role_repository = FakeRoleRepository()
    _override_dependencies(
        client_repository, user_repository, role_repository, uuid.uuid4(), RoleName.SUPER_ADMIN
    )
    test_client = TestClient(app)

    response = test_client.get("/api/v1/clients?page=1&page_size=2")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["total_pages"] == 2


def test_list_clients_rejects_client_role():
    client_repository = FakeClientRepository()
    user_repository = FakeUserRepository()
    role_repository = FakeRoleRepository()
    _override_dependencies(
        client_repository, user_repository, role_repository, uuid.uuid4(), RoleName.CLIENT
    )
    test_client = TestClient(app)

    response = test_client.get("/api/v1/clients")

    assert response.status_code == 403


def test_list_clients_rejects_trainer_role():
    client_repository = FakeClientRepository()
    user_repository = FakeUserRepository()
    role_repository = FakeRoleRepository()
    _override_dependencies(
        client_repository, user_repository, role_repository, uuid.uuid4(), RoleName.TRAINER
    )
    test_client = TestClient(app)

    response = test_client.get("/api/v1/clients")

    assert response.status_code == 403


def test_list_clients_requires_authentication():
    test_client = TestClient(app)

    response = test_client.get("/api/v1/clients")

    assert response.status_code == 401


def test_list_clients_rejects_invalid_pagination():
    client_repository = FakeClientRepository()
    user_repository = FakeUserRepository()
    role_repository = FakeRoleRepository()
    _override_dependencies(
        client_repository, user_repository, role_repository, uuid.uuid4(), RoleName.SUPER_ADMIN
    )
    test_client = TestClient(app)

    response = test_client.get("/api/v1/clients?page=0")

    assert response.status_code == 422
