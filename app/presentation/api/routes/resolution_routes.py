
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from starlette.status import HTTP_302_FOUND
from datetime import datetime, timedelta
from app.infrastructure.utils.time_utils import get_current_time
from sqlalchemy.orm import joinedload
from pathlib import Path

from app.infrastructure.database import get_db
from app.presentation.api.dependencies.auth import get_service_container, require_login
from app.application.dto.order import ResolutionRequest
from app.domain.entities.User import User
from app.domain.entities.Order import Order
from app.domain.entities.OrderEvent import OrderEvent

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter()


@router.get("/order/{order_id}/resolution")
async def resolution_center(
    request: Request,
    order_id: int,
    current_user: User = Depends(require_login),
    container = Depends(get_service_container)
):
   
    order = (
        container.db.query(Order)
        .options(joinedload(Order.user), joinedload(Order.package))
        .filter(Order.id == order_id)
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")


    if not current_user.is_admin and order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    return templates.TemplateResponse(
        "resolution_center.html",
        {
            "request": request,
            "order": order,
            "is_admin": current_user.is_admin,
        }
    )


@router.post("/order/{order_id}/resolution/submit")
async def submit_resolution_request(
    request: Request,
    order_id: int,
    request_type: str = Form(...),
    message: str = Form(""),
    cancellation_reason: str = Form(""),
    cancellation_message: str = Form(""),
    extension_days: int = Form(0),
    extension_reason: str = Form(""),
    current_user: User = Depends(require_login),
    container = Depends(get_service_container)
):
    

    if current_user.is_admin:
        order = container.order_repository.get_by_id(order_id)
    else:
        order = container.order_repository.get_by_user_and_id(current_user.id, order_id)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")


    if request_type == "revision" and order.status in ["Active", "In dispute", "Revision"]:
        raise HTTPException(
            status_code=400,
            detail="Cannot request revision at this time. Revision requests can only be made for delivered orders that are not already in revision or dispute."
        )


    if request_type == "cancel" or request_type == "cancellation":

        if order.status == "In dispute":
            raise HTTPException(
                status_code=400,
                detail="Cannot request cancellation when order is already in dispute. Please resolve the existing dispute first."
            )

        resolution_data = ResolutionRequest(
            request_type="cancellation",
            cancellation_reason=cancellation_reason,
            cancellation_message=cancellation_message
        )
        try:
            container.order_use_case.request_cancellation(order_id, current_user.id, resolution_data)
            return RedirectResponse(f"/order/{order_id}", status_code=HTTP_302_FOUND)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    elif request_type == "extension" or request_type == "extend_delivery":
        if not extension_days or extension_days <= 0:
            raise HTTPException(status_code=400, detail="Extension days must be greater than 0")


        if order.status == "In dispute":
            raise HTTPException(
                status_code=400,
                detail="Cannot request extension when order is already in dispute. Please resolve the existing dispute first."
            )

        resolution_data = ResolutionRequest(
            request_type="extend_delivery",
            extension_days=extension_days,
            extension_reason=extension_reason
        )
        try:
            container.order_use_case.request_extension(order_id, current_user.id, resolution_data)
            return RedirectResponse(f"/order/{order_id}", status_code=HTTP_302_FOUND)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    elif request_type == "dispute":
        resolution_data = ResolutionRequest(
            request_type="dispute",
            dispute_message=message
        )
        try:
            container.order_use_case.open_dispute(order_id, current_user.id, resolution_data)
            return RedirectResponse(f"/order/{order_id}", status_code=HTTP_302_FOUND)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    elif request_type == "revision":

        if order.status != "Delivered":
            raise HTTPException(status_code=400, detail="Cannot request revision in this state")


        order.due_date = get_current_time() + timedelta(hours=24)

        order.status = "Revision"
        container.order_repository.update(order)


        event = OrderEvent(
            order_id=order.id,
            event_type="revision_requested",
            user_id=current_user.id,
            event_message=message or "Revision requested",
            created_at=get_current_time()
        )
        container.db.add(event)
        container.db.commit()


        admins = container.user_repository.get_admins()
        for admin in admins:
            container.notification_use_case.create_notification(
                admin.id, order.id, "revision_requested",
                "Revision Requested",
                f"{current_user.username} requested a revision on order #{order.id}"
            )

        return RedirectResponse(f"/order/{order_id}", status_code=HTTP_302_FOUND)

    else:
        raise HTTPException(status_code=400, detail="Invalid request type")


@router.post("/order/{order_id}/resolution/approve")
async def approve_resolution_request(
    request: Request,
    order_id: int,
    current_user: User = Depends(require_login),
    container = Depends(get_service_container)
):
    
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Forbidden")

    order = container.order_repository.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    try:
        container.order_use_case.approve_resolution_request(order_id, current_user.id)
        return RedirectResponse(f"/order/{order_id}/resolution", status_code=HTTP_302_FOUND)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/order/{order_id}/resolution/reject")
async def reject_resolution_request(
    request: Request,
    order_id: int,
    rejection_message: str = Form(""),
    current_user: User = Depends(require_login),
    container = Depends(get_service_container)
):
    
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Forbidden")

    order = container.order_repository.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    try:
        container.order_use_case.reject_resolution_request(order_id, current_user.id, rejection_message)
        return RedirectResponse(f"/order/{order_id}/resolution", status_code=HTTP_302_FOUND)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

