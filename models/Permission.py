from sqlalchemy import Integer, Column, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from models import Base
from models.RolePermission import RolePermission


class Permission(Base):
    __tablename__ = "permission"

    id = Column("id", Integer, primary_key=True, nullable=False, index=True)
    module_id = Column(
        "module_id",
        ForeignKey("module.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=True,
    )
    permission = Column("permission", String, nullable=False)
    is_active = Column("is_active", Boolean, default=False)
    
    # Many to One
    module = relationship(
        "Module", backref="permission_module", foreign_keys=[module_id]
    )
    roles = relationship("Role", secondary=RolePermission, back_populates="permissions")
