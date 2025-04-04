from sqlalchemy import (
    Column,
    Numeric, 
    String, 
    Integer, 
    DateTime, 
    ForeignKey, 
    Boolean, 
    DECIMAL, 
    Date,
    Float
)
from sqlalchemy.orm import relationship
from models import Base
from models.Payroll import Payroll


class EmployeeTax(Base):
    __tablename__ = "employee_tax"

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    emp_id = Column(String(36), nullable=False, index=True)
    name = Column(String, nullable=True)
    amount = Column(Numeric(10, 6), nullable=True)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    created_by = Column(String(36), nullable=True)
    updated_by = Column(String(36), nullable=True)
    isact = Column(Boolean, default=True)
    client_id = Column(Integer,ForeignKey("client.id"), nullable=False, index=True)

    # Relation
    client = relationship("Client", back_populates="employee_tax")
    # user_payroll = relationship("Payroll", back_populates="user_to_tax")

