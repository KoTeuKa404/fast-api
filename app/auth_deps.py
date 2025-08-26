# app/auth_deps.py
from fastapi import Depends, Request, Header, HTTPException
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.db import get_db
from app.models import User
from app.utils import SECRET_KEY, ALGORITHM  # у тебе вже є
# Повертає поточного користувача по Bearer або по session cookie
def get_current_user(
    request: Request,
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
) -> User:
    username: str | None = None

    # 1) Bearer
    if authorization and authorization.startswith("Bearer "):
        try:
            payload = jwt.decode(authorization.split(" ")[1], SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
        except JWTError:
            username = None

    # 2) Session
    if not username:
        username = request.session.get("username")

    if not username:
        raise HTTPException(status_code=401, detail="Missing auth")

    user = db.query(User).filter_by(username=username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
