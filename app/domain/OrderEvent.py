from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, Text
from sqlalchemy.orm import relationship
from app.db.database import Base


class OrderEvent(Base):
    __tablename__ = "order_events"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), index=True, nullable=False)
    event_type = Column(String(50), nullable=False)  # e.g., 'revision_requested', 'completed', 'cancellation_requested', 'delivered', 'request_approved', 'request_rejected'
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Who triggered the event
    event_message = Column(Text, nullable=True)  # Main message for the event
    cancellation_reason = Column(String(100), nullable=True)  # Reason for cancellation
    cancellation_message = Column(Text, nullable=True)  # User's message for cancellation
    extension_days = Column(Integer, nullable=True)  # Extension days if applicable
    extension_reason = Column(Text, nullable=True)  # Extension reason if applicable
    
    order = relationship("Order", back_populates="events")
    user = relationship("User")
