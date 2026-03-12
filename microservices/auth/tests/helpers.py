from sqlalchemy import select

from app.core.security import verify_password
from app.models.users import User
from app.models.enums import UserRole


async def assert_user_in_db(db_session, username, email, password):
    """Утверждение: пользователь с username существует и данные совпадают."""
    result = await db_session.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    assert user is not None
    assert user.email == email
    assert verify_password(password, user.hashed_password) is True
    assert user.role == UserRole.STUDENT
