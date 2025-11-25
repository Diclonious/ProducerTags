"""Database configuration and session management"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

from app.domain.base import Base

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+mysqlconnector://root:Anabela123!@localhost:3306/producer_tags")


def _build_engine(url: str):
    """Build SQLAlchemy engine with appropriate configuration"""
    is_sqlite = url.startswith("sqlite:")
    if is_sqlite:
        connect_args = {"check_same_thread": False}
    else:
        connect_args = {
            "connect_timeout": 5,
            "autocommit": False
        }

    return create_engine(
        url,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",
        pool_pre_ping=True,
        pool_recycle=1800,
        pool_timeout=5,
        max_overflow=0,
        future=True,
        connect_args=connect_args,
    )


engine = _build_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

