"""Database configuration and session management"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Import Base from domain layer (dependency inversion)
from app.domain.base import Base


# Database URL (use mysqlconnector driver per requirements.txt)
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+mysqlconnector://root:Anabela123!@localhost:3306/producer_tags")


def _build_engine(url: str):
    """Build SQLAlchemy engine with appropriate configuration"""
    is_sqlite = url.startswith("sqlite:")
    if is_sqlite:
        connect_args = {"check_same_thread": False}
    else:
        # MySQL connection args with timeout
        connect_args = {
            "connect_timeout": 5,
            "autocommit": False
        }
    
    return create_engine(
        url,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",
        pool_pre_ping=True,
        pool_recycle=1800,
        pool_timeout=5,  # Timeout for getting connection from pool
        max_overflow=0,
        future=True,
        connect_args=connect_args,
    )


# Create SQLAlchemy engine
engine = _build_engine(DATABASE_URL)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# FastAPI dependency for DB sessions
def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

