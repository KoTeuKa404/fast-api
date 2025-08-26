from __future__ import annotations

import logging
import os
import re
import secrets
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi import FastAPI
from app.ws import router as ws_router
from fastapi import FastAPI, Response

# Якщо десь використовується Base/engine – імпорти лишаємо, але нічого не створюємо тут
from app.db import engine, Base  # noqa: F401
from app import models  # noqa: F401
from app import routes
from app import admin as admin_router
from app.admin_ui import setup_admin
from app.ws import router as ws_router
app = FastAPI()

# --------------------------------------------------------------------------------------
# DEBUG / LOGGING | docker compose logs -f web
# --------------------------------------------------------------------------------------
def _truthy(val: str | None) -> bool:
    return str(val or "").lower() in {"1", "true", "yes", "on"}

DEBUG = _truthy(os.getenv("APP_DEBUG"))
SQL_ECHO = _truthy(os.getenv("SQL_ECHO"))

logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
)

# зробимо основні логери читабельнішими у DEBUG
logging.getLogger("uvicorn").setLevel(logging.DEBUG if DEBUG else logging.INFO)
logging.getLogger("uvicorn.error").setLevel(logging.DEBUG if DEBUG else logging.INFO)
logging.getLogger("uvicorn.access").setLevel(logging.DEBUG if DEBUG else logging.INFO)
logging.getLogger("alembic").setLevel(logging.DEBUG if DEBUG else logging.INFO)
logging.getLogger("app").setLevel(logging.DEBUG if DEBUG else logging.INFO)
# SQLAlchemy engine SQL (і так багатослівний на INFO)
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO if DEBUG else logging.WARNING)

app_log = logging.getLogger("app")
req_log = logging.getLogger("app.request")


def _mask_dsn(dsn: str) -> str:
    # маскуємо пароль у DSN для логів
    return re.sub(r"//([^:/?#]+):([^@]+)@", r"//\1:***@", dsn or "", count=1)


# --------------------------------------------------------------------------------------
# FastAPI app
# --------------------------------------------------------------------------------------
TAGS_METADATA = [
    {"name": "Pages", "description": "HTML сторінки"},
    {"name": "Auth", "description": "Реєстрація/логін/паролі"},
    {"name": "User", "description": "Профіль / Me"},
    {"name": "Chat", "description": "Повідомлення / чат"},
    {"name": "Tasks", "description": "Celery задачі"},
    {"name": "Session", "description": "Стан сесії / утиліти"},
    {"name": "Admin", "description": "Адмін-дії"},
]
app = FastAPI(title="Live Chat", debug=DEBUG, openapi_tags=TAGS_METADATA)

@app.get("/healthz", include_in_schema=False)
def healthz():
    return Response(content="ok", media_type="text/plain")

# Static & templates
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Sessions
SESSION_SECRET = os.getenv("SESSION_SECRET", "devsecret_change_me")
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------------------
# HTTP-логування запитів
# --------------------------------------------------------------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    session = request.scope.get("session") or {}
    user = session.get("username") or session.get("user_id") or "-"
    status = "-"  # важливо: ініціалізація

    try:
        response = await call_next(request)
        status = getattr(response, "status_code", "-")
        return response
    except Exception:
        status = 500
        req_log.exception("Unhandled error for %s %s user=%s", request.method, request.url.path, user)
        # перепіднімаємо, щоб FastAPI віддав звичний 500 JSON
        raise
    finally:
        req_log.info("%s %s %s user=%s", request.method, request.url.path, status, user)

# --------------------------------------------------------------------------------------
# НІЯКИХ create_all тут — схемою керує Alembic
# Base.metadata.create_all(bind=engine)
# --------------------------------------------------------------------------------------

# API роутер
app.include_router(routes.router)

# Admin API + Admin UI
app.include_router(admin_router.router)
setup_admin(app)  # веб-адмінка

# Pages
@app.get("/", tags=["Pages"])
def root(request: Request):
    if not request.session.get("logged_in"):
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", tags=["Pages"])
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/account", tags=["Pages"])
def account_page(request: Request):
    if not request.session.get("logged_in"):
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("account.html", {"request": request})

@app.get("/csrf-token", tags=["Session"])
def csrf_token(request: Request):
    token = request.session.get("csrf_token")
    if not token:
        import secrets as _secrets
        token = _secrets.token_urlsafe(32)
        request.session["csrf_token"] = token
    return {"csrf_token": token}

# --------------------------------------------------------------------------------------
# Startup: авто-міграції (без падіння воркера)
# --------------------------------------------------------------------------------------
@app.on_event("startup")
def on_startup() -> None:
    app_log.info(
        "Starting app DEBUG=%s SQL_ECHO=%s DB=%s",
        DEBUG,
        SQL_ECHO,
        _mask_dsn(os.getenv("DATABASE_URL", "<unset>")),
    )
   
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=500,
        content={"detail": "Database error", "code": "db_error"},
    )

@app.exception_handler(Exception)
async def unhandled_error_handler(request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "code": "internal_error"},
    )
app.include_router(ws_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
