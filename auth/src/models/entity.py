import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, Table
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from werkzeug.security import check_password_hash, generate_password_hash

from db.postgres import Base

UserRole = Table(
    "user_role",
    Base.metadata,
    Column(
        "user_id",
        UUID(as_uuid=True),
        ForeignKey("users.user.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "role_id",
        UUID(as_uuid=True),
        ForeignKey("users.role.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    schema="users",
)


class User(Base):
    __tablename__ = "user"
    __table_args__ = {"schema": "users"}

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    login = Column(String(225), unique=True, nullable=False)
    password = Column(String(225), nullable=False)
    first_name = Column(String(225))
    last_name = Column(String(225))
    email = Column(String(225))
    created_at = Column(
        DateTime(timezone=True), default=datetime.now(timezone.utc)
    )

    # Relationships
    logins = relationship(
        "LoginRecord",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    auth_provider = relationship(
        "AuthProvider",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    roles = relationship(
        "Role",
        secondary=UserRole,
        back_populates="users",
        lazy="selectin",
        cascade="all, delete",
    )

    def __init__(
        self,
        login: str,
        password: str,
        first_name: str | None = None,
        last_name: str | None = None,
        email: str | None = None,
    ) -> None:
        self.login = login
        self.password = generate_password_hash(password)
        self.first_name = first_name
        self.last_name = last_name
        self.email = email

    def update_password(self, password: str):
        self.password = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(str(self.password), password)

    def __repr__(self) -> str:
        return f"<User {self.login}>"


class AuthProvider(Base):
    __tablename__ = "auth_provider"
    __table_args__ = {"schema": "users"}

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    service = Column(String(255), nullable=False)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey(User.id, ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    sub = Column(String(255))

    # Relationships
    user = relationship("User", back_populates="auth_provider", lazy="selectin")


class Role(Base):
    __tablename__ = "role"
    __table_args__ = {"schema": "users"}

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    name = Column(String(50), nullable=False, unique=True)
    description = Column(String(255))

    # Relationships
    users = relationship(
        "User",
        secondary=UserRole,
        back_populates="roles",
        lazy="selectin",
        passive_deletes=True,
    )


class LoginRecord(Base):
    __tablename__ = "login_record"
    __table_args__ = {"schema": "users"}

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey(User.id, ondelete="CASCADE"),
        nullable=False,
    )
    login_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.now(timezone.utc),
    )
    user_agent = Column(String(255))

    # Relationships
    user = relationship("User", back_populates="logins", lazy="selectin")
