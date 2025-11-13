from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime


class Notification(Base):
    """Notification model for user notifications"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=True)
    notification_type = Column(String(50), nullable=False)
    # Types: order_placed, revision_requested, cancellation_requested, review_left, 
    #        order_completed, extension_approved, delivered, revision_approved, 
    #        cancellation_approved, extension_requested
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    order = relationship("Order", back_populates="notifications")
    
    def __repr__(self):
        return f"<Notification(id={self.id}, type={self.notification_type}, user_id={self.user_id})>"

