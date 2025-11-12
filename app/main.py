from fastapi import FastAPI, Request, Form, HTTPException, Depends, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware
from pydantic import EmailStr, ValidationError, TypeAdapter
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload

from pathlib import Path
from sqlalchemy import update, text
from sqlalchemy import func
from app.db.database import Base, engine, SessionLocal, get_db
from app.domain.Package import Package
from app.domain.User import User
from app.domain.Order import Order
from app.domain.Tag import Tag
from app.domain.Delivery import Delivery
from app.domain.OrderEvent import OrderEvent
from fastapi.staticfiles import StaticFiles

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.add_middleware(SessionMiddleware, secret_key="change-me")

UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

from starlette.responses import RedirectResponse
from starlette.status import HTTP_302_FOUND
from sqlalchemy.orm import Session


# Startup: create tables, admin user, and default packages
@app.on_event("startup")
def startup_event():
    # Ensure all models are imported and registered
    from app.domain.User import User
    from app.domain.Order import Order
    from app.domain.Package import Package
    from app.domain.Tag import Tag
    from app.domain.Delivery import Delivery
    from app.domain.OrderEvent import OrderEvent
    
    db = SessionLocal()
    
    # Do not drop tables on startup; only ensure they exist
    Base.metadata.create_all(bind=engine)

    # Add new columns for dispute system if they don't exist
    try:
        from sqlalchemy import text
        # Check if request_type column exists
        result = db.execute(text("SHOW COLUMNS FROM orders LIKE 'request_type'"))
        if not result.fetchone():
            print("Adding dispute system columns to orders table...")
            db.execute(text("""
                ALTER TABLE orders 
                ADD COLUMN request_type VARCHAR(50) NULL,
                ADD COLUMN request_message TEXT NULL,
                ADD COLUMN cancellation_reason VARCHAR(100) NULL,
                ADD COLUMN cancellation_message TEXT NULL,
                ADD COLUMN extension_days INT NULL,
                ADD COLUMN extension_reason TEXT NULL,
                ADD COLUMN requested_by_admin VARCHAR(10) NULL
            """))
            db.commit()
            print("✅ Dispute system columns added successfully!")
    except Exception as e:
        print(f"⚠️ Migration warning: {e}")
        db.rollback()

    try:
        # Skip schema migrations here to avoid startup delays/hangs
        admin = db.query(User).filter(User.username == "Kohina").first()
        if not admin:
            admin = User(username="Kohina", email="anabelabocvarova@yahoo.com", is_admin=True)
            admin.set_password("Luna123!")
            db.add(admin)
            db.commit()
            print("✅ Admin created: Kohina / Luna123!")
        # Create default packages if none exist
        if db.query(Package).count() == 0:
            default_packages = [
                {"name": "Basic", "price": 10.0, "delivery_days": 1, "tag_count": 2,
                 "description": "Simple tag, 1 revision"},
                {"name": "Standard", "price": 20.0, "delivery_days": 2, "tag_count": 4,
                 "description": "More features, 2 revisions"},
                {"name": "Premium", "price": 40.0, "delivery_days": 3, "tag_count": 6,
                 "description": "Full customization, unlimited revisions"},
                # se inicijaliziraat kako statichni vo bazata samo koga nema za posle da mozhe update
            ]
            for pkg in default_packages:
                db.add(Package(**pkg))
            db.commit()
    finally:
        db.close()


# funcs for login and db


def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    user = db.query(User).filter(User.id == user_id).first()
    return user


def login_user(request: Request, user: User):
    request.session.update({
        "user_id": user.id,
        "username": user.username,
        "is_admin": user.is_admin,
        "email": user.email,
    })
    # Store avatar URL for quick header rendering
    try:
        if getattr(user, "avatar", None):
            request.session["avatar_url"] = str(request.url_for("uploads", path=user.avatar))
        else:
            request.session.pop("avatar_url", None)
    except Exception:
        pass


def require_login(request: Request, current_user=Depends(get_current_user)):
    if not current_user:
        next_url = str(request.url.path)
        # redirect to login
        raise HTTPException(
            status_code=HTTP_302_FOUND,
            detail=f"/login?next={next_url}"
        )
    return current_user


def is_admin(request: Request) -> bool:
    return request.session.get("is_admin", False)


def update_late_orders(db):
    # Use DB clock to avoid client-server clock drift
    db.execute(
        update(Order)
        .where(Order.status.in_(["Active", "Revision"]))
        .where(Order.due_date < func.now())
        .values(status="Late")
    )
    db.commit()


def auto_complete_delivered_orders(db):
    """Auto-complete delivered orders after 72 hours if user hasn't marked them as complete"""
    
    # Get all delivered orders
    delivered_orders = db.query(Order).filter(Order.status == "Delivered").all()
    
    cutoff_time = datetime.utcnow() - timedelta(hours=72)
    
    for order in delivered_orders:
        # Get the latest delivery for this order
        latest_delivery = (
            db.query(Delivery)
            .filter(Delivery.order_id == order.id)
            .order_by(Delivery.delivered_at.desc())
            .first()
        )
        
        # If order was delivered more than 72 hours ago, auto-complete it
        if latest_delivery and latest_delivery.delivered_at <= cutoff_time:
            order.status = "Completed"
            order.completed_date = datetime.utcnow()
    
    db.commit()


