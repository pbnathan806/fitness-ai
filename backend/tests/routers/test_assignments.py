import uuid

from fastapi.testclient import TestClient

from core.constants import RoleName
from core.deps import CurrentUser, get_current_user
from main import app
from routers.assignments import get_assignment_repository, get_client_repository
from tests.services.test_assignment_service import FakeAssignmentRepository, _make_trainer
from tests.services.test_client_service import FakeClientRepository, _make_client


def _override_dependencies(
    assignment_repository: FakeAssignmentRepository,
    client_repository: FakeClientRepository,
    user_id: uuid.UUID,
    active_role: str | None,
) -> None:
    app.dependency_overrides[get_assignment_repository] = lambda: assignment_repository
    app.dependency_overrides[get_client_repository] = lambda: client_repository
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        user_id=user_id, active_role=active_role
    )


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_create_assignment_succeeds_for_super_admin():
    assignment_repository = FakeAssignmentRepository()
    client_repository = FakeClientRepository()
    client = _make_client(user_id=uuid.uuid4())
    trainer = _make_trainer(user_id=uuid.uuid4())
    assignment_repository.seed_client(client)
    assignment_repository.seed_trainer(trainer)
    _override_dependencies(
        assignment_repository, client_repository, uuid.uuid4(), RoleName.SUPER_ADMIN
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/assignments",
        json={
            "client_id": str(client.id),
            "trainer_id": str(trainer.id),
            "is_primary": True,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["client_id"] == str(client.id)
    assert body["trainer_id"] == str(trainer.id)
    assert body["is_primary"] is True


def test_create_assignment_rejects_trainer_role():
    assignment_repository = FakeAssignmentRepository()
    client_repository = FakeClientRepository()
    client = _make_client(user_id=uuid.uuid4())
    trainer = _make_trainer(user_id=uuid.uuid4())
    assignment_repository.seed_client(client)
    assignment_repository.seed_trainer(trainer)
    _override_dependencies(assignment_repository, client_repository, uuid.uuid4(), RoleName.TRAINER)
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/assignments",
        json={"client_id": str(client.id), "trainer_id": str(trainer.id), "is_primary": False},
    )

    assert response.status_code == 403


def test_create_assignment_rejects_client_role():
    assignment_repository = FakeAssignmentRepository()
    client_repository = FakeClientRepository()
    client = _make_client(user_id=uuid.uuid4())
    trainer = _make_trainer(user_id=uuid.uuid4())
    assignment_repository.seed_client(client)
    assignment_repository.seed_trainer(trainer)
    _override_dependencies(assignment_repository, client_repository, uuid.uuid4(), RoleName.CLIENT)
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/assignments",
        json={"client_id": str(client.id), "trainer_id": str(trainer.id), "is_primary": False},
    )

    assert response.status_code == 403


def test_create_assignment_requires_authentication():
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/assignments",
        json={"client_id": str(uuid.uuid4()), "trainer_id": str(uuid.uuid4()), "is_primary": False},
    )

    assert response.status_code == 401


def test_create_assignment_returns_404_for_missing_client():
    assignment_repository = FakeAssignmentRepository()
    client_repository = FakeClientRepository()
    trainer = _make_trainer(user_id=uuid.uuid4())
    assignment_repository.seed_trainer(trainer)
    _override_dependencies(
        assignment_repository, client_repository, uuid.uuid4(), RoleName.SUPER_ADMIN
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/assignments",
        json={"client_id": str(uuid.uuid4()), "trainer_id": str(trainer.id), "is_primary": False},
    )

    assert response.status_code == 404


def test_create_assignment_returns_404_for_missing_trainer():
    assignment_repository = FakeAssignmentRepository()
    client_repository = FakeClientRepository()
    client = _make_client(user_id=uuid.uuid4())
    assignment_repository.seed_client(client)
    _override_dependencies(
        assignment_repository, client_repository, uuid.uuid4(), RoleName.SUPER_ADMIN
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/assignments",
        json={"client_id": str(client.id), "trainer_id": str(uuid.uuid4()), "is_primary": False},
    )

    assert response.status_code == 404


def test_create_assignment_returns_409_for_duplicate():
    assignment_repository = FakeAssignmentRepository()
    client_repository = FakeClientRepository()
    client = _make_client(user_id=uuid.uuid4())
    trainer = _make_trainer(user_id=uuid.uuid4())
    assignment_repository.seed_client(client)
    assignment_repository.seed_trainer(trainer)
    _override_dependencies(
        assignment_repository, client_repository, uuid.uuid4(), RoleName.SUPER_ADMIN
    )
    test_client = TestClient(app)
    payload = {"client_id": str(client.id), "trainer_id": str(trainer.id), "is_primary": False}
    test_client.post("/api/v1/assignments", json=payload)

    response = test_client.post("/api/v1/assignments", json=payload)

    assert response.status_code == 409


