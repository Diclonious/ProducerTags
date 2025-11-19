from sqlalchemy import Column, Integer, String, Float
from app.domain.base import Base


class Package(Base):
    __tablename__ = "packages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    price = Column(Float, nullable=False)
    delivery_days = Column(Integer, nullable=False)
    tag_count = Column(Integer, nullable=False)
    description = Column(String(255), nullable=True)
