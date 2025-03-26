from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import relationship
from models import Base
from sqlalchemy.sql import func


class ForgotPassword(Base):
    __tablename__ = "forgot_password"

    id = Column("id", Integer, primary_key=True, nullable=False, index=True)
    user_id = Column("user_id", ForeignKey("user.id"), nullable=False, index=True)
    token = Column("token", String(255), nullable=False)
    created_date = Column("created_date", TIMESTAMP, server_default=func.now())
