import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from core.constants import RoleName
from core.security import hash_password
from database.session import SessionLocal
from models.role import Role
from models.user import User
from models.user_role import UserRole


async def seed() -> None:
    async with SessionLocal() as db:
        existing = await db.scalar(select(User).where(User.email == "admin@example.com"))
        if existing is not None:
            print("Super Admin already exists, skipping.")
            return

        role = await db.scalar(select(Role).where(Role.name == RoleName.SUPER_ADMIN))
        if role is None:
            raise RuntimeError(
                "SUPER_ADMIN role not found. Run alembic migrations before seeding."
            )

        admin = User(
            email="admin@example.com",
            password_hash=hash_password("Password123!"),
        )
        db.add(admin)
        await db.flush()

        db.add(UserRole(user_id=admin.id, role_id=role.id))

        await db.commit()

    print("Super Admin created successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
