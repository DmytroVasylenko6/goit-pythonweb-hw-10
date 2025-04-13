import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.schemas import UserCreate

logger = logging.getLogger("rate_limiter")


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, user_id: int) -> User | None:
        stmt = select(User).filter(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        stmt = select(User).filter(User.username == username)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        stmt = select(User).filter(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, user: UserCreate, avatar_url: str = None) -> User:
        logger.info("Attempting to create user: %s", user.dict())
        try:
            db_user = User(
                **user.model_dump(exclude_unset=True, exclude={"password"}),
                hashed_password=user.password,
                avatar_url=avatar_url,
                is_verified=False,
            )
            self.db.add(db_user)
            await self.db.commit()
            logger.info("User successfully added to database")
            await self.db.refresh(db_user)
            return db_user
        except Exception as e:
            logger.error("Error creating user in repository: %s", str(e))
            await self.db.rollback()
            raise

    async def confirmed_email(self, email: str) -> None:
        user = await self.get_user_by_email(email)
        if user:
            user.is_verified = True
            await self.db.commit()

    async def update_avatar_url(self, email: str, url: str) -> User:
        user = await self.get_user_by_email(email)
        if user:
            user.avatar_url = url
            await self.db.commit()
            await self.db.refresh(user)
        return user
