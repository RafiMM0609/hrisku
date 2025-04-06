import uuid
from sqlalchemy import (
    Column,
    DateTime,
    Numeric, 
    String, 
    Integer, 
    Date,
    ForeignKey, 
    Boolean, 
    Float,
)
from sqlalchemy.orm import relationship
from models import Base
from models.StatusPayment import StatusPayment


class NationalHoliday(Base):
    __tablename__ = "national_holidays"

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    name = Column(String(36), nullable=False, index=True)
    date = Column(Date, nullable=True)
    note = Column(String, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    isact = Column(Boolean, default=True)
    is_national = Column(Boolean, default=True)
    client_id = Column(Integer, ForeignKey("client.id"), nullable=True, index=True)

    # Many to One
    clients = relationship("Client", back_populates="client_holiday", foreign_keys=[client_id])


