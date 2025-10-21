from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from app.db.database import Base
from passlib.context import CryptContext

# Use Argon2 instead of bcrypt
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    avatar = Column(String(255), nullable=True)
    orders = relationship("Order", back_populates="user")

    def set_password(self, password: str):
        # Argon2 has no 72-byte limit, so no truncation needed
        self.hashed_password = pwd_context.hash(password)

    def check_password(self, password: str):
        return pwd_context.verify(password, self.hashed_password)
