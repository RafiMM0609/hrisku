from sqlalchemy import Column, String, UUID, TIMESTAMP, func, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import uuid
from models import Base
from models.UserRole import UserRole
from models.Role import Role

class User(Base):
    __tablename__ = "user"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    # id = Column("id",UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    photo = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    face_id = Column(String, nullable=False)
    password = Column(String, unique=True, nullable=False)
    birth_date = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP)
    isact = Column(Boolean, default=True)

    # Many to Many
    roles = relationship("Role", secondary=UserRole, back_populates="users")