"""Resets the password for every existing TRAINER account to a known value
for local development, since bcrypt hashes can't be reversed to recover
whatever password an account was originally created with. Also backfills a
missing `user_roles` TRAINER assignment where a `trainer_profiles` row exists
without one - such accounts can log in but have zero usable roles.

Safe to re-run.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from core.constants import RoleName
from core.security import hash_password
from database.session import SessionLocal
from models.role import Role
from models.trainer_profile import TrainerProfile
from models.user import User
from models.user_role import UserRole

NEW_PASSWORD = "Password123!"


async def main() -> None:
    async with SessionLocal() as db:
        rows = (
            await db.execute(select(TrainerProfile, User).join(User, User.id == TrainerProfile.user_id))
        ).all()

        if not rows:
            print("No trainer accounts found.")
            return

        trainer_role = await db.scalar(select(Role).where(Role.name == RoleName.TRAINER))
        if trainer_role is None:
            raise RuntimeError("TRAINER role is not seeded. Run alembic migrations first.")

        for trainer, user in rows:
            user.password_hash = hash_password(NEW_PASSWORD)

            has_trainer_role = await db.scalar(
                select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == trainer_role.id)
            )
            if has_trainer_role is None:
                db.add(UserRole(user_id=user.id, role_id=trainer_role.id))
                print(f"Backfilled missing TRAINER role for {user.email}.")

            print(f"Reset password for {user.email} (trainer_id={trainer.id}).")

        await db.commit()

    print(f"Done. All trainer passwords set to: {NEW_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(main())
