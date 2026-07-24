from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.exceptions import AegisException
from app.core.logging import error_logger

def register_exception_handlers(app: FastAPI) -> None:
    """
    Registers custom exception interceptors for FastAPI to catch AegisException,
    validation failures, and unhandled database or system errors.
    """
    
    @app.exception_handler(AegisException)
    async def aegis_exception_handler(request: Request, exc: AegisException) -> JSONResponse:
        error_logger.error(
            "application_exception",
            path=request.url.path,
            status_code=exc.status_code,
            message=exc.message,
            details=exc.details
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": exc.__class__.__name__,
                "message": exc.message,
                "details": exc.details
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        details = exc.errors()
        error_logger.warn(
            "validation_exception",
            path=request.url.path,
            message="Input parameters failed validation checks",
            details=details
        )
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": "ValidationException",
                "message": "Input validation failed",
                "details": details
            }
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        error_logger.error(
            "unhandled_system_exception",
            path=request.url.path,
            exception=exc.__class__.__name__,
            message=str(exc)
        )
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "InternalServerError",
                "message": "An unexpected server error occurred",
                "details": None
            }
        )
