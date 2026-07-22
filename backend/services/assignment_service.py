import uuid
from dataclasses import dataclass
from datetime import datetime

from core.constants import RoleName
from models.client_trainer_assignment import ClientTrainerAssignment
from repositories.assignment_repository import AssignmentRepository
from repositories.client_repository import ClientRepository


class ForbiddenError(Exception):
    """Raised when the acting user's role does not permit the requested action."""


class ClientNotFoundError(Exception):
    """Raised when no client profile exists for the requested identifier."""


class TrainerNotFoundError(Exception):
    """Raised when no trainer profile exists for the requested identifier."""


class AssignmentNotFoundError(Exception):
    """Raised when no assignment exists for the requested identifier."""


class DuplicateAssignmentError(Exception):
    """Raised when a client is already assigned to the requested trainer."""


class PrimaryTrainerExistsError(Exception):
    """Raised when a client already has a primary trainer and another primary is requested."""


@dataclass(frozen=True)
class AssignmentDetail:
    id: uuid.UUID
    client_id: uuid.UUID
    trainer_id: uuid.UUID
    is_primary: bool
    assigned_at: datetime
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class PaginatedAssignments:
    items: list[AssignmentDetail]
    page: int
    page_size: int
    total: int


@dataclass(frozen=True)
class AssignedClient:
    assignment_id: uuid.UUID
    client_id: uuid.UUID
    first_name: str
    last_name: str
    email: str
    phone_number: str | None
    timezone: str
    is_primary: bool


@dataclass(frozen=True)
class AssignedTrainer:
    assignment_id: uuid.UUID
    trainer_id: uuid.UUID
    specialization: str | None
    experience_years: int | None
    bio: str | None
    timezone: str | None
    country: str | None
    email: str
    is_primary: bool


def _to_detail(assignment: ClientTrainerAssignment) -> AssignmentDetail:
    return AssignmentDetail(
        id=assignment.id,
        client_id=assignment.client_id,
        trainer_id=assignment.trainer_id,
        is_primary=assignment.is_primary,
        assigned_at=assignment.assigned_at,
        created_at=assignment.created_at,
        updated_at=assignment.updated_at,
    )


class AssignmentService:
    """Business logic for client-trainer assignments and their Version-1 RBAC rules (Task-15.3).

    SUPER_ADMIN has full access to create, read, list, and delete assignments.
    TRAINER may only list their own assigned clients. CLIENT may only list
    their own assigned trainers. Any other role is rejected.
    """

    def __init__(
        self,
        assignment_repository: AssignmentRepository,
        client_repository: ClientRepository,
    ) -> None:
        self._assignment_repository = assignment_repository
        self._client_repository = client_repository

    async def create_assignment(
        self,
        actor_role: str | None,
        client_id: uuid.UUID,
        trainer_id: uuid.UUID,
        is_primary: bool,
    ) -> AssignmentDetail:
        if actor_role != RoleName.SUPER_ADMIN:
            raise ForbiddenError("Only Super Admins may create assignments.")

        if not await self._assignment_repository.client_exists(client_id):
            raise ClientNotFoundError(f"Client '{client_id}' was not found.")

        if not await self._assignment_repository.trainer_exists(trainer_id):
            raise TrainerNotFoundError(f"Trainer '{trainer_id}' was not found.")

        if await self._assignment_repository.exists_for_pair(client_id, trainer_id):
            raise DuplicateAssignmentError(
                f"Client '{client_id}' is already assigned to trainer '{trainer_id}'."
            )

        if is_primary and await self._assignment_repository.client_has_primary_trainer(
            client_id
        ):
            raise PrimaryTrainerExistsError(
                f"Client '{client_id}' already has a primary trainer."
            )

        assignment = await self._assignment_repository.create(
            ClientTrainerAssignment(
                client_id=client_id,
                trainer_id=trainer_id,
                is_primary=is_primary,
            )
        )
        return _to_detail(assignment)

    async def get_assignment(
        self, actor_role: str | None, assignment_id: uuid.UUID
    ) -> AssignmentDetail:
        if actor_role != RoleName.SUPER_ADMIN:
            raise ForbiddenError("Only Super Admins may view assignments.")

        assignment = await self._assignment_repository.get_by_id(assignment_id)
        if assignment is None:
            raise AssignmentNotFoundError(f"Assignment '{assignment_id}' was not found.")
        return _to_detail(assignment)

    async def list_assignments(
        self, actor_role: str | None, page: int, page_size: int
    ) -> PaginatedAssignments:
        if actor_role != RoleName.SUPER_ADMIN:
            raise ForbiddenError("Only Super Admins may list assignments.")

        offset = (page - 1) * page_size
        assignments, total = await self._assignment_repository.list_paginated(
            offset, page_size
        )
        return PaginatedAssignments(
            items=[_to_detail(assignment) for assignment in assignments],
            page=page,
            page_size=page_size,
            total=total,
        )

    async def delete_assignment(
        self, actor_role: str | None, assignment_id: uuid.UUID
    ) -> None:
        if actor_role != RoleName.SUPER_ADMIN:
            raise ForbiddenError("Only Super Admins may delete assignments.")

        deleted = await self._assignment_repository.delete(assignment_id)
        if not deleted:
            raise AssignmentNotFoundError(f"Assignment '{assignment_id}' was not found.")

    async def list_my_clients(
        self, actor_role: str | None, actor_id: uuid.UUID
    ) -> list[AssignedClient]:
        if actor_role != RoleName.TRAINER:
            raise ForbiddenError("Only Trainers may view their assigned clients.")

        trainer_id = await self._assignment_repository.get_trainer_id_by_user_id(actor_id)
        if trainer_id is None:
            raise TrainerNotFoundError("No trainer profile exists for the current user.")

        records = await self._assignment_repository.list_clients_for_trainer(trainer_id)
        return [
            AssignedClient(
                assignment_id=record.assignment.id,
                client_id=record.client.id,
                first_name=record.client.first_name,
                last_name=record.client.last_name,
                email=record.email,
                phone_number=record.client.phone_number,
                timezone=record.client.timezone,
                is_primary=record.assignment.is_primary,
            )
            for record in records
        ]

    async def list_my_trainers(
        self, actor_role: str | None, actor_id: uuid.UUID
    ) -> list[AssignedTrainer]:
        if actor_role != RoleName.CLIENT:
            raise ForbiddenError("Only Clients may view their assigned trainers.")

        client_record = await self._client_repository.get_by_user_id(actor_id)
        if client_record is None:
            raise ClientNotFoundError("No client profile exists for the current user.")

        records = await self._assignment_repository.list_trainers_for_client(
            client_record.client.id
        )
        return [
            AssignedTrainer(
                assignment_id=record.assignment.id,
                trainer_id=record.trainer.id,
                specialization=record.trainer.specialization,
                experience_years=record.trainer.experience_years,
                bio=record.trainer.bio,
                timezone=record.trainer.timezone,
                country=record.trainer.country,
                email=record.email,
                is_primary=record.assignment.is_primary,
            )
            for record in records
        ]