def get_orders_with_relationships(db, user_id=None, status=None, admin_view=False):
    """Helper function to get orders with all relationships loaded"""
    query = db.query(Order).options(
        joinedload(Order.tags), 
        joinedload(Order.package), 
        joinedload(Order.user)
    )
    
    if not admin_view and user_id:
        query = query.filter(Order.user_id == user_id)
    
    if status:
        query = query.filter(Order.status == status)
    
    return query.all()


def calculate_monthly_revenue(db, user_id=None, status="Completed"):
    """Helper function to calculate monthly revenue for orders"""
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    query = db.query(Order).options(joinedload(Order.package)).filter(
        Order.status == status,
        Order.completed_date >= month_start,
    )
    
    if user_id:
        query = query.filter(Order.user_id == user_id)
    
    orders = query.all()
    return sum(float(o.package.price) if o.package and o.package.price is not None else 0.0 for o in orders)


def save_uploaded_file(file: UploadFile, prefix: str = "", user_id: int = None) -> str:
    """Helper function to save uploaded files with consistent naming"""
    upload_dir = UPLOAD_DIR
    upload_dir.mkdir(exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    safe_name = file.filename.replace(" ", "_")
    
    if user_id:
        filename = f"{prefix}_user{user_id}_{timestamp}_{safe_name}"
    else:
        filename = f"{prefix}_{timestamp}_{safe_name}"
    
    file_path = upload_dir / filename
    return filename


def calculate_chart_data(db, range_q="monthly"):
    """Helper function to calculate chart data for analytics"""
    from datetime import date, timedelta
    
    labels = []
    revenue_series = []
    completed_series = []
    cancelled_series = []
    cancelled_revenue_series = []
    
    if range_q == "yearly":
        base = date.today().replace(day=1)
        months = []
        for i in range(11, -1, -1):
            y = base.year if base.month - i > 0 else base.year - 1
            m = ((base.month - i - 1) % 12) + 1
            months.append((y, m))
        for y, m in months:
            start = datetime(year=y, month=m, day=1)
            end = datetime(year=y+1, month=1, day=1) if m == 12 else datetime(year=y, month=m+1, day=1)
            completed_m = db.query(Order).options(joinedload(Order.package)).\
                filter(Order.status == "Completed", Order.completed_date >= start, Order.completed_date < end).all()
            cancelled_m = db.query(Order).options(joinedload(Order.package)).\
                filter(Order.status == "Cancelled", Order.cancelled_date >= start, Order.cancelled_date < end).all()
            revenue_m = sum(float(o.package.price) if o.package and o.package.price is not None else 0.0 for o in completed_m)
            cancelled_revenue_m = sum(float(o.package.price) if o.package and o.package.price is not None else 0.0 for o in cancelled_m)
            labels.append(start.strftime('%b %Y'))
            revenue_series.append(round(revenue_m, 2))
            completed_series.append(len(completed_m))
            cancelled_series.append(len(cancelled_m))
            cancelled_revenue_series.append(round(cancelled_revenue_m, 2))
    else:
        start = date.today() - timedelta(days=29)
        for i in range(30):
            d = start + timedelta(days=i)
            d0 = datetime(d.year, d.month, d.day)
            d1 = d0 + timedelta(days=1)
            completed_d = db.query(Order).options(joinedload(Order.package)).\
                filter(Order.status == "Completed", Order.completed_date >= d0, Order.completed_date < d1).all()
            cancelled_d = db.query(Order).options(joinedload(Order.package)).\
                filter(Order.status == "Cancelled", Order.cancelled_date >= d0, Order.cancelled_date < d1).all()
            revenue_d = sum(float(o.package.price) if o.package and o.package.price is not None else 0.0 for o in completed_d)
            cancelled_revenue_d = sum(float(o.package.price) if o.package and o.package.price is not None else 0.0 for o in cancelled_d)
            labels.append(d.strftime('%d %b'))
            revenue_series.append(round(revenue_d, 2))
            completed_series.append(len(completed_d))
            cancelled_series.append(len(cancelled_d))
            cancelled_revenue_series.append(round(cancelled_revenue_d, 2))
    
    return labels, revenue_series, completed_series, cancelled_series, cancelled_revenue_series


# -------------------- AUTH --------------------

@app.get("/")
async def root(request: Request):
    # Show public reviews from all users
    db = SessionLocal()
    try:
        public_reviews = (
            db.query(Order)
            .options(joinedload(Order.package), joinedload(Order.user))
            .filter(Order.review.isnot(None))
            .order_by(Order.id.desc())
            .limit(12)
            .all()
        )
    finally:
        db.close()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "is_logged_in": bool(request.session.get("user_id")),
            "username": request.session.get("username"),
            "is_admin": request.session.get("is_admin"),
            "public_reviews": public_reviews,
        }
    )


