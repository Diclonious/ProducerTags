from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from app.db.database import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.User import User
    from app.domain.Package import Package
    from app.domain.Tag import Tag


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
    
    # Dispute system fields
    request_type = Column(String(50), nullable=True)  # 'revision', 'cancellation', 'extend_delivery'
    request_message = Column(Text, nullable=True)
    cancellation_reason = Column(String(100), nullable=True)
    cancellation_message = Column(Text, nullable=True)
    extension_days = Column(Integer, nullable=True)
    extension_reason = Column(Text, nullable=True)
    requested_by_admin = Column(String(10), nullable=True)  # 'true' or 'false'

    user = relationship("User", back_populates="orders")
    package = relationship("Package")
    tags = relationship("Tag", back_populates="order")
