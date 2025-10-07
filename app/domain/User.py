from sqlalchemy import Column, Integer, String
from app.db.database import Base
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False, unique=True)
    email = Column(String(100), nullable=False, unique=True)
    password = Column(String(100), nullable=False) 

    # Domain logic can also go here if needed
    def check_password(self, password: str) -> bool:
        return self.password == password 