@app.get("/login")
async def login(request: Request):
    # Save "next" path (e.g., /myorders)
    next_url = request.query_params.get("next", "/")
    request.session["next_url"] = next_url
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/users/login")
async def users_login(
        request: Request,
        username: str = Form(...),
        password: str = Form(...),
        db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.check_password(password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid username or password"})

    login_user(request, user)  # ✅ Clean helper

    next_url = request.session.pop("next_url", "/")
    return RedirectResponse(url=next_url, status_code=HTTP_302_FOUND)


@app.get("/profile")
async def view_profile(request: Request, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user:
        return RedirectResponse("/login?next=/profile", status_code=HTTP_302_FOUND)

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


@app.post("/profile")
async def update_profile(
        request: Request,
        username: str = Form(...),
        email: str = Form(...),
        new_password: str = Form(""),
        avatar: UploadFile = File(None),
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse("/login?next=/profile", status_code=HTTP_302_FOUND)

    # Validate email
    try:
        TypeAdapter(EmailStr).validate_python(email)
    except ValidationError:
        return templates.TemplateResponse(
            "profile.html",
            {"request": request, "user": current_user, "error": "Invalid email format"}
        )

    # Check duplicates
    if db.query(User).filter(User.username == username, User.id != current_user.id).first():
        return templates.TemplateResponse(
            "profile.html",
            {"request": request, "user": current_user, "error": "Username already taken"}
        )

    if db.query(User).filter(User.email == email, User.id != current_user.id).first():
        return templates.TemplateResponse(
            "profile.html",
            {"request": request, "user": current_user, "error": "Email already in use"}
        )

    # Update fields
    current_user.username = username
    current_user.email = email

    if new_password.strip():
        current_user.set_password(new_password.strip())

    # Handle avatar upload
    if avatar and getattr(avatar, "filename", ""):
        filename = save_uploaded_file(avatar, "avatar", current_user.id)
        file_path = UPLOAD_DIR / filename
        content = await avatar.read()
        with open(file_path, "wb") as f:
            f.write(content)
        current_user.avatar = filename

    db.commit()

    # Refresh session data
    request.session["username"] = current_user.username

    avatar_url = None
    if getattr(current_user, "avatar", None):
        avatar_url = request.url_for("uploads", path=current_user.avatar)

    return templates.TemplateResponse(
        "profile.html",
        {"request": request, "user": current_user, "success": "Profile updated successfully!", "avatar_url": avatar_url}
    )


@app.get("/signup")
async def signup_form(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@app.post("/signup")
async def signup(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    try:
        try:
            TypeAdapter(EmailStr).validate_python(email)
        except ValidationError:
            return templates.TemplateResponse("signup.html", {"request": request, "error": "Invalid email format"})

        if db.query(User).filter(User.username == username).first():
            return templates.TemplateResponse("signup.html", {"request": request, "error": "Username already in use"})
        if db.query(User).filter(User.email == email).first():
            return templates.TemplateResponse("signup.html", {"request": request, "error": "Email already in use"})

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


# -------------------- ORDERS --------------------

@app.get("/order/new")
async def new_order(request: Request):
    db = SessionLocal()
    try:
        packages = db.query(Package).all()
    finally:
        db.close()
    return templates.TemplateResponse("choosepackage.html", {"request": request, "packages": packages})


@app.post("/order/new")
async def select_package(request: Request, package_id: int = Form(...)):
    db = SessionLocal()
    try:
        package = db.query(Package).filter(Package.id == package_id).first()
        if not package:
            return RedirectResponse(url="/order/new", status_code=HTTP_302_FOUND)
    finally:
        db.close()
    return templates.TemplateResponse("order_form.html", {"request": request, "package": package})


@app.post("/order/submit")
async def submit_order(request: Request, package_id: int = Form(...), details: str = Form(None)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=HTTP_302_FOUND)

    form = await request.form()
    tags = [t.strip() for t in form.getlist("tags") if t.strip()]
    moods = [m.strip() for m in form.getlist("moods")]

    db = SessionLocal()
    try:
        package = db.query(Package).filter(Package.id == package_id).first()
        if not package:
            return RedirectResponse(url="/order/new", status_code=HTTP_302_FOUND)

        due_date = datetime.utcnow() + timedelta(days=package.delivery_days)
        order = Order(user_id=user_id, package_id=package.id, details=details, due_date=due_date, status="Active")
        db.add(order)
        db.commit()
        db.refresh(order)

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
        # ✅ Update late orders in DB first
        update_late_orders(db)
        # Auto-complete delivered orders after 72 hours
        auto_complete_delivered_orders(db)

        # Now fetch orders safely
        orders = get_orders_with_relationships(db, user_id=user_id)
        
        # Calculate spent this month
        spent_eur = calculate_monthly_revenue(db, user_id=user_id, status="Completed")
        now = datetime.utcnow()

        return templates.TemplateResponse("myorders.html", {"request": request, "orders": orders, "spent_month": round(spent_eur, 2), "month_name": now.strftime('%B')})
    finally:
        db.close()


@app.get("/myorders-admin")
async def my_orders_admin(request: Request):
    if not request.session.get("is_admin"):
        return RedirectResponse(url="/login", status_code=HTTP_302_FOUND)

    db = SessionLocal()
    try:
        update_late_orders(db)  # ✅ Update DB first
        # Auto-complete delivered orders after 72 hours
        auto_complete_delivered_orders(db)

        orders = get_orders_with_relationships(db, admin_view=True)
        
        # Calculate earnings this month
        earned_eur = calculate_monthly_revenue(db, status="Completed")
        now = datetime.utcnow()
        
        # update session value for navbar dropdown
        try:
            request.session["admin_month_earnings"] = round(earned_eur, 2)
        except Exception:
            pass

        return templates.TemplateResponse("myorders-admin.html", {"request": request, "orders": orders, "is_admin": True, "earned_month": round(earned_eur, 2), "month_name": now.strftime('%B')})
    finally:
        db.close()


@app.get("/completed-orders")
async def completed_orders(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=HTTP_302_FOUND)

    db = SessionLocal()
    try:
        # Auto-complete delivered orders after 72 hours
        auto_complete_delivered_orders(db)
        
        if request.session.get("is_admin"):
            # Admin sees all completed orders
            orders = get_orders_with_relationships(db, status="Completed", admin_view=True)
        else:
            # Regular users see only their own completed orders
            orders = get_orders_with_relationships(db, user_id=user_id, status="Completed")
        
        # Sort by due_date descending
        orders.sort(key=lambda x: x.due_date, reverse=True)

        return templates.TemplateResponse(
            "completed_orders.html",
            {
                "request": request,
                "orders": orders,
                "is_admin": request.session.get("is_admin", False)
            }
        )
    finally:
        db.close()


@app.get("/order/{order_id}")
async def view_order(request: Request, order_id: int):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=HTTP_302_FOUND)

    db = SessionLocal()
    try:
        # Update late orders first
        update_late_orders(db)
        # Auto-complete delivered orders after 72 hours
        auto_complete_delivered_orders(db)

        # Fetch the order with relationships
        order = (
            db.query(Order)
            .options(
                joinedload(Order.tags), 
                joinedload(Order.user), 
                joinedload(Order.package), 
                joinedload(Order.deliveries).joinedload(Delivery.user),
                joinedload(Order.events).joinedload(OrderEvent.user)
            )
            .filter(Order.id == order_id)
            .first()
        )

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Restrict non-admins to their own orders
        if not request.session.get("is_admin") and order.user_id != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        # Generate file URL if delivery_file exists
        file_url = None
        if order.delivery_file:
            file_url = request.url_for("uploads", path=order.delivery_file)

        # Combine deliveries and events into a single timeline, sorted chronologically
        timeline_items = []
        
        # Add deliveries
        if order.deliveries:
            for delivery in order.deliveries:
                if delivery.delivered_at:  # Only add deliveries with valid timestamps
                    timeline_items.append({
                        'type': 'delivery',
                        'delivery': delivery,
                        'date': delivery.delivered_at
                    })
        
        # Add events (excluding 'delivered' events since they're represented by deliveries)
        # Exclude revision_requested events if order is currently in dispute with revision request
        # (they're shown in the Dispute Card section instead to avoid duplication)
        if order.events:
            for event in order.events:
                if event.event_type != 'delivered' and event.created_at:  # Only add events with valid timestamps
                    # Skip revision_requested events if order is currently in dispute with revision request
                    # (they're shown in the Dispute Card section)
                    if event.event_type == 'revision_requested' and order.status == 'In dispute' and order.request_type == 'revision':
                        continue
                    timeline_items.append({
                        'type': 'event',
                        'event': event,
                        'date': event.created_at
                    })
        
        # Add legacy delivery if exists
        if order.status == 'Delivered' and order.delivery_file and not order.deliveries:
            legacy_date = order.due_date or datetime.utcnow()
            timeline_items.append({
                'type': 'legacy_delivery',
                'order': order,
                'date': legacy_date
            })
        
        # Sort by date chronologically (oldest first) - this ensures deliveries appear in order
        # and events appear in chronological order relative to deliveries
        # Use timestamp comparison to ensure proper ordering
        def get_sort_key(item):
            date = item['date']
            if date is None:
                return datetime.min
            # Ensure we're comparing datetime objects properly
            if isinstance(date, datetime):
                return date
            return datetime.min
        
        timeline_items.sort(key=get_sort_key, reverse=False)

        return templates.TemplateResponse(
            "order_detail.html",
            {
                "request": request,
                "order": order,
                "file_url": file_url,
                "is_admin": request.session.get("is_admin", False),
                "timeline_items": timeline_items,
            }
        )
    finally:
        db.close()


# -------------------- ORDER STATUS --------------------
@app.post("/order/{order_id}/complete")  # user side
async def mark_order_complete(request: Request, order_id: int):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)

    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id, Order.user_id == user_id).first()
        if not order or order.status != "Delivered":
            raise HTTPException(status_code=400, detail="Cannot complete this order")

        order.status = "Completed"
        order.completed_date = datetime.utcnow()
        
        # Create order event for completion
        event = OrderEvent(
            order_id=order.id,
            event_type="completed",
            user_id=user_id,
            event_message="Order marked as completed",
            created_at=datetime.utcnow()
        )
        db.add(event)
        db.commit()
    finally:
        db.close()

    # Redirect to a review page for this order
    return RedirectResponse(url=f"/order/{order_id}/review", status_code=302)


@app.post("/order/{order_id}/deliver")  # admin side
async def admin_deliver_order(
        request: Request,
        order_id: int,
        response_text: str = Form(...),
        file: UploadFile = File(...)
):
    if not request.session.get("is_admin"):
        raise HTTPException(status_code=403, detail="Forbidden")

    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order or order.status not in ["Active", "Revision"]:
            raise HTTPException(status_code=400, detail="Cannot deliver in this state")

        # Save the uploaded file
        filename = save_uploaded_file(file, "delivery")
        file_path = UPLOAD_DIR / filename

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Get the next delivery number for this order
        delivery_count = db.query(Delivery).filter(Delivery.order_id == order_id).count()
        delivery_number = delivery_count + 1

        # Create a new delivery record
        delivery = Delivery(
            order_id=order_id,
            delivery_number=delivery_number,
            response_text=response_text,
            delivery_file=filename,
            delivered_at=datetime.utcnow(),
            user_id=request.session.get("user_id")  # Admin who delivered
        )
        db.add(delivery)

        # Update order status
        order.status = "Delivered"
        order.response = response_text  # Keep for backward compatibility
        order.delivery_file = filename  # Keep for backward compatibility
        
        # Create order event for delivery
        event = OrderEvent(
            order_id=order.id,
            event_type="delivered",
            user_id=request.session.get("user_id"),
            event_message=response_text,
            created_at=datetime.utcnow()
        )
        db.add(event)
        db.commit()
    finally:
        db.close()

    # Redirect back to admin orders page
    return RedirectResponse(url="/myorders-admin", status_code=HTTP_302_FOUND)


@app.post("/order/{order_id}/request-revision")  # user side
async def user_request_revision(request: Request, order_id: int, revision_text: str = Form(...)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=HTTP_302_FOUND)

    db = SessionLocal()
    try:
        order = db.query(Order).options(joinedload(Order.package)).filter(Order.id == order_id, Order.user_id == user_id).first()
        if not order or order.status != "Delivered":
            raise HTTPException(status_code=400, detail="Cannot request revision in this state")

        # Reset timer: calculate new due_date based on package delivery days
        if order.package and order.package.delivery_days:
            order.due_date = datetime.utcnow() + timedelta(days=order.package.delivery_days)
        
        order.status = "Revision"
        
        # Create order event for revision request
        event = OrderEvent(
            order_id=order.id,
            event_type="revision_requested",
            user_id=user_id,
            event_message=revision_text,
            created_at=datetime.utcnow()
        )
        db.add(event)
        db.commit()
    finally:
        db.close()

    return RedirectResponse("/myorders", status_code=HTTP_302_FOUND)


@app.post("/order/{order_id}/approve-delivery")
async def user_approve_delivery(request: Request, order_id: int):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=HTTP_302_FOUND)

    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id, Order.user_id == user_id).first()
        if not order or order.status != "Delivered":
            raise HTTPException(status_code=400, detail="Cannot approve delivery in this state")
        order.status = "Completed"
        order.completed_date = datetime.utcnow()
        db.commit()
    finally:
        db.close()
    return RedirectResponse(url=f"/order/{order_id}", status_code=HTTP_302_FOUND)


@app.get("/order/{order_id}/download-delivered-file/{delivery_id}")
async def download_delivered_file(request: Request, order_id: int, delivery_id: int):
    user_id = request.session.get("user_id")
    is_admin = request.session.get("is_admin")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Check if the current user is the owner of the order or an admin
        if order.user_id != user_id and not is_admin:
            raise HTTPException(status_code=403, detail="Not authorized to download this file")

        delivery = db.query(Delivery).filter(
            Delivery.id == delivery_id, 
            Delivery.order_id == order_id
        ).first()
        
        if not delivery or not delivery.delivery_file:
            raise HTTPException(status_code=404, detail="Delivery file not found")

        file_path = BASE_DIR / "uploads" / delivery.delivery_file
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Delivered file not found on server")

        return FileResponse(
            path=str(file_path), 
            filename=delivery.delivery_file, 
            media_type="application/octet-stream"
        )
    finally:
        db.close()


@app.get("/order/{order_id}/download-delivered-file/legacy")
async def download_legacy_delivered_file(request: Request, order_id: int):
    """Handle downloads for old deliveries stored directly on the order"""
    user_id = request.session.get("user_id")
    is_admin = request.session.get("is_admin")
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Check if the current user is the owner of the order or an admin
        if order.user_id != user_id and not is_admin:
            raise HTTPException(status_code=403, detail="Not authorized to download this file")

        if not order.delivery_file:
            raise HTTPException(status_code=404, detail="No file delivered for this order")

        file_path = BASE_DIR / "uploads" / order.delivery_file
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Delivered file not found on server")

        return FileResponse(
            path=str(file_path), 
            filename=order.delivery_file, 
            media_type="application/octet-stream"
        )
    finally:
        db.close()


@app.get("/order/{order_id}/review")
async def review_order(request: Request, order_id: int):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=302)

    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id, Order.user_id == user_id).first()
        if not order or order.status != "Completed":
            raise HTTPException(status_code=400, detail="Cannot review this order")

        return templates.TemplateResponse(
            "review_form.html",
            {"request": request, "order": order}
        )
    finally:
        db.close()


