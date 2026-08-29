import logging
import sys
import os
from typing import Any
from src.core.interfaces.ilogger import ILogger
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
from src.core.exceptions.logger_exceptions import (
    LoggerInitializationError,
    LoggerDispatchError,
    LoggerError,
)


class PythonLogger(ILogger):
    """
    Concrete implementation of ILogger using the Python standard logging library.
    Supports structured logging via 'extra' fields and custom domain exceptions.
    Automatically injects request_id into all logs.
    """

    def __init__(self, name: str, app_state: str, level: int = logging.INFO):
        try:
            self._logger = logging.getLogger(name)
            self._logger.setLevel(level)
            self._state = app_state
            self.stacklevel = 2

            # Prevent adding multiple handlers if the logger is re-initialized
            if not self._logger.handlers:
                console_handler = logging.StreamHandler(sys.stdout)

                log_dir = "logs"
                if not os.path.exists(log_dir):
                    os.makedirs(log_dir)

                # Include request_id in the JSON format
                formatter = jsonlogger.JsonFormatter(
                    "%(asctime)s %(levelname)s %(name)s %(module)s %(lineno)d %(request_id)s %(message)s",
                    json_ensure_ascii=False,
                )
                console_handler.setFormatter(formatter)

                log_filepath = os.path.join(log_dir, "app.jsonl")
                # Max 5MB per file, keeps 5 backup copies
                try:
                    file_handler = RotatingFileHandler(
                        log_filepath, maxBytes=5 * 1024 * 1024, backupCount=5
                    )
                    file_handler.setFormatter(formatter)
                    self._logger.addHandler(file_handler)
                except (OSError, PermissionError) as e:
                    sys.stderr.write(
                        f"Warning: Failed to initialize file handler: {str(e)}. "
                        "Logging will continue to stdout only.\n"
                    )

                self._logger.addHandler(console_handler)

        except Exception as e:
            raise LoggerInitializationError(
                f"Failed to initialize PythonLogger: {str(e)}"
            )

    def _format_metadata(self, kwargs: dict) -> dict:
        """Ensures all metadata is JSON serializable and avoids key conflicts."""
        reserved_keys = {
            "args",
            "asctime",
            "created",
            "exc_info",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "msg",
            "name",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "stack_info",
            "thread",
            "threadName",
        }

        return {
            (f"field_{k}" if k in reserved_keys else k): (
                v if isinstance(v, (str, int, float, bool, type(None))) else str(v)
            )
            for k, v in kwargs.items()
        }

    def debug(self, msg: str, **kwargs: Any) -> None:
        try:
            self._logger.debug(
                msg, extra=self._format_metadata(kwargs), stacklevel=self.stacklevel
            )
        except Exception as e:
            self._handle_failure(e)

    def info(self, msg: str, **kwargs: Any) -> None:
        try:
            self._logger.info(
                msg, extra=self._format_metadata(kwargs), stacklevel=self.stacklevel
            )
        except Exception as e:
            self._handle_failure(e)

    def warning(self, msg: str, **kwargs: Any) -> None:
        try:
            self._logger.warning(
                msg, extra=self._format_metadata(kwargs), stacklevel=self.stacklevel
            )
        except Exception as e:
            self._handle_failure(e)

    def error(
        self,
        msg: str,
        exc_info: Any = None,
        **kwargs: Any,
    ) -> None:
        try:
            info = kwargs.pop("exc", exc_info)
            metadata = self._format_metadata(kwargs)
            # exc_info=exc allows the standard logger to capture the full traceback
            self._logger.error(
                msg, exc_info=info, extra=metadata, stacklevel=self.stacklevel
            )
        except Exception as e:
            self._handle_failure(e)

    def critical(
        self,
        msg: str,
        exc_info: Any = None,
        **kwargs: Any,
    ) -> None:
        try:
            info = kwargs.pop("exc", exc_info)
            metadata = self._format_metadata(kwargs)
            # exc_info=exc allows the standard logger to capture the full traceback
            self._logger.critical(
                msg, exc_info=info, extra=metadata, stacklevel=self.stacklevel
            )
        except Exception as e:
            self._handle_failure(e)

    def _handle_failure(self, e: Exception) -> None:
        """
        Internal error handling logic.
        Crashes in Dev to alert the engineer; stays silent in Prod to save the UX.
        """
        error_msg = f"Logging failure: {str(e)}"

        # 1. Always attempt to write the failure to stderr as a last resort
        sys.stderr.write(f"--- LOGGING SYSTEM CRITICAL --- \n{error_msg}\n")

        # 2. Strategy based on Environment
        if self._state == "production":
            # In Prod, we swallow the error.
            return

        # 3. In Dev/Staging, we raise to stop the execution
        if isinstance(e, OSError):
            raise LoggerDispatchError(f"Dev Alert: Check your disk/permissions: {e}")

        raise LoggerError(f"Dev Alert: Unexpected logging logic error: {e}")
