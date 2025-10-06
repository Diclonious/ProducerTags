from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from starlette.status import HTTP_302_FOUND
 

# Absolute imports
from app.db.database import Base, engine, SessionLocal
from app.domain.User import User
from app.domain.Order import Order


app = FastAPI()

templates = Jinja2Templates(directory="templates")





@app.on_event("startup")
def on_startup() -> None:
    # Create tables if they do not exist
    Base.metadata.create_all(bind=engine)

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})



@app.get("/order/new")
async def new_order(request: Request):
    return templates.TemplateResponse("order_form.html", {"request": request})


@app.get("/login")
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/signup")
async def signup_form(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})


@app.post("/signup")
async def signup(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing is not None:
            return templates.TemplateResponse("signup.html", {"request": request, "error": "Email already in use"})

        user = User(username=username, email=email, password=password)
        db.add(user)
        db.commit()
        return RedirectResponse(url="/login", status_code=HTTP_302_FOUND)
    finally:
        db.close()


# Backward-compatibility: redirect old paths to new signup endpoints
@app.get("/users/signup")
async def legacy_signup_get() -> RedirectResponse:
    return RedirectResponse(url="/signup", status_code=HTTP_302_FOUND)


@app.post("/users/signup")
async def legacy_signup_post(username: str = Form(...), email: str = Form(...), password: str = Form(...)) -> RedirectResponse:
    # Forward the request to the canonical endpoint
    return RedirectResponse(url=f"/signup?username={username}&email={email}&password={password}", status_code=HTTP_302_FOUND)