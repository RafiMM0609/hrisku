from sqlalchemy import (
    Column, 
    String, 
    Integer, 
    DateTime, 
    ForeignKey, 
    Boolean, 
    Date,
    Float,
    Numeric
)
from sqlalchemy.orm import relationship
from models import Base


class Bpjs(Base):
    __tablename__ = "bpjs"

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    client_id = Column(Integer,ForeignKey("client.id"), nullable=False, index=True)
    name = Column(String, nullable=True)
    company_contribution = Column(Float, nullable=True)
    employee_contribution = Column(Float, nullable=True)
    amount = Column(Numeric(10, 6), nullable=True)
    created_by = Column(String(36), nullable=True)
    updated_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    isact = Column(Boolean, default=True)

    # Relation
    client = relationship("Client", back_populates="bpjs")

