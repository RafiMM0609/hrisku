from sqlalchemy import Column, String, ForeignKey, Integer, UUID, TIMESTAMP, func, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import uuid
from models import Base
from models.UserRole import UserRole
from models.ShiftSchedule import ShiftSchedule
from models.TimeSheet import TimeSheet
from models.Performance import Performance
from sqlalchemy.future import select
from datetime import date, timedelta
from sqlalchemy.sql import func

class User(Base):
    __tablename__ = "user"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    created_by = Column(String(36), nullable=False)
    updated_by = Column(String(36), nullable=False)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    photo = Column(String, nullable=True)
    nik = Column(String, nullable=True)
    phone = Column(String, nullable=False)
    address = Column(String, nullable=False)
    face_id = Column(String, nullable=False)
    client_id = Column(Integer,ForeignKey("client.id") ,nullable=False, index=True)
    outlet_id = Column(Integer,ForeignKey("client_outlet.id") ,nullable=False, index=True)
    password = Column(String, nullable=False)
    first_login = Column(String, nullable=False)
    birth_date = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP)
    isact = Column(Boolean, default=True)
    status = Column(Boolean, default=True)
    id_seq = Column(Integer, nullable=True)
    id_user = Column(String(10), nullable=True)

    # One  to Many
    client_user = relationship("Client", back_populates="user_client", foreign_keys=[client_id])
    user_shift = relationship("ShiftSchedule", back_populates="users", foreign_keys=[ShiftSchedule.emp_id])
    user_outlet = relationship("ClientOutlet", back_populates="outlet_user", foreign_keys=[outlet_id])
    contract_user = relationship("Contract", back_populates="users")
    attendance_user = relationship("Attendance", back_populates="users")
    leave_user = relationship("LeaveTable", back_populates="users")
    timesheet_user = relationship("TimeSheet", back_populates="users")
    performance_user = relationship("Performance", back_populates="users")
    # Many to Many
    roles = relationship("Role", secondary=UserRole, back_populates="users")