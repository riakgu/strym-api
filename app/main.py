from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import get_settings
from app.routers import health, ingestion, query, stats, stream
from app.core.exceptions import AppException, app_exception_handler
from app.db.connection import init_db, close_db
from app.services.stream_service import stream_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    await stream_service.init()
    yield
    # Shutdown
    await stream_service.close()
    await close_db()
    print("Shutting down...")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="Real-time log monitoring system",
        lifespan=lifespan,
    )
    
    app.include_router(health.router)
    app.include_router(ingestion.router)
    app.include_router(query.router)
    app.include_router(stats.router)
    app.include_router(stream.router)

    app.add_exception_handler(AppException, app_exception_handler)

    return app


app = create_app()