@app.post("/order/{order_id}/review")
async def submit_review(request: Request, order_id: int, review_text: str = Form(...), rating: int = Form(...)):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=302)

    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id, Order.user_id == user_id).first()
        if not order or order.status != "Completed":
            raise HTTPException(status_code=400, detail="Cannot review this order")

        order.review = rating
        order.review_text = review_text
        db.commit()
    finally:
        db.close()

    return RedirectResponse(url="/myorders", status_code=302)
# -------------------- REVIEWS --------------------
@app.get("/myreviews")
async def my_reviews(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/login?next=/myreviews", status_code=HTTP_302_FOUND)

    db = SessionLocal()
    try:
        if request.session.get("is_admin"):
            # Admin: show all reviews from all users
            orders = (
                db.query(Order)
                .options(joinedload(Order.package), joinedload(Order.user))
                .filter(Order.review.isnot(None))
                .order_by(Order.id.desc())
                .all()
            )
            template_name = "adminreviews.html"
        else:
            orders = (
                db.query(Order)
                .options(joinedload(Order.package))
                .filter(Order.user_id == user_id, Order.review.isnot(None))
                .order_by(Order.id.desc())
                .all()
            )
            template_name = "myreviews.html"
    finally:
        db.close()

    return templates.TemplateResponse(template_name, {"request": request, "orders": orders})


# -------------------- RESOLUTION CENTER --------------------

@app.get("/order/{order_id}/resolution")
async def resolution_center(request: Request, order_id: int):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=HTTP_302_FOUND)

    db = SessionLocal()
    try:
        order = (
            db.query(Order)
            .options(joinedload(Order.user), joinedload(Order.package))
            .filter(Order.id == order_id)
            .first()
        )

        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Restrict non-admins to their own orders
        if not request.session.get("is_admin") and order.user_id != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        return templates.TemplateResponse(
            "resolution_center.html",
            {
                "request": request,
                "order": order,
                "is_admin": request.session.get("is_admin", False),
            }
        )
    finally:
        db.close()


