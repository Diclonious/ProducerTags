from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


# MySQL connection URL (root / Anabela123!) to database `producer_tags`
DATABASE_URL = "mysql+pymysql://root:Anabela123!@localhost:3306/producer_tags"


# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True,  # proactively checks connection health
    future=True,
)


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


