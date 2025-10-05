"""
Structured logging configuration for production

Provides JSON-formatted logging with custom fields for debugging and monitoring.
Supports both console and file logging with configurable levels.

Features:
- JSON formatting for log aggregation systems
- Custom fields (request_id, user_id, duration_ms)
- Console and file handlers
- Third-party library noise reduction
- Production-ready configuration
"""

import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path


try:
    from pythonjsonlogger import jsonlogger
    JSON_LOGGER_AVAILABLE = True
except ImportError:
    JSON_LOGGER_AVAILABLE = False


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields"""
    
    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any]
    ) -> None:
        """
        Add custom fields to log record
        
        Args:
            log_record: Dictionary to populate with log data
            record: Original logging record
            message_dict: Additional message data
        """
        super().add_fields(log_record, record, message_dict)
        
        # Add standard fields
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['module'] = record.module
        log_record['function'] = record.funcName
        log_record['line'] = record.lineno
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        if hasattr(record, 'duration_ms'):
            log_record['duration_ms'] = record.duration_ms
        if hasattr(record, 'event'):
            log_record['event'] = record.event


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = "logs/app.log",
    json_logs: bool = True
) -> None:
    """
    Configure application logging
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (None to disable file logging)
        json_logs: Use JSON formatting (True) or plain text (False)
        
    Example:
        >>> setup_logging(level="DEBUG", json_logs=True)
        >>> logger = logging.getLogger(__name__)
        >>> logger.info("Application started", extra={"version": "2.0.0"})
    """
    # Create log directory if needed
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create formatters
    if json_logs and JSON_LOGGER_AVAILABLE:
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(logger)s %(message)s'
        )
    else:
        if json_logs and not JSON_LOGGER_AVAILABLE:
            print(
                "Warning: python-json-logger not installed. "
                "Using plain text logging. "
                "Install with: pip install python-json-logger",
                file=sys.stderr
            )
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - '
            '%(module)s:%(funcName)s:%(lineno)d - %(message)s'
        )
    
    # Console handler (stdout for INFO+, stderr for WARNING+)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Add console handler
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("moviepy").setLevel(logging.WARNING)
    logging.getLogger("imageio").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    
    # Log startup
    startup_extra = {
        "level": level,
        "json_logs": json_logs,
        "log_file": log_file or "console-only",
        "event": "logging_configured"
    }
    
    if json_logs and JSON_LOGGER_AVAILABLE:
        root_logger.info("Logging configured", extra=startup_extra)
    else:
        root_logger.info(
            f"Logging configured: level={level}, "
            f"json={json_logs}, file={log_file}"
        )
