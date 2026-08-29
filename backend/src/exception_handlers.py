from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from src.core.interfaces.ilogger import ILogger
from src.core.exceptions.logger_exceptions import LoggerError

def register_exception_handlers(app: FastAPI, logger: ILogger) -> None:
    """
    Registers global exception handlers for the FastAPI application.
    """
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception occurred on path {request.url.path}: {str(exc)}", exc=exc)
        return JSONResponse(
            status_code=500,
            content={"message": "An unexpected internal server error occurred."},
        )

    @app.exception_handler(LoggerError)
    async def logger_exception_handler(request: Request, exc: LoggerError):
        logger.error(f"Logger error occurred: {str(exc)}", exc=exc)
        return JSONResponse(
            status_code=500,
            content={"message": "Internal logging error."},
        )
