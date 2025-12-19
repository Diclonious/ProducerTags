
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from starlette.status import HTTP_302_FOUND
from pathlib import Path

from app.infrastructure.database import get_db
from app.presentation.api.dependencies.auth import get_service_container, require_admin
from app.application.dto.package import PackageUpdate
from app.domain.entities.User import User

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter()


@router.get("/packages")
async def list_packages(
    request: Request,
    current_user: User = Depends(require_admin),
    container = Depends(get_service_container)
):
    
    packages = container.package_use_case.get_all_packages()
    return templates.TemplateResponse(
        "packages.html",
        {"request": request, "packages": packages}
    )


@router.get("/package/{package_id}/edit")
async def edit_package_form(
    request: Request,
    package_id: int,
    current_user: User = Depends(require_admin),
    container = Depends(get_service_container)
):
    package = container.package_use_case.get_package_by_id(package_id)
    if not package:
        raise HTTPException(status_code=404, detail="Package not found")

    return templates.TemplateResponse(
        "edit_package.html",
        {"request": request, "package": package}
    )


@router.post("/package/{package_id}/edit")
async def edit_package_submit(
    request: Request,
    package_id: int,
    name: str = Form(...),
    price: float = Form(...),
    delivery_days: int = Form(...),
    tag_count: int = Form(...),
    description: str = Form(None),
    current_user: User = Depends(require_admin),
    container = Depends(get_service_container)
):
    package_data = PackageUpdate(
        name=name,
        price=price,
        delivery_days=delivery_days,
        tag_count=tag_count,
        description=description
    )
    try:
        container.package_use_case.update_package(package_id, package_data)
        return RedirectResponse("/packages", status_code=HTTP_302_FOUND)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

