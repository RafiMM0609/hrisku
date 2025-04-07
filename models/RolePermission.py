from sqlalchemy import Column, ForeignKey, Integer, Table, Boolean
from sqlalchemy.orm import relationship
from models import Base

RolePermission = Table(
    "role_permission",
    Base.metadata,
    Column(
        "id", 
        Integer, 
        primary_key=True, 
        nullable=False, 
        index=True
    ),
    Column(
        "role_id",
        Integer,
        ForeignKey("role.id"),
        nullable=False,
        index=True,
    ),
    Column(
        "permission_id",
        Integer,
        ForeignKey("permission.id"),
        nullable=False,
        index=True,
    ),
    Column(
        "isact",
        Boolean,
        nullable=False,
        server_default="true"
    ),
    Column(
        "isdel",
        Boolean,
        nullable=False,
        server_default="false"
    )
)
