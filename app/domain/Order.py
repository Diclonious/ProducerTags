from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

from sqlalchemy.orm import relationship


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    package_id = Column(Integer, ForeignKey("packages.id"), nullable=False)
    details = Column(String(255), nullable=True)

    # Relationship to tags
    tags = relationship("Tag", back_populates="order", cascade="all, delete-orphan")
