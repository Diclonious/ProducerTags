from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os


# Database URL (use MySQL via mysqlconnector to avoid cryptography dependency)
DATABASE_URL = "mysql+pymysql://root:Anabela123!@localhost:3306/producer_tags"


def _build_engine(url: str):
    is_sqlite = url.startswith("sqlite:")
    connect_args = {"check_same_thread": False} if is_sqlite else {}
    return create_engine(
        url,
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",
        pool_pre_ping=not is_sqlite,
        future=True,
        connect_args=connect_args,
    )


# Create SQLAlchemy engine
engine = _build_engine(DATABASE_URL)


# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Declarative base for ORM models
Base = declarative_base()


# FastAPI dependency for DB sessions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


