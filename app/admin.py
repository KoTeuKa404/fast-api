from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import User
from app.permissions import require_superuser

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/users", dependencies=[Depends(require_superuser)])
def list_users(db: Session = Depends(get_db)):
    return db.execute(select(User)).scalars().all()

@router.post("/users/{user_id}/set-level/{level}", dependencies=[Depends(require_superuser)])
def set_level(user_id: int, level: int, db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(404, "User not found")
    u.lvl_user = int(level)
    db.commit()
    db.refresh(u)
    return {"ok": True, "user_id": u.id, "lvl_user": u.lvl_user}

@router.post("/users/{user_id}/toggle-admin", dependencies=[Depends(require_superuser)])
def toggle_admin(user_id: int, db: Session = Depends(get_db)):
    u = db.get(User, user_id)
    if not u:
        raise HTTPException(404, "User not found")
    u.is_superuser = not bool(u.is_superuser)
    db.commit()
    db.refresh(u)
    return {"ok": True, "user_id": u.id, "is_superuser": u.is_superuser}
