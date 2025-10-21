from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.Order import Order


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    name = Column(String(255), nullable=False)
    mood = Column(String(50), nullable=False)

    order = relationship("Order", back_populates="tags")
