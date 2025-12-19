"""FastAPI application entry point"""
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
    message_routes,
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

# Setup upload directory
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Mount static files
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Register route modules
app.include_router(auth_routes.router)
app.include_router(order_routes.router)
app.include_router(package_routes.router)
app.include_router(message_routes.router)
app.include_router(notification_routes.router)
app.include_router(review_routes.router)
app.include_router(resolution_routes.router)
app.include_router(analytics_routes.router)


@app.on_event("startup")
def startup_event():

    try:
        initialize_database()
    except Exception as e:
        print(f"[CRITICAL] Failed to initialize database: {e}")
        print("[WARN] Application started but database operations will fail")
        print("[INFO] Please check your database connection and restart the application")
