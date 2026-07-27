"""Seeds 5 sample CLIENT accounts (client1..client5) for local development.

Also removes the throwaway client rows left over from manual UI smoke-testing
("C One", "Smoke Test", "Smokey Test") so the dev database only carries real
seed data going forward.

Idempotent: re-running skips any client1..client5 email that already exists.
"""

import asyncio
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete, select

from core.constants import RoleName
from core.security import hash_password
from database.session import SessionLocal
from models.client import Client
from models.client_trainer_assignment import ClientTrainerAssignment
from models.role import Role
from models.user import User
from models.user_role import UserRole

# Leftover client ids from manual browser smoke-testing of Task 22.3
# (frontend/src/app/pages/clients/*) - not real data.
STALE_CLIENT_IDS = [
    uuid.UUID("682dfe53-fb5e-4968-bc29-5c997fea5114"),  # "C One"
    uuid.UUID("7b77760a-9f0d-4d04-96e5-394697a1f58f"),  # "Smoke Test"
    uuid.UUID("c9f707d3-9a4a-45ee-a3d4-5222a4106eda"),  # "Smokey Test"
]

# One of each supported timezone family (US + IST) per TIMEZONE_REQUIREMENTS.md,
# cycled across the 5 sample clients for variety.
SAMPLE_TIMEZONES = [
    "America/New_York",
    "America/Chicago",
    "America/Denver",
    "America/Los_Angeles",
    "Asia/Kolkata",
]

SAMPLE_CLIENTS = [
    {
        "email": f"client{i}@example.com",
        "first_name": "Client",
        "last_name": str(i),
        "phone_number": f"555010{i:04d}",
        "timezone": SAMPLE_TIMEZONES[(i - 1) % len(SAMPLE_TIMEZONES)],
    }
    for i in range(1, 6)
]


async def remove_stale_clients(db) -> None:
    for client_id in STALE_CLIENT_IDS:
        client = await db.get(Client, client_id)
        if client is None:
            continue

        await db.execute(
            delete(ClientTrainerAssignment).where(ClientTrainerAssignment.client_id == client_id)
        )
        user_id = client.user_id
        await db.delete(client)
        await db.execute(delete(UserRole).where(UserRole.user_id == user_id))
        user = await db.get(User, user_id)
        if user is not None:
            await db.delete(user)
        print(f"Removed stale client {client_id} (user {user_id}).")

    await db.commit()


async def seed_clients(db) -> None:
    client_role = await db.scalar(select(Role).where(Role.name == RoleName.CLIENT))
    if client_role is None:
        raise RuntimeError("CLIENT role is not seeded. Run alembic migrations first.")

    admin = await db.scalar(select(User).where(User.email == "admin@example.com"))
    created_by = admin.id if admin is not None else None

    for entry in SAMPLE_CLIENTS:
        existing = await db.scalar(select(User).where(User.email == entry["email"]))
        if existing is not None:
            print(f"{entry['email']} already exists, skipping.")
            continue

        user = User(email=entry["email"], password_hash=hash_password("Password123!"))
        db.add(user)
        await db.flush()

        db.add(UserRole(user_id=user.id, role_id=client_role.id))
        db.add(
            Client(
                user_id=user.id,
                first_name=entry["first_name"],
                last_name=entry["last_name"],
                phone_number=entry["phone_number"],
                timezone=entry["timezone"],
                created_by=created_by,
                updated_by=created_by,
            )
        )
        print(f"Created {entry['email']} ({entry['first_name']} {entry['last_name']}).")

    await db.commit()


async def main() -> None:
    async with SessionLocal() as db:
        await remove_stale_clients(db)
        await seed_clients(db)

    print("Done. Sample client password: Password123!")


if __name__ == "__main__":
    asyncio.run(main())
