from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean, Time
from sqlalchemy.orm import relationship
from models import Base
from models.UserRole import UserRole
from models.RolePermission import RolePermission


class ShiftSchedule(Base):
    __tablename__ = "shift_schedule"

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    emp_id = Column(String(36), ForeignKey("user.id"), nullable=False, index=True)
    workdays = Column(Integer, nullable=True)
    day = Column(String, nullable=True)
    type = Column(String, nullable=True)
    time_start = Column(Time, nullable=True)
    time_end = Column(Time, nullable=True)
    client_id = Column(Integer, nullable=True)
    created_by = Column(ForeignKey("user.id"), nullable=True)
    updated_by = Column(ForeignKey("user.id"), nullable=True)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    isact = Column(Boolean, default=True)

    # Many to Many
    users = relationship("User", back_populates="user_shift", foreign_keys=[emp_id])
