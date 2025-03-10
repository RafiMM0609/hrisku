import uuid
from sqlalchemy import Boolean, Column, String, Integer
from sqlalchemy.dialects.postgresql import UUID
from typing import List
from models import Base

class UserToken(Base):
    __tablename__ = "user_token"

    id = Column(Integer, primary_key=True, index=True)
    emp_id = Column(String(36), nullable=False, index=True)
    token = Column(String, nullable=False)
    isact = Column(Boolean, default=True)
