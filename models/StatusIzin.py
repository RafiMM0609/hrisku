from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from models import Base


class StatusIzin(Base):
    __tablename__ = "master_status_izin"

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    name = Column(String, nullable=False, index=True)

    leave_status = relationship("LeaveTable", back_populates="status_leave")

