from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from app.db.database import Base


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

    user = relationship("User", back_populates="orders")
    package = relationship("Package")
    tags = relationship("Tag", back_populates="order")
