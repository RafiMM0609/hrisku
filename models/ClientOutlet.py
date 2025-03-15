from sqlalchemy import(
    Column, 
    String, 
    Integer, 
    DateTime, 
    ForeignKey, 
    Boolean,
    Float
)
from sqlalchemy.orm import relationship
from models import Base
from models.UserRole import UserRole
from models.RolePermission import RolePermission
from models.User import User


class ClientOutlet(Base):
    __tablename__ = "client_outlet"

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    client_id = Column(String, ForeignKey("client.id"), nullable=False,index=True)
    name = Column(String, nullable=True)
    type = Column(String, nullable=True)
    region = Column(String, nullable=True)
    area = Column(String, nullable=True)
    address = Column(String, nullable=True)
    longitude = Column(Float, nullable=True)
    latitude = Column(Float, nullable=True)
    created_by = Column(ForeignKey("user.id"), nullable=True)
    updated_by = Column(ForeignKey("user.id"), nullable=True)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    isact = Column(Boolean, default=True)

    client = relationship("Client", back_populates="outlets")
    outlet_user = relationship("User", back_populates="user_outlet", foreign_keys=[User.outlet_id])
