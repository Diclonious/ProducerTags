from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base
from sqlalchemy import Column, DateTime


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # ✅ must have ForeignKey
    package_id = Column(Integer, nullable=False)
    details = Column(String(255), nullable=True)
    due_date = Column(DateTime, nullable=True)

    tags = relationship("Tag", back_populates="order", cascade="all, delete-orphan")
    user = relationship("User", back_populates="orders")  # ✅ back_populates matches User.orders
