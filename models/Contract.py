from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean, Date
from sqlalchemy.orm import relationship
from models import Base
from models.UserRole import UserRole
from models.RolePermission import RolePermission


class Contract(Base):
    __tablename__ = "contract"

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    emp_id = Column(String(36), ForeignKey("user.id"), nullable=False, index=True)
    start = Column(Date, nullable=True)
    end = Column(Date, nullable=True)
    period = Column(Integer, nullable=True)
    file = Column(String(255), nullable=True)
    created_by = Column(String(36), nullable=True)
    updated_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    isact = Column(Boolean, default=True)

    # Many to Many
    users = relationship("User", back_populates="contract_user", foreign_keys=[emp_id])
