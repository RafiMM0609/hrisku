from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean, and_
from sqlalchemy.orm import relationship
from models import Base
from models.UserRole import UserRole
from models.RolePermission import RolePermission  # Ensure this is correctly imported


class Role(Base):
    __tablename__ = "role"

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    created_by = Column(ForeignKey("user.id"), nullable=True)
    updated_by = Column(ForeignKey("user.id"), nullable=True)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    isact = Column(Boolean, default=True)

    # Many to Many
    users = relationship("User", secondary=UserRole, back_populates="roles")
    permissions = relationship(
        "Permission",
        secondary=RolePermission,
        primaryjoin=and_(
            RolePermission.c.role_id == id,
            RolePermission.c.isact == True
        ),
        back_populates="roles"
    )