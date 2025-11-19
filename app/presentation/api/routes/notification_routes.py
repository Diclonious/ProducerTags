"""Notification system routes"""
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path

from app.infrastructure.database import get_db
from app.presentation.api.dependencies.auth import get_service_container, require_login
from app.domain.entities.User import User

router = APIRouter()


def _get_time_ago(dt):
    """Helper to get human-readable time difference"""
    from datetime import datetime
    from app.infrastructure.utils.time_utils import get_current_time
    now = get_current_time()
    diff = now - dt
    
    if diff.days > 7:
        return dt.strftime("%b %d")
    elif diff.days > 0:
        return f"{diff.days}d ago"
    elif diff.seconds >= 3600:
        hours = diff.seconds // 3600
        return f"{hours}h ago"
    elif diff.seconds >= 60:
        minutes = diff.seconds // 60
        return f"{minutes}m ago"
    else:
        return "Just now"


@router.get("/notifications")
async def get_notifications(
    request: Request,
    current_user: User = Depends(require_login),
    container = Depends(get_service_container)
):
    """Get all notifications for current user (AJAX endpoint)"""
    notifications = container.notification_use_case.get_notifications(current_user.id)
    
    notifications_data = []
    for notif in notifications:
        notifications_data.append({
            "id": notif.id,
            "order_id": notif.order_id,
            "type": notif.notification_type,
            "title": notif.title,
            "message": notif.message,
            "is_read": notif.is_read,
            "created_at": notif.created_at.strftime("%b %d, %I:%M %p") if notif.created_at else "",
            "time_ago": _get_time_ago(notif.created_at) if notif.created_at else "Just now"
        })
    
    return JSONResponse(content={"notifications": notifications_data})


@router.get("/notifications/unread-count")
async def get_unread_count(
    request: Request,
    current_user: User = Depends(require_login),
    container = Depends(get_service_container)
):
    """Get count of unread notifications"""
    count = container.notification_use_case.get_unread_count(current_user.id)
    return JSONResponse(content={"count": count})


@router.post("/notifications/{notification_id}/mark-read")
async def mark_notification_read(
    request: Request,
    notification_id: int,
    current_user: User = Depends(require_login),
    container = Depends(get_service_container)
):
    """Mark a notification as read"""
    success = container.notification_use_case.mark_as_read(notification_id, current_user.id)
    return JSONResponse(content={"success": success})


@router.post("/notifications/mark-all-read")
async def mark_all_notifications_read(
    request: Request,
    current_user: User = Depends(require_login),
    container = Depends(get_service_container)
):
    """Mark all notifications as read"""
    count = container.notification_use_case.mark_all_read(current_user.id)
    return JSONResponse(content={"success": True})

