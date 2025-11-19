from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.domain.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.entities.Delivery import Delivery


class DeliveryFile(Base):
    __tablename__ = "delivery_files"

    id = Column(Integer, primary_key=True, index=True)
    delivery_id = Column(Integer, ForeignKey("deliveries.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=True)
    file_size = Column(Integer, nullable=True)  # in bytes
    uploaded_at = Column(DateTime, nullable=False)
    
    # Relationships
    delivery = relationship("Delivery", back_populates="files")

