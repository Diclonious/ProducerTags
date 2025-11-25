"""Authentication dependencies for FastAPI routes"""
from fastapi import Request, HTTPException, Depends
from starlette.status import HTTP_302_FOUND
from sqlalchemy.orm import Session
from app.infrastructure.database import get_db
from app.domain.entities.User import User
from app.application.services.service_container import ServiceContainer
from pathlib import Path


def get_service_container(db: Session = Depends(get_db)) -> ServiceContainer:
    """Get service container with all dependencies"""
    BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
    UPLOAD_DIR = BASE_DIR / "uploads"
    return ServiceContainer(db, UPLOAD_DIR)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    """Get current user from session"""
    user_id = request.session.get("user_id")
    if not user_id:
        return None

    container = get_service_container(db)
    return container.user_repository.get_by_id(user_id)


def require_login(request: Request, current_user: User | None = Depends(get_current_user)):
    """Require user to be logged in"""
    if not current_user:
        from starlette.responses import RedirectResponse
        next_url = str(request.url.path)
        return RedirectResponse(url=f"/login?next={next_url}", status_code=HTTP_302_FOUND)
    return current_user


def require_admin(request: Request, current_user: User = Depends(require_login)):
    """Require user to be admin"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Forbidden")
    return current_user

