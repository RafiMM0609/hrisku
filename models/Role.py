from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from models import Base
from models.UserRole import UserRole
from models.RolePermission import RolePermission


class Role(Base):
    __tablename__ = "role"

    id = Column("id", Integer, primary_key=True, nullable=False, index=True)
    name = Column("name", String, nullable=False, index=True)
    description = Column("description", String, nullable=True)
    created_by = Column("created_by", ForeignKey("user.id"), nullable=True)
    updated_by = Column("updated_by", ForeignKey("user.id"), nullable=True)
    created_at = Column("created_at", DateTime(timezone=True))
    updated_at = Column("updated_at", DateTime(timezone=True))
    isact = Column("isact", Boolean, default=True)

    # Many to Many
    users = relationship("User", secondary=UserRole, back_populates="roles")
    permissions = relationship(
        "Permission", secondary=RolePermission, back_populates="roles"
    )
