from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from models import Base


class StatusPayment(Base):
    __tablename__ = "master_status_payment"

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    name = Column(String, nullable=False, index=True)

    payments = relationship("ClientPayment", back_populates="status_payment")