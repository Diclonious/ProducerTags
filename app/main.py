from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from starlette.status import HTTP_302_FOUND
from pydantic import EmailStr, ValidationError, TypeAdapter
from starlette.middleware.sessions import SessionMiddleware
 

# Absolute imports
from app.db.database import Base, engine, SessionLocal
from app.domain.User import User
from app.domain.Order import Order
from app.domain.Package import Package



app = FastAPI()

templates = Jinja2Templates(directory="templates")

# Session middleware for simple auth state
app.add_middleware(SessionMiddleware, secret_key="change-me")




#startup database
@app.on_event("startup")
def on_startup() -> None:
    # Create tables if they do not exist
    Base.metadata.create_all(bind=engine)
#root
@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})



#login
@app.get("/login")
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

    
@app.post("/users/login")
async def users_login(request: Request, username: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if user is None or not user.check_password(password):
            return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid username or password"})
        request.session["user_id"] = user.id
        request.session["username"] = user.username
        return RedirectResponse(url="/", status_code=HTTP_302_FOUND)
    finally:
        db.close()

#signup
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
            return templates.TemplateResponse("signup.html", {"request": request, "error": "Invalid email format"})

        # Enforce unique username and email
        if db.query(User).filter(User.username == username).first() is not None:
            return templates.TemplateResponse("signup.html", {"request": request, "error": "Username already in use"})
        if db.query(User).filter(User.email == email).first() is not None:
            return templates.TemplateResponse("signup.html", {"request": request, "error": "Email already in use"})

        user = User(username=username, email=email, password=password)
        db.add(user)
        db.commit()
        return RedirectResponse(url="/login", status_code=HTTP_302_FOUND)
    finally:
        db.close()



@app.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=HTTP_302_FOUND)


#orders
@app.get("/order/new")
async def new_order(request: Request):
    packages = [
        {
            "id": 1,
            "name": "Basic",
            "price": 10.0,
            "delivery_days": 1,
            "tag_count": 1,
            "features": ["Simple tag", "1 revision"]
        },
        {
            "id": 2,
            "name": "Standard",
            "price": 20.0,
            "delivery_days": 2,
            "tag_count": 2,
            "features": ["Enhanced tag", "2 revisions"]
        },
        {
            "id": 3,
            "name": "Premium",
            "price": 35.0,
            "delivery_days": 3,
            "tag_count": 3,
            "features": ["Full custom tag", "Unlimited revisions"]
        },
    ]
    return templates.TemplateResponse("choosepackage.html", {"request": request, "packages": packages})