@app.post("/order/{order_id}/resolution/submit")
async def submit_resolution_request(
    request: Request,
    order_id: int,
    request_type: str = Form(...),
    message: str = Form(""),
    cancellation_reason: str = Form(""),
    cancellation_message: str = Form(""),
    extension_days: int = Form(0),
    extension_reason: str = Form("")
):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=HTTP_302_FOUND)

    db = SessionLocal()
    try:
        # For admin users, they can submit requests for any order
        if request.session.get("is_admin"):
            order = db.query(Order).filter(Order.id == order_id).first()
        else:
            order = db.query(Order).filter(Order.id == order_id, Order.user_id == user_id).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Validate revision requests - can only be made when order is not Active, In dispute, or Revision
        if request_type == "revision" and (order.status == "Active" or order.status == "In dispute" or order.status == "Revision"):
            raise HTTPException(status_code=400, detail="Cannot request revision at this time. Revision requests can only be made for delivered orders that are not already in revision or dispute.")

        # Update order with resolution request - set to In dispute for all requests
        order.status = "In dispute"
        order.request_type = request_type
        order.request_message = message
        order.requested_by_admin = str(request.session.get("is_admin", False)).lower()
        
        if request_type == "cancellation":
            order.cancellation_reason = cancellation_reason
            order.cancellation_message = cancellation_message
        elif request_type == "extend_delivery":
            order.extension_days = extension_days
            order.extension_reason = extension_reason

        # Create order event
        event_type_map = {
            "cancellation": "cancellation_requested",
            "revision": "revision_requested",
            "extend_delivery": "extension_requested"
        }
        event = OrderEvent(
            order_id=order.id,
            event_type=event_type_map.get(request_type, "request_submitted"),
            user_id=user_id,
            event_message=message,
            cancellation_reason=cancellation_reason if request_type == "cancellation" else None,
            cancellation_message=cancellation_message if request_type == "cancellation" else None,
            extension_days=extension_days if request_type == "extend_delivery" else None,
            extension_reason=extension_reason if request_type == "extend_delivery" else None,
            created_at=datetime.utcnow()
        )
        db.add(event)
        db.commit()
    finally:
        db.close()

    return RedirectResponse(url=f"/order/{order_id}", status_code=HTTP_302_FOUND)


