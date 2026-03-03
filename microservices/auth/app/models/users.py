from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import String, LargeBinary, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ENUM as PGENUM

from app.core.database import Base
from .enums import UserRole


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid4
    )
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    hashed_password: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        PGENUM(UserRole, name="user_roles", create_type=True),
        nullable=False,
        default=UserRole.STUDENT,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email={self.email})>"
