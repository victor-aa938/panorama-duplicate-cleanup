"""
Logging utility module for duplicate service cleanup tool.

Implements file and console logging with rotation, timestamp, module name, and context support.
"""

import logging
import os
import sys
import json
from logging.handlers import RotatingFileHandler
from typing import Optional, Dict, Any


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging output."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON string."""
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        # Add extra fields if present
        if hasattr(record, "context"):
            log_data["context"] = record.context

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def get_console_handler(console_level: int = logging.INFO) -> logging.Handler:
    """Create console handler with specified level."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(console_level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(message)s"
    )
    handler.setFormatter(formatter)
    return handler


def get_file_handler(
    log_file: str,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> RotatingFileHandler:
    """Create rotating file handler."""
    os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else ".", exist_ok=True)

    handler = RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count
    )
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(message)s"
    )
    handler.setFormatter(formatter)
    return handler


def get_json_file_handler(
    log_file: str,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> RotatingFileHandler:
    """Create rotating JSON file handler."""
    os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else ".", exist_ok=True)

    handler = RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count
    )
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(JsonFormatter())
    return handler


class ContextFilter(logging.Filter):
    """Filter to add context to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add context to record if not present."""
        if not hasattr(record, "context"):
            record.context = {}
        return True


def get_logger(
    name: str = "duplicate_service_cleanup",
    log_file: Optional[str] = None,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    use_json: bool = False,
) -> logging.Logger:
    """
    Get configured logger instance.

    Args:
        name: Logger name
        log_file: Path to log file (optional, for file logging)
        console_level: Log level for console output
        file_level: Log level for file output
        use_json: Use JSON format for file output

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Capture all levels

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    logger.addFilter(ContextFilter())

    # Console handler
    logger.addHandler(get_console_handler(console_level))

    # File handler (optional)
    if log_file:
        if use_json:
            logger.addHandler(get_json_file_handler(log_file))
        else:
            logger.addHandler(get_file_handler(log_file))

    return logger


# Default logger instance
default_logger = None


def init_logger(
    log_file: Optional[str] = None,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    use_json: bool = False,
) -> logging.Logger:
    """
    Initialize the default logger with specified settings.

    Args:
        log_file: Path to log file (optional)
        console_level: Log level for console output
        file_level: Log level for file output
        use_json: Use JSON format for file output

    Returns:
        Default logger instance
    """
    global default_logger
    default_logger = get_logger(
        name="duplicate_service_cleanup",
        log_file=log_file,
        console_level=console_level,
        file_level=file_level,
        use_json=use_json,
    )
    return default_logger


def get_default_logger() -> logging.Logger:
    """
    Get the default logger instance.

    Returns:
        Default logger instance
    """
    global default_logger
    if default_logger is None:
        default_logger = get_logger()
    return default_logger