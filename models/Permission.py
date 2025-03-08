from sqlalchemy import Integer, Column, String, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from models import Base
from models.RolePermission import RolePermission
from models.Module import Module


class Permission(Base):
    __tablename__ = "permission"

    id = Column("id", Integer, primary_key=True, nullable=False, index=True)
    module_id = Column(
        "module_id",
        ForeignKey("module.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=True,
    )
    name = Column("name", String, nullable=False)
    isact = Column("isact", Boolean, default=True)
    order_id = Column("order_id", Integer, nullable=True)
    created_by = Column("created_by", ForeignKey("user.id"), nullable=True)
    updated_by = Column("updated_by", ForeignKey("user.id"), nullable=True)
    created_at = Column("created_at", DateTime(timezone=True))
    updated_at = Column("updated_at", DateTime(timezone=True))
    

    module = relationship(
        "Module", backref="permission_module", foreign_keys=[module_id]
    )
    # Many to One
    roles = relationship("Role", secondary=RolePermission, back_populates="permissions")
