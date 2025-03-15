from sqlalchemy import (
    Column, 
    String, 
    Integer, 
    DateTime, 
    ForeignKey, 
    Boolean, 
    Float, 
    Date
)
from sqlalchemy.orm import relationship
from models import Base
from models.ClientPayment import ClientPayment


class Client(Base):
    __tablename__ = "client"

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    brand = Column(String, nullable=True)
    product_service = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    cs_person = Column(String, nullable=True)
    cs_number = Column(String, nullable=True)
    cs_email = Column(String, nullable=True)
    address = Column(String, nullable=True)
    website = Column(String, nullable=True)
    fee_agency = Column(Float, nullable=True)
    basic_salary = Column(Float, nullable=True)
    created_by = Column(String(36), nullable=True)
    updated_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    isact = Column(Boolean, default=True)
    payment_status = Column(Boolean, default=True)
    due_date_payment = Column(Date, nullable=True)
    id_client = Column(String, nullable=True)
    
    # Relation
    user_client = relationship("User", back_populates="client_user")
    outlets = relationship("ClientOutlet", back_populates="client")
    bpjs = relationship("Bpjs", back_populates="client")
    allowances = relationship("Allowances", back_populates="client")
    client_payments = relationship("ClientPayment", back_populates="clients")

