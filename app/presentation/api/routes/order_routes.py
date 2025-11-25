"""Order management routes"""
from fastapi import APIRouter, Request, Form, Depends, UploadFile, File, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from starlette.responses import RedirectResponse
from starlette.status import HTTP_302_FOUND
from typing import List
from datetime import datetime, timedelta
from app.infrastructure.utils.time_utils import get_current_time
from sqlalchemy.orm import Session, joinedload
from pathlib import Path

from app.infrastructure.database import get_db
from app.presentation.api.dependencies.auth import (
    get_service_container, require_login, require_admin
)
from app.application.dto.order import OrderCreate, PaymentInfo, OrderReview, ResolutionRequest
from app.domain.entities.User import User
from app.domain.entities.Order import Order
from app.domain.entities.Tag import Tag
from app.domain.entities.Delivery import Delivery
from app.domain.entities.DeliveryFile import DeliveryFile
from app.domain.entities.OrderEvent import OrderEvent
from app.domain.entities.Message import Message

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter()


def update_late_orders(container):
    """Update orders that are past due date"""
    container.order_repository.update_late_orders()


@router.get("/order/new")
async def new_order(
    request: Request,
    container = Depends(get_service_container)
):
    """Show package selection page"""
    packages = container.package_use_case.get_all_packages()
    return templates.TemplateResponse(
        "choosepackage.html",
        {"request": request, "packages": packages}
    )


@router.post("/order/new")
async def select_package(
    request: Request,
    package_id: int = Form(...),
    container = Depends(get_service_container)
):
    """Select a package and show order form"""
    package = container.package_use_case.get_package_by_id(package_id)
    if not package:
        return RedirectResponse(url="/order/new", status_code=HTTP_302_FOUND)

    return templates.TemplateResponse(
        "order_form.html",
        {"request": request, "package": package}
    )


@router.post("/order/submit")
async def submit_order(
    request: Request,
    package_id: int = Form(...),
    details: str = Form(None),
    card_number: str = Form(...),
    card_holder: str = Form(...),
    card_expiry: str = Form(...),
    card_cvv: str = Form(...),
    current_user: User = Depends(require_login),
    container = Depends(get_service_container)
):
    """Submit a new order"""

    card_number_clean = card_number.replace(" ", "").replace("-", "")
    card_expiry_clean = card_expiry.replace("/", "")

    package = container.package_use_case.get_package_by_id(package_id)
    if not package:
        return RedirectResponse(url="/order/new", status_code=HTTP_302_FOUND)


    if not card_number_clean or len(card_number_clean) < 13 or len(card_number_clean) > 19:
        return templates.TemplateResponse(
            "order_form.html",
            {
                "request": request,
                "package": package,
                "error": "Invalid card number. Please check your payment information."
            }
        )

    if not card_holder or len(card_holder.strip()) < 3:
        return templates.TemplateResponse(
            "order_form.html",
            {
                "request": request,
                "package": package,
                "error": "Invalid cardholder name. Please check your payment information."
            }
        )

    if not card_expiry_clean or len(card_expiry_clean) != 4:
        return templates.TemplateResponse(
            "order_form.html",
            {
                "request": request,
                "package": package,
                "error": "Invalid expiry date. Please use MM/YY format."
            }
        )


    try:
        expiry_month = int(card_expiry_clean[:2])
        expiry_year = int(card_expiry_clean[2:])
        current_date = get_current_time()
        current_year = current_date.year % 100
        current_month = current_date.month

        if expiry_month < 1 or expiry_month > 12:
            raise ValueError("Invalid month")

        if expiry_year < current_year or (expiry_year == current_year and expiry_month < current_month):
            return templates.TemplateResponse(
                "order_form.html",
                {
                    "request": request,
                    "package": package,
                    "error": "Card has expired. Please use a valid card."
                }
            )
    except (ValueError, IndexError):
        return templates.TemplateResponse(
            "order_form.html",
            {
                "request": request,
                "package": package,
                "error": "Invalid expiry date format. Please use MM/YY format."
            }
        )

    if not card_cvv or len(card_cvv) < 3 or len(card_cvv) > 4:
        return templates.TemplateResponse(
            "order_form.html",
            {
                "request": request,
                "package": package,
                "error": "Invalid CVV. Please check your payment information."
            }
        )


    form = await request.form()
    tags = [t.strip() for t in form.getlist("tags") if t.strip()]
    moods = [m.strip() for m in form.getlist("moods")]


    payment_info = PaymentInfo(
        card_number=card_number,
        card_holder=card_holder,
        card_expiry=card_expiry,
        card_cvv=card_cvv
    )


    order_data = OrderCreate(
        package_id=package_id,
        details=details,
        tags=tags,
        moods=moods,
        payment=payment_info
    )

    try:

        order = container.order_use_case.create_order(current_user.id, order_data)


        for tag_value, mood_value in zip(tags, moods):
            tag = Tag(order_id=order.id, name=tag_value, mood=mood_value)
            container.db.add(tag)
        container.db.commit()

        return RedirectResponse(url="/myorders", status_code=HTTP_302_FOUND)
    except ValueError as e:
        return templates.TemplateResponse(
            "order_form.html",
            {
                "request": request,
                "package": package,
                "error": str(e)
            }
        )


