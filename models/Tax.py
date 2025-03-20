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


class Tax(Base):
    __tablename__ = "tax"

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    client_id = Column(Integer,ForeignKey("client.id"), nullable=False, index=True)
    name = Column(String, nullable=True)
    percent = Column(Numeric(10, 6), nullable=True)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    created_by = Column(String(36), nullable=True)
    updated_by = Column(String(36), nullable=True)
    isact = Column(Boolean, default=True)

    # Relation
    clients = relationship("Client", back_populates="client_tax", foreign_keys=[client_id])

