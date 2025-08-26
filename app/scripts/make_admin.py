# scripts/make_admin.py
from app.db import SessionLocal
from app.models import User
from app.utils import hash_password

with SessionLocal() as db:
    u = db.query(User).filter_by(username="admin").first()
    if not u:
        u = User(username="admin", hashed_password=hash_password("changeme"), lvl_user=100, is_superuser=True)
        db.add(u); db.commit()
    else:
        u.is_superuser = True; u.lvl_user = max(u.lvl_user or 0, 100); db.commit()
print("Admin ready")