def test_create_assignment_returns_409_for_second_primary():
    assignment_repository = FakeAssignmentRepository()
    client_repository = FakeClientRepository()
    client = _make_client(user_id=uuid.uuid4())
    trainer_one = _make_trainer(user_id=uuid.uuid4())
    trainer_two = _make_trainer(user_id=uuid.uuid4())
    assignment_repository.seed_client(client)
    assignment_repository.seed_trainer(trainer_one)
    assignment_repository.seed_trainer(trainer_two)
    _override_dependencies(
        assignment_repository, client_repository, uuid.uuid4(), RoleName.SUPER_ADMIN
    )
    test_client = TestClient(app)
    test_client.post(
        "/api/v1/assignments",
        json={"client_id": str(client.id), "trainer_id": str(trainer_one.id), "is_primary": True},
    )

    response = test_client.post(
        "/api/v1/assignments",
        json={"client_id": str(client.id), "trainer_id": str(trainer_two.id), "is_primary": True},
    )

    assert response.status_code == 409


def test_get_assignment_succeeds_for_super_admin():
    assignment_repository = FakeAssignmentRepository()
    client_repository = FakeClientRepository()
    client = _make_client(user_id=uuid.uuid4())
    trainer = _make_trainer(user_id=uuid.uuid4())
    assignment_repository.seed_client(client)
    assignment_repository.seed_trainer(trainer)
    _override_dependencies(
        assignment_repository, client_repository, uuid.uuid4(), RoleName.SUPER_ADMIN
    )
    test_client = TestClient(app)
    created = test_client.post(
        "/api/v1/assignments",
        json={"client_id": str(client.id), "trainer_id": str(trainer.id), "is_primary": False},
    ).json()

    response = test_client.get(f"/api/v1/assignments/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_assignment_rejects_trainer():
    assignment_repository = FakeAssignmentRepository()
    client_repository = FakeClientRepository()
    _override_dependencies(assignment_repository, client_repository, uuid.uuid4(), RoleName.TRAINER)
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/assignments/{uuid.uuid4()}")

    assert response.status_code == 403


def test_get_assignment_returns_404_for_missing_assignment():
    assignment_repository = FakeAssignmentRepository()
    client_repository = FakeClientRepository()
    _override_dependencies(
        assignment_repository, client_repository, uuid.uuid4(), RoleName.SUPER_ADMIN
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/assignments/{uuid.uuid4()}")

    assert response.status_code == 404


def test_list_assignments_succeeds_for_super_admin_with_pagination():
    assignment_repository = FakeAssignmentRepository()
    client_repository = FakeClientRepository()
    _override_dependencies(
        assignment_repository, client_repository, uuid.uuid4(), RoleName.SUPER_ADMIN
    )
    test_client = TestClient(app)
    for _ in range(3):
        client = _make_client(user_id=uuid.uuid4())
        trainer = _make_trainer(user_id=uuid.uuid4())
        assignment_repository.seed_client(client)
        assignment_repository.seed_trainer(trainer)
        test_client.post(
            "/api/v1/assignments",
            json={"client_id": str(client.id), "trainer_id": str(trainer.id), "is_primary": False},
        )

    response = test_client.get("/api/v1/assignments?page=1&page_size=2")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["total_pages"] == 2


def test_list_assignments_rejects_client_role():
    assignment_repository = FakeAssignmentRepository()
    client_repository = FakeClientRepository()
    _override_dependencies(assignment_repository, client_repository, uuid.uuid4(), RoleName.CLIENT)
    test_client = TestClient(app)

    response = test_client.get("/api/v1/assignments")

    assert response.status_code == 403


def test_list_assignments_requires_authentication():
    test_client = TestClient(app)

    response = test_client.get("/api/v1/assignments")

    assert response.status_code == 401


def test_delete_assignment_succeeds_for_super_admin():
    assignment_repository = FakeAssignmentRepository()
    client_repository = FakeClientRepository()
    client = _make_client(user_id=uuid.uuid4())
    trainer = _make_trainer(user_id=uuid.uuid4())
    assignment_repository.seed_client(client)
    assignment_repository.seed_trainer(trainer)
    _override_dependencies(
        assignment_repository, client_repository, uuid.uuid4(), RoleName.SUPER_ADMIN
    )
    test_client = TestClient(app)
    created = test_client.post(
        "/api/v1/assignments",
        json={"client_id": str(client.id), "trainer_id": str(trainer.id), "is_primary": False},
    ).json()

    response = test_client.delete(f"/api/v1/assignments/{created['id']}")

    assert response.status_code == 204
    assert test_client.get(f"/api/v1/assignments/{created['id']}").status_code == 404


def test_delete_assignment_rejects_trainer():
    assignment_repository = FakeAssignmentRepository()
    client_repository = FakeClientRepository()
    _override_dependencies(assignment_repository, client_repository, uuid.uuid4(), RoleName.TRAINER)
    test_client = TestClient(app)

    response = test_client.delete(f"/api/v1/assignments/{uuid.uuid4()}")

    assert response.status_code == 403


def test_delete_assignment_returns_404_for_missing_assignment():
    assignment_repository = FakeAssignmentRepository()
    client_repository = FakeClientRepository()
    _override_dependencies(
        assignment_repository, client_repository, uuid.uuid4(), RoleName.SUPER_ADMIN
    )
    test_client = TestClient(app)

    response = test_client.delete(f"/api/v1/assignments/{uuid.uuid4()}")

    assert response.status_code == 404


def test_get_my_clients_succeeds_for_trainer():
    assignment_repository = FakeAssignmentRepository()
    client_repository = FakeClientRepository()
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    client = _make_client(user_id=uuid.uuid4())
    assignment_repository.seed_trainer(trainer)
    assignment_repository.seed_client(client, "client@example.com")
    _override_dependencies(
        assignment_repository, client_repository, trainer_user_id, RoleName.SUPER_ADMIN
    )
    test_client = TestClient(app)
    test_client.post(
        "/api/v1/assignments",
        json={"client_id": str(client.id), "trainer_id": str(trainer.id), "is_primary": True},
    )
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        user_id=trainer_user_id, active_role=RoleName.TRAINER
    )

    response = test_client.get("/api/v1/assignments/my-clients")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["client_id"] == str(client.id)
    assert body[0]["is_primary"] is True


def test_get_my_clients_rejects_super_admin():
    assignment_repository = FakeAssignmentRepository()
    client_repository = FakeClientRepository()
    _override_dependencies(
        assignment_repository, client_repository, uuid.uuid4(), RoleName.SUPER_ADMIN
    )
    test_client = TestClient(app)

    response = test_client.get("/api/v1/assignments/my-clients")

    assert response.status_code == 403


def test_get_my_clients_rejects_client_role():
    assignment_repository = FakeAssignmentRepository()
    client_repository = FakeClientRepository()
    _override_dependencies(assignment_repository, client_repository, uuid.uuid4(), RoleName.CLIENT)
    test_client = TestClient(app)

    response = test_client.get("/api/v1/assignments/my-clients")

    assert response.status_code == 403


def test_get_my_trainers_succeeds_for_client():
    assignment_repository = FakeAssignmentRepository()
    client_repository = FakeClientRepository()
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id)
    trainer = _make_trainer(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    assignment_repository.seed_client(client)
    assignment_repository.seed_trainer(trainer, "trainer@example.com")
    _override_dependencies(
        assignment_repository, client_repository, client_user_id, RoleName.CLIENT
    )
    test_client = TestClient(app)
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        user_id=client_user_id, active_role=RoleName.SUPER_ADMIN
    )
    test_client.post(
        "/api/v1/assignments",
        json={"client_id": str(client.id), "trainer_id": str(trainer.id), "is_primary": True},
    )
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        user_id=client_user_id, active_role=RoleName.CLIENT
    )

    response = test_client.get("/api/v1/assignments/my-trainers")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["trainer_id"] == str(trainer.id)
    assert body[0]["is_primary"] is True


def test_get_my_trainers_rejects_trainer_role():
    assignment_repository = FakeAssignmentRepository()
    client_repository = FakeClientRepository()
    _override_dependencies(assignment_repository, client_repository, uuid.uuid4(), RoleName.TRAINER)
    test_client = TestClient(app)

    response = test_client.get("/api/v1/assignments/my-trainers")

    assert response.status_code == 403


def test_get_my_trainers_requires_authentication():
    test_client = TestClient(app)

    response = test_client.get("/api/v1/assignments/my-trainers")

    assert response.status_code == 401