@router.get("/myorders")
async def my_orders(
    request: Request,
    current_user: User = Depends(require_login),
    container = Depends(get_service_container)
):
    """User's orders dashboard"""

    update_late_orders(container)


    orders = container.order_use_case.get_orders_for_user(current_user.id)


    now = get_current_time()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    spent_eur = container.order_repository.get_revenue(current_user.id, "Completed", month_start)

    return templates.TemplateResponse(
        "myorders.html",
        {
            "request": request,
            "orders": orders,
            "spent_month": round(spent_eur, 2),
            "month_name": now.strftime('%B')
        }
    )


@router.get("/myorders-admin")
async def my_orders_admin(
    request: Request,
    current_user: User = Depends(require_admin),
    container = Depends(get_service_container)
):
    """Admin orders dashboard"""
    update_late_orders(container)

    orders = container.order_use_case.get_all_orders()


    now = get_current_time()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    earned_eur = container.order_repository.get_revenue(None, "Completed", month_start)


    try:
        request.session["admin_month_earnings"] = round(earned_eur, 2)
    except Exception:
        pass

    return templates.TemplateResponse(
        "myorders-admin.html",
        {
            "request": request,
            "orders": orders,
            "is_admin": True,
            "earned_month": round(earned_eur, 2),
            "month_name": now.strftime('%B')
        }
    )


