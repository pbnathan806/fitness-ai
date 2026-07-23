import uuid

from fastapi.testclient import TestClient

from core.constants import RoleName
from core.deps import CurrentUser, get_current_user
from main import app
from routers.subscription_plans import get_subscription_plan_repository
from tests.services.test_subscription_plan_service import (
    FakeSubscriptionPlanRepository,
    _make_plan,
)


def _override_dependencies(
    repository: FakeSubscriptionPlanRepository, user_id: uuid.UUID, active_role: str | None
) -> None:
    app.dependency_overrides[get_subscription_plan_repository] = lambda: repository
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        user_id=user_id, active_role=active_role
    )


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_create_plan_succeeds_for_super_admin():
    repository = FakeSubscriptionPlanRepository()
    _override_dependencies(repository, uuid.uuid4(), RoleName.SUPER_ADMIN)
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/subscription-plans",
        json={
            "name": "Premium",
            "description": "Premium coaching plan.",
            "duration_days": 30,
            "price": 99.99,
            "currency": "USD",
            "max_sessions_per_month": 8,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Premium"
    assert body["is_active"] is True


def test_create_plan_rejects_trainer_role():
    repository = FakeSubscriptionPlanRepository()
    _override_dependencies(repository, uuid.uuid4(), RoleName.TRAINER)
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/subscription-plans",
        json={
            "name": "Premium",
            "duration_days": 30,
            "price": 99.99,
            "currency": "USD",
        },
    )

    assert response.status_code == 403


def test_create_plan_rejects_client_role():
    repository = FakeSubscriptionPlanRepository()
    _override_dependencies(repository, uuid.uuid4(), RoleName.CLIENT)
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/subscription-plans",
        json={
            "name": "Premium",
            "duration_days": 30,
            "price": 99.99,
            "currency": "USD",
        },
    )

    assert response.status_code == 403


def test_create_plan_requires_authentication():
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/subscription-plans",
        json={"name": "Premium", "duration_days": 30, "price": 99.99, "currency": "USD"},
    )

    assert response.status_code == 401


def test_create_plan_returns_409_for_duplicate_name():
    repository = FakeSubscriptionPlanRepository()
    repository.seed(_make_plan(name="Premium"))
    _override_dependencies(repository, uuid.uuid4(), RoleName.SUPER_ADMIN)
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/subscription-plans",
        json={"name": "Premium", "duration_days": 30, "price": 99.99, "currency": "USD"},
    )

    assert response.status_code == 409


def test_list_subscription_plans_returns_only_active_plans():
    repository = FakeSubscriptionPlanRepository()
    repository.seed(_make_plan(name="Active Plan", is_active=True))
    repository.seed(_make_plan(name="Inactive Plan", is_active=False))
    _override_dependencies(repository, uuid.uuid4(), RoleName.CLIENT)
    test_client = TestClient(app)

    response = test_client.get("/api/v1/subscription-plans")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["name"] == "Active Plan"


def test_list_subscription_plans_requires_authentication():
    test_client = TestClient(app)

    response = test_client.get("/api/v1/subscription-plans")

    assert response.status_code == 401


def test_get_subscription_plan_succeeds_for_any_authenticated_role():
    repository = FakeSubscriptionPlanRepository()
    plan = _make_plan()
    repository.seed(plan)
    _override_dependencies(repository, uuid.uuid4(), RoleName.TRAINER)
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/subscription-plans/{plan.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(plan.id)


def test_get_subscription_plan_returns_404_for_missing_plan():
    repository = FakeSubscriptionPlanRepository()
    _override_dependencies(repository, uuid.uuid4(), RoleName.CLIENT)
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/subscription-plans/{uuid.uuid4()}")

    assert response.status_code == 404


def test_update_subscription_plan_succeeds_for_super_admin():
    repository = FakeSubscriptionPlanRepository()
    plan = _make_plan(price=99.99)
    repository.seed(plan)
    _override_dependencies(repository, uuid.uuid4(), RoleName.SUPER_ADMIN)
    test_client = TestClient(app)

    response = test_client.put(
        f"/api/v1/subscription-plans/{plan.id}",
        json={"price": 149.99, "is_active": False},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["price"] == 149.99
    assert body["is_active"] is False


def test_update_subscription_plan_ignores_immutable_fields():
    repository = FakeSubscriptionPlanRepository()
    plan = _make_plan(name="Premium", duration_days=30, currency="USD")
    repository.seed(plan)
    _override_dependencies(repository, uuid.uuid4(), RoleName.SUPER_ADMIN)
    test_client = TestClient(app)

    response = test_client.put(
        f"/api/v1/subscription-plans/{plan.id}",
        json={
            "name": "Renamed",
            "duration_days": 60,
            "currency": "EUR",
            "description": "New description.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Premium"
    assert body["duration_days"] == 30
    assert body["currency"] == "USD"
    assert body["description"] == "New description."


def test_update_subscription_plan_rejects_trainer_role():
    repository = FakeSubscriptionPlanRepository()
    plan = _make_plan()
    repository.seed(plan)
    _override_dependencies(repository, uuid.uuid4(), RoleName.TRAINER)
    test_client = TestClient(app)

    response = test_client.put(f"/api/v1/subscription-plans/{plan.id}", json={"price": 10.0})

    assert response.status_code == 403


def test_update_subscription_plan_returns_404_for_missing_plan():
    repository = FakeSubscriptionPlanRepository()
    _override_dependencies(repository, uuid.uuid4(), RoleName.SUPER_ADMIN)
    test_client = TestClient(app)

    response = test_client.put(
        f"/api/v1/subscription-plans/{uuid.uuid4()}", json={"price": 10.0}
    )

    assert response.status_code == 404
