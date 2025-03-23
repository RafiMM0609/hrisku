from sqlalchemy import (
    Column, 
    String, 
    Integer, 
    DateTime, 
    ForeignKey, 
    Boolean, 
    Date, 
    Time, 
    Numeric
)
from sqlalchemy.orm import relationship
from models import Base
from models.UserRole import UserRole
from models.RolePermission import RolePermission


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("client.id"), nullable=False, index=True)
    emp_id = Column(String(36), ForeignKey("user.id"), nullable=False, index=True)
    loc_id = Column(Integer, ForeignKey("client_outlet.id"), nullable=True)
    date = Column(Date, nullable=True)
    clock_in = Column(Time, nullable=True)
    clock_out = Column(Time, nullable=True)
    longitude = Column(Numeric(10, 6), nullable=True)
    latitude = Column(Numeric(10, 6), nullable=True)
    is_leave = Column(Boolean, default=False)
    created_by = Column(String(36), nullable=True)
    updated_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    isact = Column(Boolean, default=True)

    # Many to Many
    users = relationship("User", back_populates="attendance_user", foreign_keys=[emp_id])
    outlets = relationship("ClientOutlet", back_populates="attendance_outlet", foreign_keys=[loc_id])
