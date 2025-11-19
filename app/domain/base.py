"""Base class for domain entities - framework agnostic"""
from sqlalchemy.ext.declarative import declarative_base

# Declarative base that doesn't depend on infrastructure
# This will be used by SQLAlchemy in infrastructure layer
Base = declarative_base()

