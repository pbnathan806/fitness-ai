import asyncio
import uuid
from datetime import datetime, timezone

import pytest

from core.constants import RoleName
from models.client import Client
from models.client_trainer_assignment import ClientTrainerAssignment
from models.trainer_profile import TrainerProfile
from repositories.assignment_repository import (
    AssignedClientRecord,
    AssignedTrainerRecord,
    AssignmentRepository,
)
from services.assignment_service import (
    AssignmentNotFoundError,
    AssignmentService,
    ClientNotFoundError,
    DuplicateAssignmentError,
    ForbiddenError,
    PrimaryTrainerExistsError,
    TrainerNotFoundError,
)
from tests.services.test_client_service import FakeClientRepository, _make_client


class FakeAssignmentRepository(AssignmentRepository):
    def __init__(self) -> None:
        self._assignments: dict[uuid.UUID, ClientTrainerAssignment] = {}
        self._clients: dict[uuid.UUID, tuple[Client, str]] = {}
        self._trainers: dict[uuid.UUID, tuple[TrainerProfile, str]] = {}
        self._trainer_by_user_id: dict[uuid.UUID, uuid.UUID] = {}

    def seed_client(self, client: Client, email: str = "client@example.com") -> None:
        self._clients[client.id] = (client, email)

    def seed_trainer(self, trainer: TrainerProfile, email: str = "trainer@example.com") -> None:
        self._trainers[trainer.id] = (trainer, email)
        self._trainer_by_user_id[trainer.user_id] = trainer.id

    def seed_assignment(self, assignment: ClientTrainerAssignment) -> None:
        self._assignments[assignment.id] = assignment

    async def client_exists(self, client_id: uuid.UUID) -> bool:
        return client_id in self._clients

    async def trainer_exists(self, trainer_id: uuid.UUID) -> bool:
        return trainer_id in self._trainers

    async def exists_for_pair(self, client_id: uuid.UUID, trainer_id: uuid.UUID) -> bool:
        return any(
            a.client_id == client_id and a.trainer_id == trainer_id
            for a in self._assignments.values()
        )

    async def client_has_primary_trainer(self, client_id: uuid.UUID) -> bool:
        return any(
            a.client_id == client_id and a.is_primary for a in self._assignments.values()
        )

    async def create(
        self, assignment: ClientTrainerAssignment
    ) -> ClientTrainerAssignment:
        now = datetime.now(timezone.utc)
        assignment.id = assignment.id or uuid.uuid4()
        assignment.assigned_at = now
        assignment.created_at = now
        assignment.updated_at = now
        self._assignments[assignment.id] = assignment
        return assignment

    async def get_by_id(
        self, assignment_id: uuid.UUID
    ) -> ClientTrainerAssignment | None:
        return self._assignments.get(assignment_id)

    async def delete(self, assignment_id: uuid.UUID) -> bool:
        if assignment_id in self._assignments:
            del self._assignments[assignment_id]
            return True
        return False

    async def list_paginated(
        self, offset: int, limit: int
    ) -> tuple[list[ClientTrainerAssignment], int]:
        ordered = sorted(
            self._assignments.values(), key=lambda a: a.created_at, reverse=True
        )
        page = ordered[offset : offset + limit]
        return page, len(ordered)

    async def get_trainer_id_by_user_id(self, user_id: uuid.UUID) -> uuid.UUID | None:
        return self._trainer_by_user_id.get(user_id)

    async def list_clients_for_trainer(
        self, trainer_id: uuid.UUID
    ) -> list[AssignedClientRecord]:
        records = []
        for assignment in self._assignments.values():
            if assignment.trainer_id == trainer_id:
                client, email = self._clients[assignment.client_id]
                records.append(
                    AssignedClientRecord(assignment=assignment, client=client, email=email)
                )
        return records

    async def list_trainers_for_client(
        self, client_id: uuid.UUID
    ) -> list[AssignedTrainerRecord]:
        records = []
        for assignment in self._assignments.values():
            if assignment.client_id == client_id:
                trainer, email = self._trainers[assignment.trainer_id]
                records.append(
                    AssignedTrainerRecord(assignment=assignment, trainer=trainer, email=email)
                )
        return records


