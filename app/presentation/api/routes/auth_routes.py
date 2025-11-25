"""Authentication routes"""
from fastapi import APIRouter, Request, Form, Depends, UploadFile, File
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from starlette.status import HTTP_302_FOUND
from pydantic import EmailStr, ValidationError, TypeAdapter
from sqlalchemy.orm import Session
from pathlib import Path

from app.infrastructure.database import get_db
from app.presentation.api.dependencies.auth import get_service_container, get_current_user, require_login
from app.application.dto.user import UserCreate, UserLogin
from app.domain.entities.User import User

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter()


def login_user(request: Request, user: User):
    """Helper to set session data"""
    request.session.update({
        "user_id": user.id,
        "username": user.username,
        "is_admin": user.is_admin,
        "email": user.email,
    })
    try:
        if getattr(user, "avatar", None):
            request.session["avatar_url"] = str(request.url_for("uploads", path=user.avatar))
        else:
            request.session.pop("avatar_url", None)
    except Exception:
        pass


@router.get("/")
async def root(request: Request, db: Session = Depends(get_db)):
    """Homepage with public reviews"""
    from sqlalchemy.orm import joinedload
    from app.domain.entities.Order import Order

    container = get_service_container(db)
    try:


        public_reviews = (
            db.query(Order)
            .options(joinedload(Order.package), joinedload(Order.user))
            .filter(Order.review.isnot(None))
            .order_by(Order.id.desc())
            .limit(12)
            .all()
        )


        all_orders = container.order_repository.get_all()


        completed_orders = [o for o in all_orders if o.status == "Completed"]
        tags_delivered = len(completed_orders)


        reviews = [o.review for o in all_orders if o.review is not None]
        if reviews:
            avg_rating = sum(reviews) / len(reviews)
            avg_rating_formatted = f"{avg_rating:.1f}"
        else:
            avg_rating_formatted = "0.0"


        turnaround = "24h"


        import os
        from pathlib import Path

        BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
        static_audio_dir = BASE_DIR / "static" / "audio"
        audio_file = None
        if static_audio_dir.exists():

            audio_files = list(static_audio_dir.glob("*.wav")) + list(static_audio_dir.glob("*.mp3"))
            if audio_files:

                audio_file = sorted(audio_files, key=lambda x: x.name)[0].name

    finally:
        pass

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "is_logged_in": bool(request.session.get("user_id")),
            "username": request.session.get("username"),
            "is_admin": request.session.get("is_admin"),
            "public_reviews": public_reviews,
            "tags_delivered": tags_delivered,
            "avg_rating": avg_rating_formatted,
            "turnaround": turnaround,
            "audio_file": audio_file,
        }
    )


@router.get("/login")
async def login(request: Request):
    """Login page"""
    next_url = request.query_params.get("next", "/")
    request.session["next_url"] = next_url
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/users/login")
async def users_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle user login"""
    container = get_service_container(db)
    login_data = UserLogin(username=username, password=password)

    user = container.auth_use_case.authenticate_user(login_data)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password"}
        )

    login_user(request, user)
    next_url = request.session.pop("next_url", "/")
    return RedirectResponse(url=next_url, status_code=HTTP_302_FOUND)


@router.get("/signup")
async def signup_form(request: Request):
    """Signup page"""
    return templates.TemplateResponse("signup.html", {"request": request})


@router.post("/signup")
async def signup(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Handle user signup"""
    container = get_service_container(db)

    try:
        TypeAdapter(EmailStr).validate_python(email)
    except ValidationError:
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": "Invalid email format"}
        )

    user_data = UserCreate(username=username, email=email, password=password, is_admin=False)

    try:
        user = container.auth_use_case.create_user(user_data)
        return RedirectResponse(url="/login", status_code=HTTP_302_FOUND)
    except ValueError as e:
        return templates.TemplateResponse(
            "signup.html",
            {"request": request, "error": str(e)}
        )


@router.get("/profile")
async def view_profile(
    request: Request,
    current_user: User = Depends(require_login),
    db: Session = Depends(get_db)
):
    """View user profile"""
    avatar_url = None
    if getattr(current_user, "avatar", None):
        avatar_url = request.url_for("uploads", path=current_user.avatar)
        try:
            request.session["avatar_url"] = str(avatar_url)
        except Exception:
            pass

    return templates.TemplateResponse(
        "profile.html",
        {"request": request, "user": current_user, "avatar_url": avatar_url}
    )


@router.post("/profile")
async def update_profile(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    new_password: str = Form(""),
    avatar: UploadFile = File(None),
    current_user: User = Depends(require_login),
    db: Session = Depends(get_db)
):
    """Update user profile"""
    container = get_service_container(db)


    try:
        TypeAdapter(EmailStr).validate_python(email)
    except ValidationError:
        return templates.TemplateResponse(
            "profile.html",
            {"request": request, "user": current_user, "error": "Invalid email format"}
        )


    existing_user = container.user_repository.get_by_username(username)
    if existing_user and existing_user.id != current_user.id:
        return templates.TemplateResponse(
            "profile.html",
            {"request": request, "user": current_user, "error": "Username already taken"}
        )

    existing_email = container.user_repository.get_by_email(email)
    if existing_email and existing_email.id != current_user.id:
        return templates.TemplateResponse(
            "profile.html",
            {"request": request, "user": current_user, "error": "Email already in use"}
        )


    current_user.username = username
    current_user.email = email

    if new_password.strip():
        current_user.set_password(new_password.strip())


    if avatar and getattr(avatar, "filename", ""):
        filename = container.file_storage.save_uploaded_file(avatar, "avatar", current_user.id)
        file_path = container.file_storage.get_file_path(filename)
        content = await avatar.read()
        with open(file_path, "wb") as f:
            f.write(content)
        current_user.avatar = filename

    container.user_repository.update(current_user)


    request.session["username"] = current_user.username

    avatar_url = None
    if getattr(current_user, "avatar", None):
        avatar_url = request.url_for("uploads", path=current_user.avatar)

    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "user": current_user,
            "success": "Profile updated successfully!",
            "avatar_url": avatar_url
        }
    )


@router.post("/logout")
async def logout(request: Request):
    """Handle user logout"""
    request.session.clear()
    return RedirectResponse(url="/", status_code=HTTP_302_FOUND)

