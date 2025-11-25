from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, Text
from sqlalchemy.orm import relationship
from app.domain.base import Base


class OrderEvent(Base):
    __tablename__ = "order_events"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), index=True, nullable=False)
    event_type = Column(String(50), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    event_message = Column(Text, nullable=True)
    cancellation_reason = Column(String(100), nullable=True)
    cancellation_message = Column(Text, nullable=True)
    extension_days = Column(Integer, nullable=True)
    extension_reason = Column(Text, nullable=True)

    order = relationship("Order", back_populates="events")
    user = relationship("User")
