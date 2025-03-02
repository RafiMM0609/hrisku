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
    created_by_id = Column("created_by_id", ForeignKey("user.id"), nullable=True)
    updated_by_id = Column("updated_by_id", ForeignKey("user.id"), nullable=True)
    created_at = Column("created_at", DateTime(timezone=True))
    updated_at = Column("updated_at", DateTime(timezone=True))
    is_active = Column("is_active", Boolean, default=False)

    # Many to one
    created_by = relationship(
        "User", backref="role_created_by", foreign_keys=[created_by_id]
    )
    updated_by = relationship(
        "User", backref="role_updated_by", foreign_keys=[updated_by_id]
    )

    # Many to Many
    users = relationship("User", secondary=UserRole, back_populates="roles")
    permissions = relationship(
        "Permission", secondary=RolePermission, back_populates="roles"
    )
