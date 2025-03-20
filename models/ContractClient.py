from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean, Date
from sqlalchemy.orm import relationship
from models import Base
from models.UserRole import UserRole
from models.RolePermission import RolePermission


class ContractClient(Base):
    __tablename__ = "contract_client"

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("client.id"),nullable=False, index=True)
    start = Column(Date, nullable=True)
    end = Column(Date, nullable=True)
    manager_signature = Column(String(255), nullable=True)
    technical_signature = Column(String(255), nullable=True)
    created_by = Column(String(36), nullable=True)
    updated_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    isact = Column(Boolean, default=True)

    # Many to Many
    clients = relationship("Client", back_populates="contract_clients", foreign_keys=[client_id])