@app.post("/order/{order_id}/approve-request")
async def approve_request(request: Request, order_id: int):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=HTTP_302_FOUND)

    db = SessionLocal()
    try:
        order = db.query(Order).options(joinedload(Order.package)).filter(Order.id == order_id).first()
        if not order or order.status != "In dispute":
            raise HTTPException(status_code=400, detail="Cannot approve this request")

        # Check if the current user is the one who should approve
        is_admin = request.session.get("is_admin", False)
        requested_by_admin = order.requested_by_admin == 'true'
        
        # Admin requests need user approval, user requests need admin approval
        if (requested_by_admin and is_admin) or (not requested_by_admin and not is_admin):
            raise HTTPException(status_code=400, detail="You cannot approve your own request")

        # Store request info before clearing for event
        request_type = order.request_type
        request_message = order.request_message
        
        # Process the approved request
        if order.request_type == "revision":
            # Reset timer: calculate new due_date based on package delivery days
            if order.package and order.package.delivery_days:
                order.due_date = datetime.utcnow() + timedelta(days=order.package.delivery_days)
            order.status = "Revision"
            # Keep request_message for revision requests so it can be displayed
        elif order.request_type == "cancellation":
            order.status = "Cancelled"
            order.cancelled_date = datetime.utcnow()
        elif order.request_type == "extend_delivery":
            # Extend the due date
            if order.extension_days and order.extension_days > 0:
                order.due_date = order.due_date + timedelta(days=order.extension_days)
            order.status = "Active"

        # Create order event for approved request
        event = OrderEvent(
            order_id=order.id,
            event_type="request_approved",
            user_id=user_id,
            event_message=request_message,
            cancellation_reason=order.cancellation_reason if request_type == "cancellation" else None,
            cancellation_message=order.cancellation_message if request_type == "cancellation" else None,
            extension_days=order.extension_days if request_type == "extend_delivery" else None,
            extension_reason=order.extension_reason if request_type == "extend_delivery" else None,
            created_at=datetime.utcnow()
        )
        db.add(event)

        # Clear dispute fields (except request_message for revisions)
        if order.request_type != "revision":
            order.request_message = None
        order.request_type = None
        order.cancellation_reason = None
        order.cancellation_message = None
        order.extension_days = None
        order.extension_reason = None
        order.requested_by_admin = None

        db.commit()
    finally:
        db.close()

    return RedirectResponse(url=f"/order/{order_id}", status_code=HTTP_302_FOUND)


