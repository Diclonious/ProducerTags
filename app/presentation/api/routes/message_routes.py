"""Messaging system routes"""
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from starlette.responses import RedirectResponse
from starlette.status import HTTP_302_FOUND
from pathlib import Path

from app.infrastructure.database import get_db
from app.presentation.api.dependencies.auth import get_service_container, require_login
from app.application.dto.message import MessageCreate
from app.domain.entities.User import User

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter()


@router.post("/order/{order_id}/messages/send")
async def send_message(
    request: Request,
    order_id: int,
    message_text: str = Form(None),
    current_user: User = Depends(require_login),
    container = Depends(get_service_container)
):
    
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

    message_data = MessageCreate(message_text=message_text.strip())

    try:
        message = container.message_use_case.send_message(
            order_id,
            current_user.id,
            message_data,
            current_user.is_admin
        )


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
    
    try:
        messages = container.message_use_case.get_messages_for_order(
            order_id,
            current_user.id,
            current_user.is_admin
        )

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
    
    count = container.message_use_case.get_unread_count(
        current_user.id,
        current_user.is_admin
    )
    return JSONResponse(content={"count": count})


@router.get("/messages/notifications")
async def get_message_notifications(
    request: Request,
    current_user: User = Depends(require_login),
    container = Depends(get_service_container)
):
    """Get recent messages grouped by sender and order"""
    from app.domain.entities.Message import Message
    from app.domain.entities.Order import Order
    from sqlalchemy.orm import joinedload


    query = container.db.query(Message).join(Order).options(
        joinedload(Message.sender),
        joinedload(Message.order)
    ).filter(Message.sender_id != current_user.id)

    if not current_user.is_admin:
        query = query.filter(Order.user_id == current_user.id)

    all_messages = query.order_by(Message.created_at.desc()).limit(50).all()


    message_groups = {}
    for msg in all_messages:
        key = (msg.sender_id, msg.order_id)
        if key not in message_groups:
            message_groups[key] = {
                "messages": [],
                "unread_count": 0,
                "latest_message": None
            }

        message_groups[key]["messages"].append(msg)
        if not msg.is_read:
            message_groups[key]["unread_count"] += 1

        if (message_groups[key]["latest_message"] is None or
            (msg.created_at and message_groups[key]["latest_message"].created_at and
             msg.created_at > message_groups[key]["latest_message"].created_at)):
            message_groups[key]["latest_message"] = msg


    grouped_messages = []
    for key, group_data in message_groups.items():
        latest_msg = group_data["latest_message"]
        if latest_msg:
            msg_timestamp = latest_msg.created_at.timestamp() if latest_msg.created_at else 0
            sender = container.user_repository.get_by_id(latest_msg.sender_id)

            grouped_messages.append({
                "sender_id": latest_msg.sender_id,
                "order_id": latest_msg.order_id,
                "sender_name": sender.username if sender else "User",
                "sender_avatar": sender.avatar if sender else None,
                "message_text": latest_msg.message_text[:100] + "..." if len(latest_msg.message_text) > 100 else latest_msg.message_text,
                "created_at": latest_msg.created_at.strftime("%b %d, %I:%M %p") if latest_msg.created_at else "",
                "time_ago": _get_time_ago(latest_msg.created_at) if latest_msg.created_at else "Just now",
                "unread_count": group_data["unread_count"],
                "has_unread": group_data["unread_count"] > 0,
                "latest_message_id": latest_msg.id,
                "_sort_timestamp": msg_timestamp
            })


    grouped_messages_sorted = sorted(
        grouped_messages,
        key=lambda x: (not x["has_unread"], -x["_sort_timestamp"])
    )

    for msg in grouped_messages_sorted:
        del msg["_sort_timestamp"]

    return JSONResponse(content={"messages": grouped_messages_sorted})


@router.post("/messages/mark-all-read")
async def mark_all_messages_read(
    request: Request,
    current_user: User = Depends(require_login),
    container = Depends(get_service_container)
):
   
    count = container.message_use_case.mark_all_read(
        current_user.id,
        current_user.is_admin
    )
    return JSONResponse(content={"success": True})


def _get_time_ago(dt):
    
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

