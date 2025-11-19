from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from app.domain.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.entities.Order import Order
    from app.domain.entities.User import User
    from app.domain.entities.DeliveryFile import DeliveryFile


class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    delivery_number = Column(Integer, nullable=False)  # 1, 2, 3, etc.
    response_text = Column(Text, nullable=True)
    delivery_file = Column(String(255), nullable=True)  # Keep for backward compatibility
    delivered_at = Column(DateTime, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Admin who delivered
    
    # Relationships
    order = relationship("Order", back_populates="deliveries")
    user = relationship("User")
    files = relationship("DeliveryFile", back_populates="delivery", cascade="all, delete-orphan")
