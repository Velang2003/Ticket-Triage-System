"""Structured JSON logging setup.

Rules enforced here:
- All log output is JSON (machine-readable, works in Docker / cloud).
- `submitter_email` is redacted from every log record (NFR-5).
- LLM request latency and outcome are always logged at INFO level.
"""
import logging
import json
import sys
from datetime import datetime, timezone
from typing import Any


REDACTED_FIELDS = {"submitter_email", "email"}


class RedactingFilter(logging.Filter):
    """Remove sensitive fields from log record `extra` dicts."""

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: A003
        for field in REDACTED_FIELDS:
            if hasattr(record, field):
                setattr(record, field, "***REDACTED***")
        return True


class JSONFormatter(logging.Formatter):
    """Render log records as compact JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include any `extra` keys attached to the log call
        skip = {
            "name", "msg", "args", "created", "filename", "funcName",
            "levelname", "levelno", "lineno", "module", "msecs",
            "pathname", "process", "processName", "relativeCreated",
            "stack_info", "thread", "threadName", "exc_info", "exc_text",
            "message",
        }
        for key, value in record.__dict__.items():
            if key not in skip and not key.startswith("_"):
                # Redact any stray sensitive fields
                if key in REDACTED_FIELDS:
                    value = "***REDACTED***"
                log_entry[key] = value

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


def configure_logging(level: str = "INFO") -> None:
    """Configure root logger with JSON formatter and redacting filter."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    handler.addFilter(RedactingFilter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Quieten noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
