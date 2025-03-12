from sqlalchemy import (
    Column, 
    String, 
    Integer, 
    DateTime, 
    Date,
    ForeignKey, 
    Boolean, 
    Float,
)
from sqlalchemy.orm import relationship
from models import Base
from models.UserRole import UserRole
from models.RolePermission import RolePermission


class ClientPayment(Base):
    __tablename__ = "client_payment"

    id = Column(String(36), primary_key=True, nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("client.id"), nullable=False, index=True)
    amount = Column(Float, nullable=True)
    date = Column(Date, nullable=True)
    status = Column(Integer, nullable=True)
    # created_by = Column(ForeignKey("user.id"), nullable=True)
    # updated_by = Column(ForeignKey("user.id"), nullable=True)
    # created_at = Column(DateTime(timezone=True))
    # updated_at = Column(DateTime(timezone=True))
    isact = Column(Boolean, default=True)

    # Many to One
    clients = relationship("Client", back_populates="client_payments", foreign_keys=[client_id])
