from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.status import HTTP_302_FOUND
from fastapi import HTTPException

from pydantic import EmailStr, ValidationError, TypeAdapter
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload

from pathlib import Path

from app.db.database import Base, engine, SessionLocal
from app.domain.User import User
from app.domain.Order import Order
from app.domain.Tag import Tag

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
# Session middleware for simple auth state
app.add_middleware(SessionMiddleware, secret_key="change-me")

# Define once, near the top of main.py
PACKAGES = [
    {
        "id": 1,
        "name": "Basic",
        "price": 10.0,
        "delivery_days": 1,
        "tag_count": 2,
        "description": "Simple tag, 1 revision",
        "features": ["Simple tag", "1 revision"]
    },
    {
        "id": 2,
        "name": "Standard",
        "price": 20.0,
        "delivery_days": 2,
        "tag_count": 4,
        "description": "More features, 2 revisions",
        "features": ["More tags", "2 revisions"]
    },
    {
        "id": 3,
        "name": "Premium",
        "price": 40.0,
        "delivery_days": 3,
        "tag_count": 6,
        "description": "Full customization, unlimited revisions",
        "features": ["Custom tags", "Unlimited revisions"]
    },
]


# startup database

@app.on_event("startup")
def create_admin_user():
    db = SessionLocal()

    Base.metadata.create_all(bind=engine)
    try:
        admin = db.query(User).filter(User.username == "Kohina").first()
        if not admin:
            admin = User(username="Kohina", email="anabelabocvarova@yahoo.com", is_admin=True)
            admin.set_password("Luna123!")  # ✅ Proper way to set password
            db.add(admin)
            db.commit()
            print("✅ Admin user created: username='Kohina', password='Luna123!'")
        else:
            print("ℹ️ Admin user already exists.")
    finally:
        db.close()


def is_admin(request: Request) -> bool:
    return request.session.get("is_admin", False)


# root
@app.get("/")
async def root(request: Request):
    user_id = request.session.get("user_id")
    username = request.session.get("username")

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "is_logged_in": bool(user_id),
            "username": username,
        },
    )


# login
@app.get("/login")
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/users/login")
async def users_login(request: Request, username: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None or not user.check_password(password):
            return templates.TemplateResponse(
                "login.html",
                {"request": request, "error": "Invalid username or password"}
            )

        # Store login info + admin flag
        request.session["user_id"] = user.id
        request.session["username"] = user.username
        request.session["is_admin"] = user.is_admin

        return RedirectResponse(url="/", status_code=HTTP_302_FOUND)

    finally:
        db.close()


# signup
@app.get("/signup")
async def signup_form(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@app.post("/signup")
async def signup(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    try:
        # Validate email format
        try:
            TypeAdapter(EmailStr).validate_python(email)
        except ValidationError:
            return templates.TemplateResponse(
                "signup.html",
                {"request": request, "error": "Invalid email format"}
            )

        # Check for unique username/email
        if db.query(User).filter(User.username == username).first() is not None:
            return templates.TemplateResponse(
                "signup.html",
                {"request": request, "error": "Username already in use"}
            )
        if db.query(User).filter(User.email == email).first() is not None:
            return templates.TemplateResponse(
                "signup.html",
                {"request": request, "error": "Email already in use"}
            )

        # Create user and hash password with Argon2
        user = User(username=username, email=email, is_admin=False)
        user.set_password(password)
        db.add(user)
        db.commit()

        return RedirectResponse(url="/login", status_code=HTTP_302_FOUND)

    finally:
        db.close()


@app.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=HTTP_302_FOUND)


# orders
@app.get("/order/new")
async def new_order(request: Request):
    return templates.TemplateResponse("choosepackage.html", {"request": request, "packages": PACKAGES})


@app.post("/order/new")
async def select_package(request: Request, package_id: int = Form(...)):
    package = next((p for p in PACKAGES if p["id"] == package_id), None)
    if not package:
        return RedirectResponse(url="/order/new", status_code=HTTP_302_FOUND)
    return templates.TemplateResponse("order_form.html", {"request": request, "package": package})




@app.post("/order/submit")
async def submit_order(
        request: Request,
        package_id: int = Form(...),
        details: str = Form(None),
):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=HTTP_302_FOUND)

    form = await request.form()
    tags = form.getlist("tags")
    moods = form.getlist("moods")

    # clean data
    tags = [t.strip() for t in tags if t.strip()]
    moods = [m.strip() for m in moods]

    db = SessionLocal()
    try:
        # Calculate due date based on package delivery_days
        package = next((p for p in PACKAGES if p["id"] == package_id), None)
        due_date = datetime.utcnow() + timedelta(days=package["delivery_days"])

        order = Order(
            user_id=user_id,
            package_id=package_id,
            details=details,
            due_date=due_date  # store in DB, you need to add Column in Order model
        )
        db.add(order)
        db.commit()
        db.refresh(order)

        # Save each tag with its mood
        for tag_value, mood_value in zip(tags, moods):
            db.add(Tag(order_id=order.id, name=tag_value, mood=mood_value))
        db.commit()
    finally:
        db.close()

    return RedirectResponse(url="/myorders", status_code=HTTP_302_FOUND)



@app.get("/myorders")
async def my_orders(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=HTTP_302_FOUND)

    db = SessionLocal()
    try:
        # Load all orders with tags
        orders = (
            db.query(Order)
            .options(joinedload(Order.tags))  # Only load tags
            .filter(Order.user_id == user_id)
            .all()
        )

        # Static packages dictionary for easy lookup
        packages = {
            1: {"name": "Basic", "delivery_days": 1, "tag_count": 2},
            2: {"name": "Standard", "delivery_days": 2, "tag_count": 4},
            3: {"name": "Premium", "delivery_days": 3, "tag_count": 6},
        }

        # Attach package info to each order dynamically
        for order in orders:
            order.package = packages.get(order.package_id, {"name": "Unknown"})
            print(f"Order ID: {order.id}, Package: {order.package['name']}")
            print("Tags:", [(tag.name, tag.mood) for tag in order.tags])
            print("------")

    finally:
        db.close()

    return templates.TemplateResponse("myorders.html", {
        "request": request,
        "orders": orders
    })


# admin side

@app.get("/myorders-admin")
async def my_orders_admin(request: Request):
    user_id = request.session.get("user_id")
    if not user_id or not request.session.get("is_admin"):
        return RedirectResponse(url="/login", status_code=HTTP_302_FOUND)

    db = SessionLocal()
    try:
        orders = db.query(Order).options(joinedload(Order.tags), joinedload(Order.user)).all()
        total_orders = len(orders)
    finally:
        db.close()

    return templates.TemplateResponse("myorders-admin.html", {
        "request": request,
        "orders": orders,
        "total_orders": total_orders,
        "is_admin": True,
    })



@app.get("/order/{order_id}")
async def view_order(request: Request, order_id: int):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=HTTP_302_FOUND)

    db = SessionLocal()
    try:
        order = (
            db.query(Order)
            .options(joinedload(Order.tags), joinedload(Order.user))
            .filter(Order.id == order_id)
            .first()
        )

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Non-admins can only view their own orders
        if not request.session.get("is_admin") and order.user_id != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        packages = {p["id"]: p for p in PACKAGES}
        order.package = packages.get(order.package_id, {"name": "Unknown"})

    finally:
        db.close()

    return templates.TemplateResponse("order_detail.html", {
        "request": request,
        "order": order
    })
