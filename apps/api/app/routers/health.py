from fastapi import APIRouter
from sqlalchemy import text

from app.config import settings
from app.db import SessionLocal

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    # Health endpoint de kiem tra service va DB ping co hoat dong (liveness/readiness).
    db_state = "up"
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception:
        db_state = "down"
    return {"status": "ok", "database": db_state, "app_env": settings.app_env}
