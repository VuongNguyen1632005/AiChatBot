from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional
from app.models.sql.user import User

class UserRepository:
    """
    Repository chịu trách nhiệm thực thi các truy vấn cơ sở dữ liệu cho thực thể User.
    """
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """
        Lấy thông tin người dùng dựa trên địa chỉ email.
        """
        result = await db.execute(select(User).filter(User.email == email))
        return result.scalars().first()

    @staticmethod
    async def create_user(db: AsyncSession, user_data: dict) -> User:
        """
        Tạo mới một bản ghi người dùng trong cơ sở dữ liệu.
        """
        db_user = User(**user_data)
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """
        Lấy thông tin người dùng dựa trên địa chỉ email.
        """
        return await UserRepository.get_user_by_email(db, email)

    @staticmethod
    async def update_password(db: AsyncSession, email: str, hashed_password: str) -> None:
        """
        Cập nhật mật khẩu mới cho người dùng.
        """
        user = await UserRepository.get_user_by_email(db, email)
        if user:
            user.password_hash = hashed_password
            db.add(user)
            await db.commit()

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """
        Lấy thông tin người dùng theo ID.
        """
        result = await db.execute(select(User).filter(User.id == user_id))
        return result.scalars().first()

    @staticmethod
    async def activate_user(db: AsyncSession, user_id: int) -> None:
        """
        Kích hoạt tài khoản người dùng: set email_verified=True, status='ACTIVE'.
        """
        result = await db.execute(select(User).filter(User.id == user_id))
        user = result.scalars().first()
        if user:
            user.email_verified = True
            user.status = "ACTIVE"
            db.add(user)
            await db.commit()