@router.get("/order/{order_id}")
async def view_order(
    request: Request,
    order_id: int,
    current_user: User = Depends(require_login),
    container = Depends(get_service_container)
):
    """View order details"""
    update_late_orders(container)


    order = (
        container.db.query(Order)
        .options(
            joinedload(Order.tags),
            joinedload(Order.user),
            joinedload(Order.package),
            joinedload(Order.deliveries).joinedload(Delivery.user),
            joinedload(Order.deliveries).joinedload(Delivery.files),
            joinedload(Order.events).joinedload(OrderEvent.user),
            joinedload(Order.messages).joinedload(Message.sender)
        )
        .filter(Order.id == order_id)
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")


    if not current_user.is_admin and order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")


    timeline_items = []

    if order.deliveries:
        for delivery in order.deliveries:
            if delivery.delivered_at:
                timeline_items.append({
                    'type': 'delivery',
                    'delivery': delivery,
                    'date': delivery.delivered_at
                })

    if order.events:
        for event in order.events:
            if event.event_type != 'delivered' and event.created_at:
                timeline_items.append({
                    'type': 'event',
                    'event': event,
                    'date': event.created_at
                })

    if order.status == 'Delivered' and order.delivery_file and not order.deliveries:
        legacy_date = order.due_date or get_current_time()
        timeline_items.append({
            'type': 'legacy_delivery',
            'order': order,
            'date': legacy_date
        })

    def get_sort_key(item):
        date = item['date']
        if date is None:
            date = datetime.min
        if not isinstance(date, datetime):
            date = datetime.min

        priority = 0
        if item.get('type') == 'event':
            event = item.get('event')
            if event:
                if event.event_type == 'delivery_date_updated':
                    priority = 1
                elif event.event_type == 'request_approved':
                    priority = 0

        return (date, priority)

    timeline_items.sort(key=get_sort_key, reverse=False)


    if order.messages:
        for msg in order.messages:
            if msg.sender_id != current_user.id and not msg.is_read:
                msg.is_read = True
        container.db.commit()


    admin_user = None
    if not current_user.is_admin:
        admin_user = container.user_repository.get_admins()[0] if container.user_repository.get_admins() else None

    file_url = None
    if order.delivery_file:
        file_url = request.url_for("uploads", path=order.delivery_file)

    return templates.TemplateResponse(
        "order_detail.html",
        {
            "request": request,
            "order": order,
            "file_url": file_url,
            "is_admin": current_user.is_admin,
            "timeline_items": timeline_items,
            "messages": order.messages if order.messages else [],
            "admin_user": admin_user,
        }
    )


@router.post("/order/{order_id}/complete")
async def mark_order_complete(
    request: Request,
    order_id: int,
    current_user: User = Depends(require_login),
    container = Depends(get_service_container)
):
    """Mark an order as complete"""
    try:
        order = container.order_use_case.complete_order(order_id, current_user.id)
        return RedirectResponse(url=f"/order/{order_id}/review", status_code=302)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/order/{order_id}/deliver")
async def admin_deliver_order(
    request: Request,
    order_id: int,
    response_text: str = Form(...),
    files: List[UploadFile] = File(...),
    current_user: User = Depends(require_admin),
    container = Depends(get_service_container)
):
    """Admin deliver an order"""
    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required")

    order = container.order_repository.get_by_id(order_id)
    if not order or order.status not in ["Active", "Revision", "Late"]:
        raise HTTPException(status_code=400, detail="Cannot deliver in this state")


    delivery_count = container.db.query(Delivery).filter(Delivery.order_id == order_id).count()
    delivery_number = delivery_count + 1


    saved_files = []
    primary_filename = None

    for file in files:
        filename = container.file_storage.save_uploaded_file(file, "delivery")
        file_path = container.file_storage.get_file_path(filename)
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        saved_files.append({
            'filename': filename,
            'original_filename': file.filename,
            'size': len(content)
        })

        if primary_filename is None:
            primary_filename = filename


    delivery = Delivery(
        order_id=order_id,
        delivery_number=delivery_number,
        response_text=response_text,
        delivery_file=primary_filename,
        delivered_at=get_current_time(),
        user_id=current_user.id
    )
    container.db.add(delivery)
    container.db.flush()


    for file_info in saved_files:
        delivery_file = DeliveryFile(
            delivery_id=delivery.id,
            filename=file_info['filename'],
            original_filename=file_info['original_filename'],
            file_size=file_info['size'],
            uploaded_at=get_current_time()
        )
        container.db.add(delivery_file)


    order.status = "Delivered"
    order.response = response_text
    order.delivery_file = primary_filename
    container.order_repository.update(order)


    event = OrderEvent(
        order_id=order.id,
        event_type="delivered",
        user_id=current_user.id,
        event_message=response_text,
        created_at=get_current_time()
    )
    container.db.add(event)
    container.db.commit()


    container.notification_use_case.create_notification(
        order.user_id, order.id, "delivered",
        "Order Delivered",
        f"Your order #{order.id} has been delivered!"
    )

    return RedirectResponse(url="/myorders-admin", status_code=HTTP_302_FOUND)


@router.post("/order/{order_id}/request-revision")
async def user_request_revision(
    request: Request,
    order_id: int,
    revision_text: str = Form(...),
    current_user: User = Depends(require_login),
    container = Depends(get_service_container)
):
    """User request revision"""
    order = container.order_repository.get_by_id(order_id)
    if not order or order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    if order.status != "Delivered":
        raise HTTPException(status_code=400, detail="Cannot request revision in this state")


    if order.package and order.package.delivery_days:
        order.due_date = get_current_time() + timedelta(hours=24)

    order.status = "Revision"
    container.order_repository.update(order)


    event = OrderEvent(
        order_id=order.id,
        event_type="revision_requested",
        user_id=current_user.id,
        event_message=revision_text,
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

    return RedirectResponse("/myorders", status_code=HTTP_302_FOUND)


@router.get("/order/{order_id}/review")
async def review_order(
    request: Request,
    order_id: int,
    current_user: User = Depends(require_login),
    container = Depends(get_service_container)
):
    """Show review form"""
    order = container.order_repository.get_by_id(order_id)
    if not order or order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    if order.status != "Completed":
        raise HTTPException(status_code=400, detail="Cannot review this order")

    return templates.TemplateResponse(
        "review_form.html",
        {"request": request, "order": order}
    )


@router.post("/order/{order_id}/review")
async def submit_review(
    request: Request,
    order_id: int,
    review_text: str = Form(...),
    rating: int = Form(...),
    current_user: User = Depends(require_login),
    container = Depends(get_service_container)
):
    """Submit a review"""
    review_data = OrderReview(review=rating, review_text=review_text)

    try:
        order = container.order_use_case.submit_review(order_id, current_user.id, review_data)
        return RedirectResponse(url="/myorders", status_code=302)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/completed-orders")
async def completed_orders(
    request: Request,
    current_user: User = Depends(require_login),
    container = Depends(get_service_container)
):
    """View completed orders"""
    if current_user.is_admin:
        orders = container.order_repository.get_by_status("Completed")
    else:
        orders = container.order_repository.get_by_user_and_status(current_user.id, "Completed")

    orders.sort(key=lambda x: x.due_date or datetime.min, reverse=True)

    return templates.TemplateResponse(
        "completed_orders.html",
        {
            "request": request,
            "orders": orders,
            "is_admin": current_user.is_admin
        }
    )


@router.get("/order/{order_id}/download-delivered-file/{file_or_delivery_id}")
async def download_delivered_file(
    request: Request,
    order_id: int,
    file_or_delivery_id: int,
    current_user: User = Depends(require_login),
    container = Depends(get_service_container)
):
    """Download a delivered file"""
    order = container.order_repository.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")


    delivery_file = container.db.query(DeliveryFile).filter(
        DeliveryFile.id == file_or_delivery_id
    ).first()

    if delivery_file:
        delivery = container.db.query(Delivery).filter(
            Delivery.id == delivery_file.delivery_id,
            Delivery.order_id == order_id
        ).first()

        if not delivery:
            raise HTTPException(status_code=404, detail="Delivery file not found")

        file_path = container.file_storage.get_file_path(delivery_file.filename)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found on server")

        return FileResponse(
            path=str(file_path),
            filename=delivery_file.original_filename or delivery_file.filename,
            media_type="application/octet-stream"
        )


    delivery = container.db.query(Delivery).filter(
        Delivery.id == file_or_delivery_id,
        Delivery.order_id == order_id
    ).first()

    if not delivery or not delivery.delivery_file:
        raise HTTPException(status_code=404, detail="Delivery file not found")

    file_path = container.file_storage.get_file_path(delivery.delivery_file)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on server")

    return FileResponse(
        path=str(file_path),
        filename=delivery.delivery_file,
        media_type="application/octet-stream"
    )


@router.get("/order/{order_id}/download-delivered-file/legacy")
async def download_legacy_delivered_file(
    request: Request,
    order_id: int,
    current_user: User = Depends(require_login),
    container = Depends(get_service_container)
):
    """Download legacy delivered file"""
    order = container.order_repository.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    if not order.delivery_file:
        raise HTTPException(status_code=404, detail="No file delivered")

    file_path = container.file_storage.get_file_path(order.delivery_file)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=str(file_path),
        filename=order.delivery_file,
        media_type="application/octet-stream"
    )


@router.post("/order/{order_id}/approve-request")
async def approve_request(
    request: Request,
    order_id: int,
    current_user: User = Depends(require_login),
    container = Depends(get_service_container)
):
    """Approve a resolution request"""
    order = container.order_repository.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")




    if order.requested_by_admin == "true":

        if order.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Forbidden")
    else:

        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Forbidden")

    try:
        container.order_use_case.approve_resolution_request(order_id, current_user.id)
        return RedirectResponse(f"/order/{order_id}", status_code=HTTP_302_FOUND)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/order/{order_id}/reject-request")
async def reject_request(
    request: Request,
    order_id: int,
    rejection_message: str = Form(""),
    current_user: User = Depends(require_login),
    container = Depends(get_service_container)
):
    """Reject a resolution request"""
    order = container.order_repository.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")




    if order.requested_by_admin == "true":

        if order.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Forbidden")
    else:

        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Forbidden")

    try:
        container.order_use_case.reject_resolution_request(order_id, current_user.id, rejection_message)
        return RedirectResponse(f"/order/{order_id}", status_code=HTTP_302_FOUND)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

