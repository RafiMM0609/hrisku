from sqlalchemy import Column, ForeignKey, Integer, Table, String
from sqlalchemy.dialects.postgresql import UUID
from models import Base

UserRole = Table(
    "user_role",
    Base.metadata,
    Column("id", Integer, primary_key=True, nullable=False),
    Column("emp_id", String(36), ForeignKey("user.id"), nullable=False),
    Column("role_id", Integer, ForeignKey("role.id"), nullable=False)
)
