# app/routes.py
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Message, User
from app.schemas import *
from app.manager import ConnectionManager
from app.utils import hash_password, verify_password, create_access_token
from jose import jwt, JWTError
from celery.result import AsyncResult
from app.celery_app import celery, fake_heavy_task


router = APIRouter()
manager = ConnectionManager()
SECRET_KEY = "supersecret_for_demo"
ALGORITHM = "HS256"
# app/routes.py (на початку)
from typing import Optional
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect, Depends, HTTPException, Header, status
from pydantic import BaseModel, constr, ValidationError
# ...інші імпорти лишаємо

router = APIRouter()
manager = ConnectionManager()
SECRET_KEY = "supersecret_for_demo"
ALGORITHM = "HS256"

# ---- CSRF: явний alias під саме "X-CSRF-Token" ----
def verify_csrf_token(
    request: Request,
    x_csrf_token: Optional[str] = Header(None, alias="X-CSRF-Token"),
):
    csrf_token = request.session.get("csrf_token")
    if not csrf_token or not x_csrf_token or csrf_token != x_csrf_token:
        raise HTTPException(status_code=403, detail="CSRF token missing or invalid")

# ---- Моделі для ручного парсингу ----
class RegisterIn(BaseModel):
    username: constr(min_length=3, strip_whitespace=True)
    password: constr(min_length=5)

class LoginIn(BaseModel):
    username: constr(min_length=3, strip_whitespace=True)
    password: constr(min_length=5)

async def parse_payload(request: Request, model: type[BaseModel]) -> BaseModel:
    """
    Пробує JSON; якщо ні — читає form-data. Кидає 400 з людським detail.
    """
    try:
        ct = (request.headers.get("content-type") or "").lower()
        if "application/json" in ct:
            data = await request.json()
        else:
            form = await request.form()
            data = {k: v for k, v in form.items()}
        return model(**data)
    except ValidationError as ve:
        # формат FastAPI 422 -> перетворимо на 400 із списком помилок
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=[{"loc": e["loc"], "msg": e["msg"]} for e in ve.errors()],
        )

def verify_csrf_token(request: Request, x_csrf_token: str = Header(None)):
    csrf_token = request.session.get("csrf_token")
    if not csrf_token or not x_csrf_token or csrf_token != x_csrf_token:
        raise HTTPException(status_code=403, detail="CSRF token missing or invalid")

def get_current_user_from_token(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username: raise HTTPException(status_code=401, detail="Invalid token payload")
        user = db.query(User).filter(User.username == username).first()
        if not user: raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user_session_or_token(request: Request, authorization: str = Header(None), db: Session = Depends(get_db)):
    # 1) Bearer
    if authorization and authorization.startswith("Bearer "):
        try:
            payload = jwt.decode(authorization.split(" ")[1], SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
        except JWTError:
            username = None
    else:
        username = None
    # 2) Session
    if not username:
        username = request.session.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Missing auth (token or session)")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# заміни існуючий /register
@router.post("/register", tags=["Auth"], response_model=UserResponse)
async def register(request: Request, db: Session = Depends(get_db), csrf=Depends(verify_csrf_token)):
    data = await parse_payload(request, RegisterIn)

    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="Користувач з таким ім’ям вже існує")

    user = User(username=data.username, hashed_password=hash_password(data.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    # одразу авторизуємо сесію
    request.session["logged_in"] = True
    request.session["username"] = user.username
    request.session["user_id"] = user.id

    return user

# заміни існуючий /login
@router.post("/login", tags=["Auth"])
async def login(request: Request, db: Session = Depends(get_db), csrf=Depends(verify_csrf_token)):
    data = await parse_payload(request, LoginIn)

    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Невірний логін або пароль")

    access_token = create_access_token(data={"sub": user.username})

    request.session["logged_in"] = True
    request.session["username"] = user.username
    request.session["user_id"] = user.id

    return {"access_token": access_token}


@router.post("/logout", tags=["Auth"])
def logout(request: Request):
    request.session.clear()
    return {"ok": True}

@router.post("/change-password", tags=["User"])
def change_password(data: PasswordChange, user: User = Depends(get_current_user_from_token), db: Session = Depends(get_db), csrf=Depends(verify_csrf_token)):
    if not verify_password(data.old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Старий пароль невірний")
    user.hashed_password = hash_password(data.new_password)
    db.commit()
    return {"message": "Пароль змінено успішно"}

@router.get("/me", tags=["User"])
def me(user: User = Depends(get_current_user_session_or_token)):
    return {"username": user.username, "registered_at": user.registered_at}

@router.get("/messages", tags=["Chat"])
def get_messages(db: Session = Depends(get_db)):
    msgs = db.query(Message).order_by(Message.timestamp.asc()).all()
    return [{"id": m.id, "username": m.username, "text": m.text, "timestamp": m.timestamp.strftime("%Y-%m-%d %H:%M:%S")} for m in msgs]

@router.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    token = websocket.query_params.get("token")
    if not token: await websocket.close(code=4001); return
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username: await websocket.close(code=4001); return
        user = db.query(User).filter(User.username == username).first()
        if not user: await websocket.close(code=4001); return
    except JWTError:
        await websocket.close(code=4001); return

    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            msg = Message(username=user.username, user_id=user.id, text=data["text"])
            db.add(msg); db.commit(); db.refresh(msg)
            await manager.broadcast({
                "id": msg.id, "username": msg.username, "text": msg.text,
                "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Celery demo
@router.post("/tasks/start", response_model=dict, tags=["Tasks"])
def start_fake_task(seconds: int = 10, steps: int = 10, user: User = Depends(get_current_user_session_or_token)):
    t = fake_heavy_task.apply_async(kwargs={"seconds": seconds, "steps": steps})
    return {"task_id": t.id}

@router.get("/tasks/{task_id}/status", response_model=dict, tags=["Tasks"])
def task_status(task_id: str):
    res = AsyncResult(task_id, app=celery)
    payload = {"task_id": task_id, "state": res.state}
    if isinstance(res.info, dict): payload.update(res.info)
    return payload

@router.get("/tasks/{task_id}/result", response_model=dict, tags=["Tasks"])
def task_result(task_id: str):
    res = AsyncResult(task_id, app=celery)
    if not res.ready(): return {"task_id": task_id, "state": res.state, "ready": False}
    if res.failed():     return {"task_id": task_id, "state": res.state, "ready": True, "error": str(res.result)}
    return {"task_id": task_id, "state": res.state, "ready": True, "result": res.result}

@router.get("/session", tags=["Session"])
def session_status(request: Request):
    username = request.session.get("username")
    return {"logged_in": bool(username), "username": username}

@router.post("/tasks/{task_id}/cancel", response_model=dict, tags=["Tasks"])
def cancel_task(task_id: str):
    # terminate=True tries to kill running task; requires worker to allow it
    celery.control.revoke(task_id, terminate=True, signal="SIGTERM")
    return {"task_id": task_id, "state": "REVOKED"}
