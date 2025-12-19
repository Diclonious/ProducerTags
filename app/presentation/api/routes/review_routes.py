
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from starlette.status import HTTP_302_FOUND
from sqlalchemy.orm import joinedload
from pathlib import Path

from app.infrastructure.database import get_db
from app.presentation.api.dependencies.auth import get_service_container, require_login
from app.domain.entities.User import User
from app.domain.entities.Order import Order

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter()


@router.get("/myreviews")
async def my_reviews(
    request: Request,
    current_user: User = Depends(require_login),
    container = Depends(get_service_container)
):
    
    if current_user.is_admin:

        orders = (
            container.db.query(Order)
            .options(joinedload(Order.package), joinedload(Order.user))
            .filter(Order.review.isnot(None))
            .order_by(Order.id.desc())
            .all()
        )
        template_name = "adminreviews.html"
    else:

        orders = (
            container.db.query(Order)
            .options(joinedload(Order.package))
            .filter(Order.user_id == current_user.id, Order.review.isnot(None))
            .order_by(Order.id.desc())
            .all()
        )
        template_name = "myreviews.html"

    return templates.TemplateResponse(
        template_name,
        {"request": request, "orders": orders}
    )

