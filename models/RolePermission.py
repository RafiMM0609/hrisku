from sqlalchemy import Column, ForeignKey, Integer, Table
from sqlalchemy.orm import relationship
from models import Base

RolePermission = Table(
    "role_permission",
    Base.metadata,
    Column("id", Integer, primary_key=True, nullable=False, index=True),
    Column(
        "role_id",
        Integer,
        ForeignKey("role.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    Column(
        "permission_id",
        Integer,
        ForeignKey("permission.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
)
