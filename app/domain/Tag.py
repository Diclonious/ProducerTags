from sqlalchemy import Column, Integer, String, ForeignKey
from app.db.database import Base

from sqlalchemy.orm import relationship

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    name = Column(String(255), nullable=False)
    mood = Column(String(50), nullable=False)

    # Relationship to order
    order = relationship("Order", back_populates="tags")
