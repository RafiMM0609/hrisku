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
from models.StatusIzin import StatusIzin


class LeaveTable(Base):
    __tablename__ = "leave_table"

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    emp_id = Column(String(36), ForeignKey("user.id"), nullable=False, index=True)
    atendance_id = Column(Integer, ForeignKey("attendance.id"), nullable=True)
    type = Column(String, nullable=True)
    status = Column(Integer, ForeignKey("master_status_izin.id"),nullable=True)
    note = Column(String, nullable=True)
    evidence = Column(String, nullable=True)    
    approval_date = Column(Date, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_by = Column(String(36), nullable=True)
    updated_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    isact = Column(Boolean, default=True)

    # Many to Many
    users = relationship("User", back_populates="leave_user", foreign_keys=[emp_id])
    attendances = relationship("Attendance", back_populates="attendance_leave", foreign_keys=[atendance_id])
    status_leave = relationship("StatusIzin", back_populates="leave_status", foreign_keys=[status])
