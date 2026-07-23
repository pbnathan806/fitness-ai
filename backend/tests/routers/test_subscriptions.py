import uuid
from datetime import date, timedelta

from fastapi.testclient import TestClient

from core.constants import RoleName
from core.deps import CurrentUser, get_current_user
from main import app
from models.client_trainer_assignment import ClientTrainerAssignment
from models.subscription import SubscriptionPaymentStatus, SubscriptionStatus
from routers.subscriptions import (
    get_assignment_repository,
    get_client_repository,
    get_subscription_plan_repository,
    get_subscription_repository,
)
from tests.services.test_assignment_service import FakeAssignmentRepository, _make_trainer
from tests.services.test_client_service import FakeClientRepository, _make_client
from tests.services.test_subscription_plan_service import (
    FakeSubscriptionPlanRepository,
    _make_plan,
)
from tests.services.test_subscription_service import FakeSubscriptionRepository, _make_subscription


def _override_dependencies(
    subscription_repository: FakeSubscriptionRepository,
    subscription_plan_repository: FakeSubscriptionPlanRepository,
    client_repository: FakeClientRepository,
    assignment_repository: FakeAssignmentRepository,
    user_id: uuid.UUID,
    active_role: str | None,
) -> None:
    app.dependency_overrides[get_subscription_repository] = lambda: subscription_repository
    app.dependency_overrides[get_subscription_plan_repository] = (
        lambda: subscription_plan_repository
    )
    app.dependency_overrides[get_client_repository] = lambda: client_repository
    app.dependency_overrides[get_assignment_repository] = lambda: assignment_repository
    app.dependency_overrides[get_current_user] = lambda: CurrentUser(
        user_id=user_id, active_role=active_role
    )


