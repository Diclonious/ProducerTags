"""
FastAPI Router Example with SQLAlchemy Model and Database Connection

This example uses ACTUAL code snippets from the project to demonstrate:
- Domain Entity (SQLAlchemy Model) - Message entity
- DTOs (Data Transfer Objects) for request/response validation
- FastAPI Router with database operations
- Database connection using dependency injection

For Diploma Thesis Documentation
"""

# ============================================================================
# 1. DOMAIN ENTITY (SQLAlchemy Model)
# ============================================================================
"""
File: app/domain/entities/Message.py

This is the actual Message domain entity from the project.
It represents a message in the order-based chat communication system.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.domain.base import Base
from datetime import datetime


class Message(Base):
    """Message model for order-based chat communication"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    message_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_read = Column(Boolean, default=False)

    # Relationships
    order = relationship("Order", back_populates="messages")
    sender = relationship("User", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, order_id={self.order_id}, sender={self.sender_id})>"


# ============================================================================
# 2. DTOs (Data Transfer Objects) for Request/Response Validation
# ============================================================================
"""
File: app/application/dto/message.py

These are the actual DTOs used in the project for Message operations.
DTOs use Pydantic for request/response validation and serialization.
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class MessageCreate(BaseModel):
    """DTO for creating a new message"""
    message_text: str


class MessageResponse(BaseModel):
    """DTO for message response (includes all fields from database)"""
    id: int
    order_id: int
    sender_id: int
    message_text: str
    created_at: datetime
    is_read: bool

    class Config:
        """Pydantic configuration"""
        from_attributes = True  # Allows conversion from SQLAlchemy models


# ============================================================================
# 3. DATABASE CONNECTION AND DEPENDENCY
# ============================================================================
"""
File: app/infrastructure/database/database.py

This is the actual database connection setup from the project.
"""

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


def get_db():
    """
    FastAPI dependency for getting database session
    
    This function is used as a dependency in route handlers.
    It yields a database session and ensures it's closed after use.
    
    Usage:
        @router.get("/messages")
        def get_messages(db: Session = Depends(get_db)):
            return db.query(Message).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# 4. REPOSITORY IMPLEMENTATION
# ============================================================================
"""
File: app/infrastructure/repositories/message_repository_impl.py

This is the actual repository implementation using SQLAlchemy.
It implements the repository interface pattern for data access.
"""

from typing import List
from sqlalchemy.orm import Session, joinedload
from app.domain.entities.Message import Message
from app.domain.entities.Order import Order
from app.domain.repositories.message_repository import IMessageRepository


class MessageRepository(IMessageRepository):
    """SQLAlchemy implementation of Message repository"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_order_id(self, order_id: int) -> List[Message]:
        """Get all messages for an order with sender relationship loaded"""
        return (
            self.db.query(Message)
            .options(joinedload(Message.sender))
            .filter(Message.order_id == order_id)
            .order_by(Message.created_at.asc())
            .all()
        )

    def create(self, message: Message) -> Message:
        """Create a new message"""
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_unread_count(self, user_id: int, is_admin: bool = False) -> int:
        """Get count of unread messages for a user"""
        query = self.db.query(Message).join(Order).filter(
            Message.is_read == False,
            Message.sender_id != user_id
        )

        if not is_admin:
            query = query.filter(Order.user_id == user_id)

        return query.count()


# ============================================================================
# 5. FASTAPI ROUTER WITH DATABASE OPERATIONS
# ============================================================================
"""
File: app/presentation/api/routes/message_routes.py

