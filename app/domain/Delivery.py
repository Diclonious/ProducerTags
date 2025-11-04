from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from app.db.database import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.Order import Order
    from app.domain.User import User


class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    delivery_number = Column(Integer, nullable=False)  # 1, 2, 3, etc.
    response_text = Column(Text, nullable=True)
    delivery_file = Column(String(255), nullable=True)
    delivered_at = Column(DateTime, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Admin who delivered
    
    # Relationships
    order = relationship("Order", back_populates="deliveries")
    user = relationship("User")
