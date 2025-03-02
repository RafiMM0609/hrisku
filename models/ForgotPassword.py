from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from models import Base


class ForgotPassword(Base):
    __tablename__ = "forgot_password"

    id = Column("id", Integer, primary_key=True, nullable=False, index=True)
    user_id = Column("user_id", ForeignKey("user.id"), nullable=False, index=True)
    token = Column("token", String(200), nullable=False)
    created_date = Column("created_date", DateTime(timezone=True))

    # many to one
    user = relationship("User", backref="forgot_password_user", foreign_keys=[user_id])
