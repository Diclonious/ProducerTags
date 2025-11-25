from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from app.domain.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.entities.User import User
    from app.domain.entities.Package import Package
    from app.domain.entities.Tag import Tag


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    package_id = Column(Integer, ForeignKey("packages.id"))
    details = Column(Text)
    due_date = Column(DateTime)
    status = Column(String(50), default="Active")
    response = Column(Text, nullable=True)

    delivery_file = Column(String(255), nullable=True)
    review = Column(Integer, nullable=True)
    review_text = Column(Text, nullable=True)
    completed_date = Column(DateTime, nullable=True)
    cancelled_date = Column(DateTime, nullable=True)


    request_type = Column(String(50), nullable=True)
    request_message = Column(Text, nullable=True)
    cancellation_reason = Column(String(100), nullable=True)
    cancellation_message = Column(Text, nullable=True)
    extension_days = Column(Integer, nullable=True)
    extension_reason = Column(Text, nullable=True)
    requested_by_admin = Column(String(10), nullable=True)

    user = relationship("User", back_populates="orders")
    package = relationship("Package")
    tags = relationship("Tag", back_populates="order")
    deliveries = relationship("Delivery", back_populates="order", cascade="all, delete-orphan")
    events = relationship("OrderEvent", back_populates="order", cascade="all, delete-orphan", order_by="OrderEvent.created_at.desc()")
    messages = relationship("Message", back_populates="order", cascade="all, delete-orphan", order_by="Message.created_at.asc()")
    notifications = relationship("Notification", back_populates="order", cascade="all, delete-orphan")