def _make_trainer(user_id: uuid.UUID, **overrides) -> TrainerProfile:
    defaults = dict(
        id=uuid.uuid4(),
        user_id=user_id,
        specialization="Strength",
        experience_years=5,
        bio="Experienced trainer.",
        timezone="America/New_York",
        country="US",
        is_accepting_clients=True,
    )
    defaults.update(overrides)
    return TrainerProfile(**defaults)


def _make_service() -> tuple[AssignmentService, FakeAssignmentRepository, FakeClientRepository]:
    assignment_repository = FakeAssignmentRepository()
    client_repository = FakeClientRepository()
    service = AssignmentService(assignment_repository, client_repository)
    return service, assignment_repository, client_repository


def test_create_assignment_succeeds_for_super_admin():
    service, assignment_repository, client_repository = _make_service()
    client = _make_client(user_id=uuid.uuid4())
    trainer = _make_trainer(user_id=uuid.uuid4())
    assignment_repository.seed_client(client)
    assignment_repository.seed_trainer(trainer)

    detail = asyncio.run(
        service.create_assignment(
            actor_role=RoleName.SUPER_ADMIN,
            client_id=client.id,
            trainer_id=trainer.id,
            is_primary=True,
        )
    )

    assert detail.client_id == client.id
    assert detail.trainer_id == trainer.id
    assert detail.is_primary is True


def test_create_assignment_rejects_non_super_admin():
    service, assignment_repository, _ = _make_service()
    client = _make_client(user_id=uuid.uuid4())
    trainer = _make_trainer(user_id=uuid.uuid4())
    assignment_repository.seed_client(client)
    assignment_repository.seed_trainer(trainer)

    for role in (RoleName.TRAINER, RoleName.CLIENT, None):
        with pytest.raises(ForbiddenError):
            asyncio.run(
                service.create_assignment(
                    actor_role=role,
                    client_id=client.id,
                    trainer_id=trainer.id,
                    is_primary=False,
                )
            )


def test_create_assignment_raises_when_client_missing():
    service, assignment_repository, _ = _make_service()
    trainer = _make_trainer(user_id=uuid.uuid4())
    assignment_repository.seed_trainer(trainer)

    with pytest.raises(ClientNotFoundError):
        asyncio.run(
            service.create_assignment(
                actor_role=RoleName.SUPER_ADMIN,
                client_id=uuid.uuid4(),
                trainer_id=trainer.id,
                is_primary=False,
            )
        )


def test_create_assignment_raises_when_trainer_missing():
    service, assignment_repository, _ = _make_service()
    client = _make_client(user_id=uuid.uuid4())
    assignment_repository.seed_client(client)

    with pytest.raises(TrainerNotFoundError):
        asyncio.run(
            service.create_assignment(
                actor_role=RoleName.SUPER_ADMIN,
                client_id=client.id,
                trainer_id=uuid.uuid4(),
                is_primary=False,
            )
        )


def test_create_assignment_rejects_duplicate():
    service, assignment_repository, _ = _make_service()
    client = _make_client(user_id=uuid.uuid4())
    trainer = _make_trainer(user_id=uuid.uuid4())
    assignment_repository.seed_client(client)
    assignment_repository.seed_trainer(trainer)
    asyncio.run(
        service.create_assignment(
            actor_role=RoleName.SUPER_ADMIN,
            client_id=client.id,
            trainer_id=trainer.id,
            is_primary=False,
        )
    )

    with pytest.raises(DuplicateAssignmentError):
        asyncio.run(
            service.create_assignment(
                actor_role=RoleName.SUPER_ADMIN,
                client_id=client.id,
                trainer_id=trainer.id,
                is_primary=False,
            )
        )