@app.post("/order/{order_id}/reject-request")
async def reject_request(request: Request, order_id: int):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=HTTP_302_FOUND)

    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order or order.status != "In dispute":
            raise HTTPException(status_code=400, detail="Cannot reject this request")

        # Check if the current user is the one who should approve
        is_admin = request.session.get("is_admin", False)
        requested_by_admin = order.requested_by_admin == 'true'
        
        # Admin requests need user approval, user requests need admin approval
        if (requested_by_admin and is_admin) or (not requested_by_admin and not is_admin):
            raise HTTPException(status_code=400, detail="You cannot reject your own request")

        # Store request info before clearing for event
        request_type = order.request_type
        request_message = order.request_message

        # Revert to appropriate status based on request type
        if request_type == "cancellation":
            # Cancellation requests rejected → go back to Active
            order.status = "Active"
        elif request_type == "revision":
            # Revision requests rejected → go back to Delivered (revision requests come from delivered orders)
            order.status = "Delivered"
        elif request_type == "extend_delivery":
            # Extension requests rejected → go back to Active (assuming it was active/late/revision before)
            order.status = "Active"
        else:
            # Fallback: default to Active if request_type is unknown
            order.status = "Active"

        # Create order event for rejected request
        event = OrderEvent(
            order_id=order.id,
            event_type="request_rejected",
            user_id=user_id,
            event_message=request_message,
            cancellation_reason=order.cancellation_reason if request_type == "cancellation" else None,
            cancellation_message=order.cancellation_message if request_type == "cancellation" else None,
            extension_days=order.extension_days if request_type == "extend_delivery" else None,
            extension_reason=order.extension_reason if request_type == "extend_delivery" else None,
            created_at=datetime.utcnow()
        )
        db.add(event)

        # Clear dispute fields
        order.request_type = None
        order.request_message = None
        order.cancellation_reason = None
        order.cancellation_message = None
        order.extension_days = None
        order.extension_reason = None
        order.requested_by_admin = None

        db.commit()
    finally:
        db.close()

    return RedirectResponse(url=f"/order/{order_id}", status_code=HTTP_302_FOUND)


# -------------------- PACKAGE MANAGEMENT --------------------

