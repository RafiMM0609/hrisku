import uuid
from sqlalchemy import Boolean, Column, String, Integer
from sqlalchemy.dialects.postgresql import UUID
from typing import List
from models import Base

class UserToken(Base):
    __tablename__ = "user_token"

    id = Column(
        "id", Integer, primary_key=True, index=True
    )
    user_id = Column("user_id", UUID, nullable=False, index=True)
    token = Column("token", String, nullable=False)
    is_active = Column("is_active", Boolean, default=True)