def test_create_assignment_rejects_second_primary_trainer():
    service, assignment_repository, _ = _make_service()
    client = _make_client(user_id=uuid.uuid4())
    trainer_one = _make_trainer(user_id=uuid.uuid4())
    trainer_two = _make_trainer(user_id=uuid.uuid4())
    assignment_repository.seed_client(client)
    assignment_repository.seed_trainer(trainer_one)
    assignment_repository.seed_trainer(trainer_two)
    asyncio.run(
        service.create_assignment(
            actor_role=RoleName.SUPER_ADMIN,
            client_id=client.id,
            trainer_id=trainer_one.id,
            is_primary=True,
        )
    )

    with pytest.raises(PrimaryTrainerExistsError):
        asyncio.run(
            service.create_assignment(
                actor_role=RoleName.SUPER_ADMIN,
                client_id=client.id,
                trainer_id=trainer_two.id,
                is_primary=True,
            )
        )


def test_create_assignment_allows_multiple_non_primary_trainers():
    service, assignment_repository, _ = _make_service()
    client = _make_client(user_id=uuid.uuid4())
    trainer_one = _make_trainer(user_id=uuid.uuid4())
    trainer_two = _make_trainer(user_id=uuid.uuid4())
    assignment_repository.seed_client(client)
    assignment_repository.seed_trainer(trainer_one)
    assignment_repository.seed_trainer(trainer_two)
    asyncio.run(
        service.create_assignment(
            actor_role=RoleName.SUPER_ADMIN,
            client_id=client.id,
            trainer_id=trainer_one.id,
            is_primary=True,
        )
    )

    detail = asyncio.run(
        service.create_assignment(
            actor_role=RoleName.SUPER_ADMIN,
            client_id=client.id,
            trainer_id=trainer_two.id,
            is_primary=False,
        )
    )

    assert detail.is_primary is False


def test_get_assignment_succeeds_for_super_admin():
    service, assignment_repository, _ = _make_service()
    client = _make_client(user_id=uuid.uuid4())
    trainer = _make_trainer(user_id=uuid.uuid4())
    assignment_repository.seed_client(client)
    assignment_repository.seed_trainer(trainer)
    created = asyncio.run(
        service.create_assignment(
            actor_role=RoleName.SUPER_ADMIN,
            client_id=client.id,
            trainer_id=trainer.id,
            is_primary=False,
        )
    )

    detail = asyncio.run(
        service.get_assignment(actor_role=RoleName.SUPER_ADMIN, assignment_id=created.id)
    )

    assert detail.id == created.id


def test_get_assignment_rejects_non_super_admin():
    service, *_ = _make_service()

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.get_assignment(actor_role=RoleName.TRAINER, assignment_id=uuid.uuid4())
        )


def test_get_assignment_raises_not_found():
    service, *_ = _make_service()

    with pytest.raises(AssignmentNotFoundError):
        asyncio.run(
            service.get_assignment(actor_role=RoleName.SUPER_ADMIN, assignment_id=uuid.uuid4())
        )


def test_list_assignments_succeeds_for_super_admin_with_pagination():
    service, assignment_repository, _ = _make_service()
    for _ in range(3):
        client = _make_client(user_id=uuid.uuid4())
        trainer = _make_trainer(user_id=uuid.uuid4())
        assignment_repository.seed_client(client)
        assignment_repository.seed_trainer(trainer)
        asyncio.run(
            service.create_assignment(
                actor_role=RoleName.SUPER_ADMIN,
                client_id=client.id,
                trainer_id=trainer.id,
                is_primary=False,
            )
        )

    result = asyncio.run(
        service.list_assignments(actor_role=RoleName.SUPER_ADMIN, page=1, page_size=2)
    )

    assert result.total == 3
    assert len(result.items) == 2


def test_list_assignments_rejects_non_super_admin():
    service, *_ = _make_service()

    with pytest.raises(ForbiddenError):
        asyncio.run(service.list_assignments(actor_role=RoleName.CLIENT, page=1, page_size=20))