@app.get("/packages")
async def list_packages(request: Request):
    if not request.session.get("is_admin"):
        return RedirectResponse("/login", status_code=HTTP_302_FOUND)
    db = SessionLocal()
    try:
        packages = db.query(Package).all()
    finally:
        db.close()
    return templates.TemplateResponse("packages.html", {"request": request, "packages": packages})


@app.get("/package/{package_id}/edit")
async def edit_package_form(request: Request, package_id: int):
    if not request.session.get("is_admin"):
        return RedirectResponse("/login", status_code=HTTP_302_FOUND)
    db = SessionLocal()
    try:
        package = db.query(Package).filter(Package.id == package_id).first()
        if not package:
            raise HTTPException(status_code=404, detail="Package not found")
    finally:
        db.close()
    return templates.TemplateResponse("edit_package.html", {"request": request, "package": package})


@app.post("/package/{package_id}/edit")
async def edit_package_submit(request: Request, package_id: int, name: str = Form(...), price: float = Form(...),
                              delivery_days: int = Form(...), tag_count: int = Form(...),
                              description: str = Form(None)):
    if not request.session.get("is_admin"):
        raise HTTPException(status_code=403, detail="Forbidden")

    db = SessionLocal()
    try:
        package = db.query(Package).filter(Package.id == package_id).first()
        if not package:
            raise HTTPException(status_code=404, detail="Package not found")
        package.name = name
        package.price = price
        package.delivery_days = delivery_days
        package.tag_count = tag_count
        package.description = description
        db.commit()
    finally:
        db.close()
    return RedirectResponse("/packages", status_code=HTTP_302_FOUND)


# -------------------- ANALYTICS (Admin) --------------------
@app.get("/analytics")
async def analytics_overview(request: Request):
    if not request.session.get("is_admin"):
        return RedirectResponse("/login?next=/analytics", status_code=HTTP_302_FOUND)

    db = SessionLocal()
    try:
        total_orders = db.query(func.count(Order.id)).scalar() or 0
        completed_orders = db.query(func.count(Order.id)).filter(Order.status == "Completed").scalar() or 0
        delivered_orders = db.query(func.count(Order.id)).filter(Order.status == "Delivered").scalar() or 0
        active_orders = db.query(func.count(Order.id)).filter(Order.status == "Active").scalar() or 0
        late_orders = db.query(func.count(Order.id)).filter(Order.status == "Late").scalar() or 0
        revision_orders = db.query(func.count(Order.id)).filter(Order.status == "Revision").scalar() or 0
        dispute_orders = db.query(func.count(Order.id)).filter(Order.status == "In dispute").scalar() or 0
        cancelled_orders = db.query(func.count(Order.id)).filter(Order.status == "Cancelled").scalar() or 0

        avg_rating = db.query(func.avg(Order.review)).filter(Order.review.isnot(None)).scalar()
        avg_rating = float(avg_rating) if avg_rating is not None else 0.0

        # Calculate revenue for different order statuses
        revenue = calculate_monthly_revenue(db, status="Completed")
        cancelled_revenue = calculate_monthly_revenue(db, status="Cancelled")
        
        # Calculate expected earnings from active and revision orders
        active_orders_list = db.query(Order).options(joinedload(Order.package)).filter(Order.status == "Active").all()
        revision_orders_list = db.query(Order).options(joinedload(Order.package)).filter(Order.status == "Revision").all()
        expected_earnings = sum(float(o.package.price) if o.package and o.package.price is not None else 0.0 for o in active_orders_list + revision_orders_list)

        completion_rate = (completed_orders / total_orders * 100.0) if total_orders else 0.0
        cancellation_rate = (cancelled_orders / total_orders * 100.0) if total_orders else 0.0

        recent_reviews = (
            db.query(Order)
            .options(joinedload(Order.user), joinedload(Order.package))
            .filter(Order.review.isnot(None))
            .order_by(Order.id.desc())
            .limit(12)
            .all()
        )
        # Chart data aggregation
        range_q = request.query_params.get("range", "monthly")
        labels, revenue_series, completed_series, cancelled_series, cancelled_revenue_series = calculate_chart_data(db, range_q)
    finally:
        db.close()

    return templates.TemplateResponse(
        "analytics.html",
        {
            "request": request,
            "kpis": {
                "total": total_orders,
                "completed": completed_orders,
                "delivered": delivered_orders,
                "active": active_orders,
                "late": late_orders,
                "revision": revision_orders,
                "dispute": dispute_orders,
                "cancelled": cancelled_orders,
                "avg_rating": round(avg_rating, 2),
                "revenue": round(revenue, 2),
                "expected_earnings": round(expected_earnings, 2),
                "completion_rate": round(completion_rate, 1),
                "cancellation_rate": round(cancellation_rate, 1),
            },
            "recent_reviews": recent_reviews,
            "chart_labels": labels,
            "chart_revenue": revenue_series,
            "chart_completed": completed_series,
            "chart_cancelled": cancelled_series,
            "chart_cancelled_revenue": cancelled_revenue_series,
        }
    )
