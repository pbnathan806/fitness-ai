import uuid

from fastapi.testclient import TestClient

from core.constants import RoleName
from core.deps import CurrentUser, get_current_user
from main import app
from routers.clients import (
    get_assignment_repository,
    get_client_repository,
    get_role_repository,
    get_user_repository,
)
from tests.services.test_client_service import (
    FakeAssignmentRepository,
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
    assignment_repository: FakeAssignmentRepository | None = None,
) -> None:
    app.dependency_overrides[get_client_repository] = lambda: client_repository
    app.dependency_overrides[get_user_repository] = lambda: user_repository
    app.dependency_overrides[get_role_repository] = lambda: role_repository
    app.dependency_overrides[get_assignment_repository] = lambda: (
        assignment_repository or FakeAssignmentRepository()
    )
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


def test_get_client_succeeds_for_assigned_trainer():
    client_repository = FakeClientRepository()
    client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    trainer_user_id = uuid.uuid4()
    trainer_id = uuid.uuid4()
    assignment_repository = FakeAssignmentRepository()
    assignment_repository.set_trainer(trainer_user_id, trainer_id)
    client_repository.assign(trainer_id, client.id)
    user_repository = FakeUserRepository()
    role_repository = FakeRoleRepository()
    _override_dependencies(
        client_repository,
        user_repository,
        role_repository,
        trainer_user_id,
        RoleName.TRAINER,
        assignment_repository,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/clients/{client.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(client.id)


def test_get_client_rejects_unassigned_trainer():
    client_repository = FakeClientRepository()
    client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    trainer_user_id = uuid.uuid4()
    trainer_id = uuid.uuid4()
    assignment_repository = FakeAssignmentRepository()
    assignment_repository.set_trainer(trainer_user_id, trainer_id)
    user_repository = FakeUserRepository()
    role_repository = FakeRoleRepository()
    _override_dependencies(
        client_repository,
        user_repository,
        role_repository,
        trainer_user_id,
        RoleName.TRAINER,
        assignment_repository,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/clients/{client.id}")

    assert response.status_code == 403


def test_get_client_rejects_client_role():
    """Task-15.4: CLIENT users SHALL NOT use GET /clients/{id}, even for their own profile."""
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


def test_update_client_succeeds_for_super_admin():
    client_repository = FakeClientRepository()
    client = _make_client(user_id=uuid.uuid4(), first_name="Jane")
    client_repository.seed(client, "client@example.com")
    user_repository = FakeUserRepository()
    role_repository = FakeRoleRepository()
    _override_dependencies(
        client_repository, user_repository, role_repository, uuid.uuid4(), RoleName.SUPER_ADMIN
    )
    test_client = TestClient(app)

    response = test_client.put(
        f"/api/v1/clients/{client.id}", json={"first_name": "Janet"}
    )

    assert response.status_code == 200
    assert response.json()["first_name"] == "Janet"


def test_update_client_rejects_client_role():
    """Task-15.4: CLIENT must use PUT /clients/me instead of PUT /clients/{id}."""
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

    response = test_client.put(
        f"/api/v1/clients/{client.id}", json={"first_name": "Hacker"}
    )

    assert response.status_code == 403


def test_update_client_rejects_trainer_role():
    """Trainers remain READ-ONLY in Version-1, even for assigned clients."""
    client_repository = FakeClientRepository()
    client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    trainer_user_id = uuid.uuid4()
    trainer_id = uuid.uuid4()
    assignment_repository = FakeAssignmentRepository()
    assignment_repository.set_trainer(trainer_user_id, trainer_id)
    client_repository.assign(trainer_id, client.id)
    user_repository = FakeUserRepository()
    role_repository = FakeRoleRepository()
    _override_dependencies(
        client_repository,
        user_repository,
        role_repository,
        trainer_user_id,
        RoleName.TRAINER,
        assignment_repository,
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


def test_list_clients_returns_only_assigned_clients_for_trainer():
    client_repository = FakeClientRepository()
    assigned_client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(assigned_client, "assigned@example.com")
    unassigned_client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(unassigned_client, "unassigned@example.com")

    trainer_user_id = uuid.uuid4()
    trainer_id = uuid.uuid4()
    assignment_repository = FakeAssignmentRepository()
    assignment_repository.set_trainer(trainer_user_id, trainer_id)
    client_repository.assign(trainer_id, assigned_client.id)

    user_repository = FakeUserRepository()
    role_repository = FakeRoleRepository()
    _override_dependencies(
        client_repository,
        user_repository,
        role_repository,
        trainer_user_id,
        RoleName.TRAINER,
        assignment_repository,
    )
    test_client = TestClient(app)

    response = test_client.get("/api/v1/clients")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == str(assigned_client.id)


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


def test_get_current_client_succeeds_for_client():
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

    response = test_client.get("/api/v1/clients/me")

    assert response.status_code == 200
    assert response.json()["id"] == str(client.id)


def test_get_current_client_rejects_super_admin():
    client_repository = FakeClientRepository()
    user_repository = FakeUserRepository()
    role_repository = FakeRoleRepository()
    _override_dependencies(
        client_repository, user_repository, role_repository, uuid.uuid4(), RoleName.SUPER_ADMIN
    )
    test_client = TestClient(app)

    response = test_client.get("/api/v1/clients/me")

    assert response.status_code == 403


def test_get_current_client_rejects_trainer():
    client_repository = FakeClientRepository()
    user_repository = FakeUserRepository()
    role_repository = FakeRoleRepository()
    _override_dependencies(
        client_repository, user_repository, role_repository, uuid.uuid4(), RoleName.TRAINER
    )
    test_client = TestClient(app)

    response = test_client.get("/api/v1/clients/me")

    assert response.status_code == 403


def test_get_current_client_requires_authentication():
    test_client = TestClient(app)

    response = test_client.get("/api/v1/clients/me")

    assert response.status_code == 401


def test_update_current_client_succeeds_for_client():
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

    response = test_client.put("/api/v1/clients/me", json={"first_name": "Janet"})

    assert response.status_code == 200
    assert response.json()["first_name"] == "Janet"


def test_update_current_client_rejects_super_admin():
    client_repository = FakeClientRepository()
    user_repository = FakeUserRepository()
    role_repository = FakeRoleRepository()
    _override_dependencies(
        client_repository, user_repository, role_repository, uuid.uuid4(), RoleName.SUPER_ADMIN
    )
    test_client = TestClient(app)

    response = test_client.put("/api/v1/clients/me", json={"first_name": "Hacker"})

    assert response.status_code == 403


def test_update_current_client_rejects_trainer():
    client_repository = FakeClientRepository()
    user_repository = FakeUserRepository()
    role_repository = FakeRoleRepository()
    _override_dependencies(
        client_repository, user_repository, role_repository, uuid.uuid4(), RoleName.TRAINER
    )
    test_client = TestClient(app)

    response = test_client.put("/api/v1/clients/me", json={"first_name": "Hacker"})

    assert response.status_code == 403


def test_update_current_client_rejects_empty_body():
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

    response = test_client.put("/api/v1/clients/me", json={})

    assert response.status_code == 422
