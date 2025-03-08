from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Boolean
from models import Base


class Module(Base):
    __tablename__ = "module"

    id = Column(Integer, primary_key=True, nullable=False, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    created_by = Column(ForeignKey("user.id"), nullable=True)
    updated_by = Column(ForeignKey("user.id"), nullable=True)
    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    isact = Column(Boolean, default=True)
    order_id = Column(Integer, nullable=True)
