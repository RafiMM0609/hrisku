from sqlalchemy import Integer, Column, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from models import Base
from models.RolePermission import RolePermission


class Permission(Base):
    __tablename__ = "permission"

    id = Column("id", Integer, primary_key=True, nullable=False, index=True)
    name = Column("name", String, nullable=False)
    isact = Column("isact", Boolean, default=True)
    order_id = Column("order_id", Integer, nullable=True)
    created_by_id = Column("created_by_id", ForeignKey("user.id"), nullable=True)
    updated_by_id = Column("updated_by_id", ForeignKey("user.id"), nullable=True)
    created_at = Column("created_at", DateTime(timezone=True))
    updated_at = Column("updated_at", DateTime(timezone=True))
    
    # Many to One
    roles = relationship("Role", secondary=RolePermission, back_populates="permissions")