def test_delete_assignment_succeeds_for_super_admin():
    service, assignment_repository, _ = _make_service()
    client = _make_client(user_id=uuid.uuid4())
    trainer = _make_trainer(user_id=uuid.uuid4())
    assignment_repository.seed_client(client)
    assignment_repository.seed_trainer(trainer)
    created = asyncio.run(
        service.create_assignment(
            actor_role=RoleName.SUPER_ADMIN,
            client_id=client.id,
            trainer_id=trainer.id,
            is_primary=False,
        )
    )

    asyncio.run(service.delete_assignment(actor_role=RoleName.SUPER_ADMIN, assignment_id=created.id))

    with pytest.raises(AssignmentNotFoundError):
        asyncio.run(
            service.get_assignment(actor_role=RoleName.SUPER_ADMIN, assignment_id=created.id)
        )


def test_delete_assignment_rejects_non_super_admin():
    service, *_ = _make_service()

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.delete_assignment(actor_role=RoleName.TRAINER, assignment_id=uuid.uuid4())
        )


def test_delete_assignment_raises_not_found():
    service, *_ = _make_service()

    with pytest.raises(AssignmentNotFoundError):
        asyncio.run(
            service.delete_assignment(
                actor_role=RoleName.SUPER_ADMIN, assignment_id=uuid.uuid4()
            )
        )


def test_list_my_clients_returns_assigned_clients_for_trainer():
    service, assignment_repository, _ = _make_service()
    trainer_user_id = uuid.uuid4()
    trainer = _make_trainer(user_id=trainer_user_id)
    client = _make_client(user_id=uuid.uuid4())
    assignment_repository.seed_trainer(trainer)
    assignment_repository.seed_client(client, "client@example.com")
    asyncio.run(
        service.create_assignment(
            actor_role=RoleName.SUPER_ADMIN,
            client_id=client.id,
            trainer_id=trainer.id,
            is_primary=True,
        )
    )

    clients = asyncio.run(
        service.list_my_clients(actor_role=RoleName.TRAINER, actor_id=trainer_user_id)
    )

    assert len(clients) == 1
    assert clients[0].client_id == client.id
    assert clients[0].is_primary is True


def test_list_my_clients_rejects_non_trainer():
    service, *_ = _make_service()

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.list_my_clients(actor_role=RoleName.SUPER_ADMIN, actor_id=uuid.uuid4())
        )


def test_list_my_clients_raises_when_no_trainer_profile():
    service, *_ = _make_service()

    with pytest.raises(TrainerNotFoundError):
        asyncio.run(
            service.list_my_clients(actor_role=RoleName.TRAINER, actor_id=uuid.uuid4())
        )


def test_list_my_trainers_returns_assigned_trainers_for_client():
    service, assignment_repository, client_repository = _make_service()
    client_user_id = uuid.uuid4()
    client = _make_client(user_id=client_user_id)
    trainer = _make_trainer(user_id=uuid.uuid4())
    client_repository.seed(client, "client@example.com")
    assignment_repository.seed_client(client)
    assignment_repository.seed_trainer(trainer, "trainer@example.com")
    asyncio.run(
        service.create_assignment(
            actor_role=RoleName.SUPER_ADMIN,
            client_id=client.id,
            trainer_id=trainer.id,
            is_primary=True,
        )
    )

    trainers = asyncio.run(
        service.list_my_trainers(actor_role=RoleName.CLIENT, actor_id=client_user_id)
    )

    assert len(trainers) == 1
    assert trainers[0].trainer_id == trainer.id
    assert trainers[0].is_primary is True


def test_list_my_trainers_rejects_non_client():
    service, *_ = _make_service()

    with pytest.raises(ForbiddenError):
        asyncio.run(
            service.list_my_trainers(actor_role=RoleName.TRAINER, actor_id=uuid.uuid4())
        )


def test_list_my_trainers_raises_when_no_client_profile():
    service, *_ = _make_service()

    with pytest.raises(ClientNotFoundError):
        asyncio.run(
            service.list_my_trainers(actor_role=RoleName.CLIENT, actor_id=uuid.uuid4())
        )
