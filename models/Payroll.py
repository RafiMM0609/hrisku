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


class Payroll(Base):
    __tablename__ = "payroll"

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    emp_id = Column(String(36), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("client.id"), nullable=True, index=True)
    monthly_paid = Column(Numeric(10, 6), nullable=True)
    total_allowances = Column(Numeric(10, 6), nullable=True)
    total_bpjs = Column(Numeric(10, 6), nullable=True)
    total_tax = Column(Numeric(10, 6), nullable=True)
    net_salary = Column(Numeric(10, 6), nullable=True)
    payment_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    created_by = Column(String(36), nullable=True)
    updated_by = Column(ForeignKey("user.id"), nullable=True)
    isact = Column(Boolean, default=True)
    file = Column(String(255), nullable=True)

    # Many to One
    clients = relationship("Client", back_populates="client_payroll", foreign_keys=[client_id])


