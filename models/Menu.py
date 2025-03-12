from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from models import Base


class Menu(Base):
    __tablename__ = "menu"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    icon = Column(String)
    url = Column(String)
    parent_id = Column(
        ForeignKey("menu.id", onupdate="CASCADE", ondelete="CASCADE"),
    )
    permission_id = Column(
        ForeignKey("permission.id", onupdate="CASCADE", ondelete="CASCADE"),
        index=True,
    )
    is_has_child = Column(Boolean, nullable=True)
    isact = Column(Boolean, default=True)
    is_show = Column(Boolean, default=True)
    order_id = Column(Integer, nullable=True)
    created_by = Column(ForeignKey("user.id"), nullable=True)
    updated_by = Column(ForeignKey("user.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), index=True)
    updated_at = Column(DateTime(timezone=True))

    # many to one
    permission = relationship(
        "Permission", backref="menu_permission", foreign_keys=[permission_id]
    )
    parent = relationship(
        "Menu",
        back_populates="child",
        foreign_keys=[parent_id],
        remote_side=[id],
        cascade="all,delete",
    )

    # one to many
    child = relationship("Menu", back_populates="parent")
