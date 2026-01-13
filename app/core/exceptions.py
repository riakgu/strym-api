from fastapi import Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code


class ValidationError(AppException):
    def __init__(self, message: str):
        super().__init__(message, 400)


class NotFoundError(AppException):
    def __init__(self, resource: str, id: str):
        super().__init__(f"{resource} '{id}' not found", 404)


class RateLimitError(AppException):
    def __init__(self):
        super().__init__("Rate limit exceeded", 429)


class DatabaseError(AppException):
    def __init__(self, message: str):
        super().__init__(f"Database error: {message}", 500)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    from datetime import datetime, timezone

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "type": exc.__class__.__name__,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        },
    )