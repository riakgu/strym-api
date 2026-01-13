from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import get_settings

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
    
    return app


app = create_app()