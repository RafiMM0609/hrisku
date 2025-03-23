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


class Performance(Base):
    __tablename__ = "performance"

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    emp_id = Column(String(36), ForeignKey("user.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("client.id"), nullable=False, index=True)
    date = Column(Date, nullable=True)
    rate = Column(Integer, nullable=True)
    softskill = Column(Integer, nullable=True)
    hardskill = Column(Integer, nullable=True)
    notes = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    created_by = Column(String(36), nullable=True)
    updated_by = Column(String(36), nullable=True)
    isact = Column(Boolean, default=True)

    # Many to Many
    users = relationship("User", back_populates="performance_user", foreign_keys=[emp_id])
    clients = relationship("Client", back_populates="performance_client", foreign_keys=[client_id])