This is the actual FastAPI router implementation from the project.
It demonstrates how to use the database connection and repository pattern.
"""

from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from starlette.responses import RedirectResponse
from starlette.status import HTTP_302_FOUND
from pathlib import Path
from sqlalchemy.orm import Session

# Import database dependency
from app.infrastructure.database import get_db

# Import dependencies for authentication and service container
from app.presentation.api.dependencies.auth import get_service_container, require_login

# Import DTOs
from app.application.dto.message import MessageCreate

# Import domain entity
from app.domain.entities.User import User

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Create router instance
router = APIRouter()


@router.post("/order/{order_id}/messages/send")
async def send_message(
    request: Request,
    order_id: int,
    message_text: str = Form(None),
    current_user: User = Depends(require_login),
    container = Depends(get_service_container)
):
    """
    Send a message in order chat
    
    This endpoint demonstrates:
    - Using dependency injection for database access (get_service_container)
    - Authentication dependency (require_login)
    - Form data handling
    - JSON response for AJAX requests
    - Redirect response for form submissions
    """
    # Handle different request formats
    if not message_text:
        try:
            form_data = await request.form()
            message_text = form_data.get("message_text", "")
        except:
            try:
                body = await request.json()
                message_text = body.get("message_text", "")
            except:
                message_text = ""

    if not message_text or not message_text.strip():
        raise HTTPException(status_code=400, detail="Message text is required")

    # Create DTO from input
    message_data = MessageCreate(message_text=message_text.strip())

    try:
        # Use service container to access use case
        message = container.message_use_case.send_message(
            order_id,
            current_user.id,
            message_data,
            current_user.is_admin
        )

        # Handle different response types (JSON for AJAX, redirect for forms)
        accept_header = request.headers.get("accept", "")
        content_type = request.headers.get("content-type", "")

        if "application/json" in accept_header or "application/json" in content_type:
            sender = container.user_repository.get_by_id(current_user.id)
            return JSONResponse(content={
                "success": True,
                "message": {
                    "id": message.id,
                    "order_id": message.order_id,
                    "sender_id": message.sender_id,
                    "sender_name": sender.username if sender else "User",
                    "sender_avatar": sender.avatar if sender else None,
                    "message_text": message.message_text,
                    "created_at": message.created_at.strftime("%b %d, %I:%M %p") if message.created_at else "",
                    "is_read": message.is_read
                }
            })
        else:
            return RedirectResponse(f"/order/{order_id}#chat", status_code=HTTP_302_FOUND)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/order/{order_id}/messages")
async def get_messages(
    request: Request,
    order_id: int,
    current_user: User = Depends(require_login),
    container = Depends(get_service_container)
):
    """
    Get all messages for an order (AJAX endpoint)
    
    This endpoint demonstrates:
    - Querying messages using the repository pattern
    - Loading relationships (joinedload)
    - Returning JSON responses
    """
    try:
        # Use service container to access use case
        messages = container.message_use_case.get_messages_for_order(
            order_id,
            current_user.id,
            current_user.is_admin
        )

        # Transform domain entities to response format
        messages_data = []
        for msg in messages:
            sender = container.user_repository.get_by_id(msg.sender_id)
            messages_data.append({
                "id": msg.id,
                "sender_id": msg.sender_id,
                "sender_name": sender.username if sender else "User",
                "sender_avatar": sender.avatar if sender else None,
                "message_text": msg.message_text,
                "created_at": msg.created_at.strftime("%b %d, %I:%M %p") if msg.created_at else "",
                "is_admin": sender.is_admin if sender else False
            })

        return JSONResponse(content={"messages": messages_data})
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/messages/unread-count")
async def get_unread_messages_count(
    request: Request,
    current_user: User = Depends(require_login),
    container = Depends(get_service_container)
):
    """
    Get count of unread messages
    
    This endpoint demonstrates:
    - Direct database query using repository
    - Simple JSON response
    """
    count = container.message_use_case.get_unread_count(
        current_user.id,
        current_user.is_admin
    )
    return JSONResponse(content={"count": count})


# ============================================================================
# 6. MAIN APPLICATION SETUP
# ============================================================================
"""
File: app/main.py

This is how the router is registered in the main FastAPI application.
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path

from app.infrastructure.database.startup import initialize_database

# Import route modules
from app.presentation.api.routes import (
    auth_routes,
    order_routes,
    package_routes,
    message_routes,  # Our message router
    notification_routes,
    review_routes,
    resolution_routes,
    analytics_routes
)

# Create FastAPI application
app = FastAPI(
    title="TaggedByBelle",
    description="Order management system",
    version="2.0.0"
)

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Add session middleware
import os
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "change-me-in-production"))

# Mount static files
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Register route modules
app.include_router(auth_routes.router)
app.include_router(order_routes.router)
app.include_router(package_routes.router)
app.include_router(message_routes.router)  # Register message router
app.include_router(notification_routes.router)
app.include_router(review_routes.router)
app.include_router(resolution_routes.router)
app.include_router(analytics_routes.router)


@app.on_event("startup")
def startup_event():
    """Initialize database on application startup"""
    try:
        initialize_database()
    except Exception as e:
        print(f"[CRITICAL] Failed to initialize database: {e}")
        print("[WARN] Application started but database operations will fail")


# ============================================================================
# 7. USAGE EXAMPLES
# ============================================================================

"""
API Endpoints:

1. Send Message:
   POST /order/{order_id}/messages/send
   Form Data: message_text="Hello, this is a message"
   Headers: Cookie with session (requires login)

2. Get Messages for Order:
   GET /order/{order_id}/messages
   Returns: JSON with list of messages

3. Get Unread Count:
   GET /messages/unread-count
   Returns: JSON with count of unread messages

Testing with curl:
   # First login to get session cookie
   curl -X POST "http://localhost:8000/users/login" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=user&password=pass" \
        -c cookies.txt

   # Send a message
   curl -X POST "http://localhost:8000/order/1/messages/send" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "message_text=Hello World" \
        -b cookies.txt

   # Get messages
   curl "http://localhost:8000/order/1/messages" \
        -b cookies.txt

   # Get unread count
   curl "http://localhost:8000/messages/unread-count" \
        -b cookies.txt
"""
