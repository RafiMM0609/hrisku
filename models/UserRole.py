from sqlalchemy import Column, ForeignKey, Integer, Table, Boolean
from sqlalchemy.orm import relationship
from models import Base

RolePermission = Table(
    "user_role",
    Base.metadata,
    Column("id", Integer, primary_key=True, nullable=False, index=True),
    Column(
        "role_id",
        Integer,
        ForeignKey("role.id"),
        nullable=False,
        index=True,
    ),
    Column(
        "emp_id",
        Integer,
        ForeignKey("user.id"),
        nullable=False,
        index=True,
    ),
    Column(
        "isact",
        Boolean,
        nullable=False,
        server_default="true"
    )
)
