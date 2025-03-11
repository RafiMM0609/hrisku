from sqlalchemy import (
    Column, 
    String, 
    Integer, 
    DateTime, 
    ForeignKey, 
    Boolean, 
    DECIMAL, 
    Date
)
from sqlalchemy.orm import relationship
from models import Base


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
    fee_agency = Column(DECIMAL(5, 2), nullable=True)
    created_by = Column(String(36), nullable=True)
    updated_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    isact = Column(Boolean, default=True)
    due_date_payment = Column(Date, default=True)
    due_date_employee = Column(Date, default=True)

    # Relation
    user_client = relationship("User", back_populates="client_user")

