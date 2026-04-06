import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import engine
from app.models import Base  # noqa: F401
from app.routers.chat import router as chat_router
from app.routers.health import router as health_router

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    origins = [item.strip() for item in settings.cors_origins.split(",") if item.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # Ghi log origin da nap de debug nhanh khi browser bao loi CORS.
    logger.info("CORS origins loaded: %s", origins)

    # Tao bang tu dong cho phase mock-first de toi uu toc do demo (bootstrap tables).
    Base.metadata.create_all(bind=engine)

    app.include_router(health_router)
    app.include_router(chat_router)
    return app


app = create_app()
