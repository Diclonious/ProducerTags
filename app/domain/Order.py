from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.database import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    package_id = Column(Integer, ForeignKey("packages.id"), nullable=False)  # 👈 Add this
    file_path = Column(String(255), nullable=False)
    details = Column(String(255), nullable=True)

    # Relationships
    package = relationship("Package")