def _make_repos() -> tuple[
    FakeSubscriptionRepository,
    FakeSubscriptionPlanRepository,
    FakeClientRepository,
    FakeAssignmentRepository,
]:
    return (
        FakeSubscriptionRepository(),
        FakeSubscriptionPlanRepository(),
        FakeClientRepository(),
        FakeAssignmentRepository(),
    )


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_create_subscription_succeeds_for_super_admin():
    subscription_repository, plan_repository, client_repository, assignment_repository = (
        _make_repos()
    )
    client = _make_client(user_id=uuid.uuid4())
    plan = _make_plan()
    client_repository.seed(client, "client@example.com")
    plan_repository.seed(plan)
    _override_dependencies(
        subscription_repository,
        plan_repository,
        client_repository,
        assignment_repository,
        uuid.uuid4(),
        RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/subscriptions",
        json={
            "client_id": str(client.id),
            "subscription_plan_id": str(plan.id),
            "start_date": "2026-01-01",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["client_id"] == str(client.id)
    assert body["plan_name"] == plan.name
    assert body["start_date"] == "2026-01-01"
    assert body["status"] == "ACTIVE"


def test_create_subscription_rejects_trainer_role():
    subscription_repository, plan_repository, client_repository, assignment_repository = (
        _make_repos()
    )
    _override_dependencies(
        subscription_repository,
        plan_repository,
        client_repository,
        assignment_repository,
        uuid.uuid4(),
        RoleName.TRAINER,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/subscriptions",
        json={"client_id": str(uuid.uuid4()), "subscription_plan_id": str(uuid.uuid4())},
    )

    assert response.status_code == 403


def test_create_subscription_rejects_client_role():
    subscription_repository, plan_repository, client_repository, assignment_repository = (
        _make_repos()
    )
    _override_dependencies(
        subscription_repository,
        plan_repository,
        client_repository,
        assignment_repository,
        uuid.uuid4(),
        RoleName.CLIENT,
    )
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/subscriptions",
        json={"client_id": str(uuid.uuid4()), "subscription_plan_id": str(uuid.uuid4())},
    )

    assert response.status_code == 403


def test_create_subscription_requires_authentication():
    test_client = TestClient(app)

    response = test_client.post(
        "/api/v1/subscriptions",
        json={"client_id": str(uuid.uuid4()), "subscription_plan_id": str(uuid.uuid4())},
    )

    assert response.status_code == 401


def test_create_subscription_returns_409_for_duplicate_active_subscription():
    subscription_repository, plan_repository, client_repository, assignment_repository = (
        _make_repos()
    )
    client = _make_client(user_id=uuid.uuid4())
    plan = _make_plan()
    client_repository.seed(client, "client@example.com")
    plan_repository.seed(plan)
    _override_dependencies(
        subscription_repository,
        plan_repository,
        client_repository,
        assignment_repository,
        uuid.uuid4(),
        RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)
    payload = {"client_id": str(client.id), "subscription_plan_id": str(plan.id)}
    test_client.post("/api/v1/subscriptions", json=payload)

    response = test_client.post("/api/v1/subscriptions", json=payload)

    assert response.status_code == 409


def test_list_subscriptions_succeeds_for_super_admin_with_pagination():
    subscription_repository, plan_repository, client_repository, assignment_repository = (
        _make_repos()
    )
    for _ in range(3):
        subscription_repository.seed(_make_subscription(uuid.uuid4(), uuid.uuid4()))
    _override_dependencies(
        subscription_repository,
        plan_repository,
        client_repository,
        assignment_repository,
        uuid.uuid4(),
        RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get("/api/v1/subscriptions?page=1&page_size=2")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["total_pages"] == 2


def test_list_subscriptions_rejects_client_role():
    subscription_repository, plan_repository, client_repository, assignment_repository = (
        _make_repos()
    )
    _override_dependencies(
        subscription_repository,
        plan_repository,
        client_repository,
        assignment_repository,
        uuid.uuid4(),
        RoleName.CLIENT,
    )
    test_client = TestClient(app)

    response = test_client.get("/api/v1/subscriptions")

    assert response.status_code == 403


def test_get_my_subscriptions_succeeds_for_client():
    subscription_repository, plan_repository, client_repository, assignment_repository = (
        _make_repos()
    )
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id)
    client_repository.seed(client, "client@example.com")
    subscription_repository.seed(
        _make_subscription(
            client.id,
            uuid.uuid4(),
            plan_name="Premium",
            payment_status=SubscriptionPaymentStatus.PAID,
        )
    )
    _override_dependencies(
        subscription_repository,
        plan_repository,
        client_repository,
        assignment_repository,
        client_user_id,
        RoleName.CLIENT,
    )
    test_client = TestClient(app)

    response = test_client.get("/api/v1/subscriptions/my-subscriptions")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["plan_name"] == "Premium"
    assert body[0]["payment_status"] == "PAID"
    assert "plan_price" in body[0]
    assert "notes" not in body[0]


def test_get_my_subscriptions_rejects_trainer_role():
    subscription_repository, plan_repository, client_repository, assignment_repository = (
        _make_repos()
    )
    _override_dependencies(
        subscription_repository,
        plan_repository,
        client_repository,
        assignment_repository,
        uuid.uuid4(),
        RoleName.TRAINER,
    )
    test_client = TestClient(app)

    response = test_client.get("/api/v1/subscriptions/my-subscriptions")

    assert response.status_code == 403


def test_get_my_subscriptions_requires_authentication():
    test_client = TestClient(app)

    response = test_client.get("/api/v1/subscriptions/my-subscriptions")

    assert response.status_code == 401


def test_get_client_eligibility_succeeds_for_assigned_trainer():
    subscription_repository, plan_repository, client_repository, assignment_repository = (
        _make_repos()
    )
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    assignment_repository.seed_trainer(trainer)
    assignment_repository.seed_assignment(
        ClientTrainerAssignment(
            id=uuid.uuid4(), client_id=client.id, trainer_id=trainer.id, is_primary=True
        )
    )
    subscription_repository.seed(
        _make_subscription(
            client.id,
            uuid.uuid4(),
            plan_name="Premium",
            status=SubscriptionStatus.ACTIVE,
            end_date=date.today() + timedelta(days=10),
        )
    )
    _override_dependencies(
        subscription_repository,
        plan_repository,
        client_repository,
        assignment_repository,
        trainer_user_id,
        RoleName.TRAINER,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/subscriptions/client/{client.id}/eligibility")

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "client_id": str(client.id),
        "plan_name": "Premium",
        "status": "ACTIVE",
        "end_date": body["end_date"],
        "can_schedule_sessions": True,
    }
    assert set(body.keys()) == {
        "client_id",
        "plan_name",
        "status",
        "end_date",
        "can_schedule_sessions",
    }


def test_get_client_eligibility_rejects_unassigned_trainer():
    subscription_repository, plan_repository, client_repository, assignment_repository = (
        _make_repos()
    )
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    assignment_repository.seed_trainer(trainer)
    subscription_repository.seed(_make_subscription(client.id, uuid.uuid4()))
    _override_dependencies(
        subscription_repository,
        plan_repository,
        client_repository,
        assignment_repository,
        trainer_user_id,
        RoleName.TRAINER,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/subscriptions/client/{client.id}/eligibility")

    assert response.status_code == 403


def test_get_client_eligibility_succeeds_for_super_admin():
    subscription_repository, plan_repository, client_repository, assignment_repository = (
        _make_repos()
    )
    client = _make_client(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    subscription_repository.seed(_make_subscription(client.id, uuid.uuid4()))
    _override_dependencies(
        subscription_repository,
        plan_repository,
        client_repository,
        assignment_repository,
        uuid.uuid4(),
        RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/subscriptions/client/{client.id}/eligibility")

    assert response.status_code == 200


def test_get_client_eligibility_rejects_client_role():
    subscription_repository, plan_repository, client_repository, assignment_repository = (
        _make_repos()
    )
    _override_dependencies(
        subscription_repository,
        plan_repository,
        client_repository,
        assignment_repository,
        uuid.uuid4(),
        RoleName.CLIENT,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/subscriptions/client/{uuid.uuid4()}/eligibility")

    assert response.status_code == 403


def test_get_subscription_succeeds_for_super_admin():
    subscription_repository, plan_repository, client_repository, assignment_repository = (
        _make_repos()
    )
    subscription = _make_subscription(uuid.uuid4(), uuid.uuid4())
    subscription_repository.seed(subscription)
    _override_dependencies(
        subscription_repository,
        plan_repository,
        client_repository,
        assignment_repository,
        uuid.uuid4(),
        RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/subscriptions/{subscription.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(subscription.id)


def test_get_subscription_returns_404_for_missing_subscription():
    subscription_repository, plan_repository, client_repository, assignment_repository = (
        _make_repos()
    )
    _override_dependencies(
        subscription_repository,
        plan_repository,
        client_repository,
        assignment_repository,
        uuid.uuid4(),
        RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.get(f"/api/v1/subscriptions/{uuid.uuid4()}")

    assert response.status_code == 404


def test_update_subscription_succeeds_for_super_admin():
    subscription_repository, plan_repository, client_repository, assignment_repository = (
        _make_repos()
    )
    subscription = _make_subscription(uuid.uuid4(), uuid.uuid4())
    subscription_repository.seed(subscription)
    _override_dependencies(
        subscription_repository,
        plan_repository,
        client_repository,
        assignment_repository,
        uuid.uuid4(),
        RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.patch(
        f"/api/v1/subscriptions/{subscription.id}",
        json={"status": "CANCELLED", "notes": "Client requested cancellation."},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "CANCELLED"
    assert body["notes"] == "Client requested cancellation."


def test_update_subscription_ignores_immutable_fields():
    subscription_repository, plan_repository, client_repository, assignment_repository = (
        _make_repos()
    )
    client_id = uuid.uuid4()
    subscription = _make_subscription(client_id, uuid.uuid4(), plan_name="Premium")
    subscription_repository.seed(subscription)
    _override_dependencies(
        subscription_repository,
        plan_repository,
        client_repository,
        assignment_repository,
        uuid.uuid4(),
        RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.patch(
        f"/api/v1/subscriptions/{subscription.id}",
        json={"client_id": str(uuid.uuid4()), "auto_renew": True},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["client_id"] == str(client_id)
    assert body["auto_renew"] is True


def test_update_subscription_rejects_trainer_role():
    subscription_repository, plan_repository, client_repository, assignment_repository = (
        _make_repos()
    )
    subscription = _make_subscription(uuid.uuid4(), uuid.uuid4())
    subscription_repository.seed(subscription)
    _override_dependencies(
        subscription_repository,
        plan_repository,
        client_repository,
        assignment_repository,
        uuid.uuid4(),
        RoleName.TRAINER,
    )
    test_client = TestClient(app)

    response = test_client.patch(
        f"/api/v1/subscriptions/{subscription.id}", json={"status": "CANCELLED"}
    )

    assert response.status_code == 403


def test_update_subscription_returns_404_for_missing_subscription():
    subscription_repository, plan_repository, client_repository, assignment_repository = (
        _make_repos()
    )
    _override_dependencies(
        subscription_repository,
        plan_repository,
        client_repository,
        assignment_repository,
        uuid.uuid4(),
        RoleName.SUPER_ADMIN,
    )
    test_client = TestClient(app)

    response = test_client.patch(
        f"/api/v1/subscriptions/{uuid.uuid4()}", json={"status": "CANCELLED"}
    )

    assert response.status_code == 404
