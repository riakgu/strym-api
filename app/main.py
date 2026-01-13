from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import get_settings
from app.routers import health, ingestion, query, stats

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up...")
    yield
    # Shutdown
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

    return app


app = create_app()