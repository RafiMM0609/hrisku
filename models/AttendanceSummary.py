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
from models.LeaveTable import LeaveTable


class AttendanceSummary(Base):
    __tablename__ = "attendance_summary"

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("client.id"), nullable=False, index=True)
    emp_id = Column(String(36), ForeignKey("user.id"), nullable=False, index=True)
    contract_id = Column(Integer, ForeignKey("contract.id"), nullable=True)
    month_date = Column(Date, nullable=True)
    total_work_days = Column(Integer, nullable=True)
    total_attendance = Column(Integer, nullable=True)
    attendance_percentage = Column(Numeric(5, 2), nullable=True)
    monthly_salary = Column(Numeric(12, 8), nullable=True)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    isact = Column(Boolean, default=True)

    # Many to Many
    users = relationship("User", back_populates="sumat_user", foreign_keys=[emp_id])
    clients = relationship("Client", back_populates="sumat_client", foreign_keys=[client_id])
