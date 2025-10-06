from sqlalchemy import Column, Integer, String, ForeignKey
from app.db.database import Base

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    file_path = Column(String(255), nullable=False)
    details = Column(String(255), nullable=True)