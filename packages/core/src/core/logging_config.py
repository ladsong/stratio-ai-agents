"""Structured logging configuration for nanobot."""
import logging
import sys
from datetime import datetime
from typing import Any


class StructuredFormatter(logging.Formatter):
    """JSON-like structured log formatter."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured output."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, "run_id"):
            log_data["run_id"] = record.run_id
        if hasattr(record, "thread_id"):
            log_data["thread_id"] = record.thread_id
        if hasattr(record, "tool_name"):
            log_data["tool_name"] = record.tool_name
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        if hasattr(record, "from_status"):
            log_data["from_status"] = record.from_status
        if hasattr(record, "to_status"):
            log_data["to_status"] = record.to_status
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Format as key=value pairs for easy parsing
        parts = [f"{k}={v}" for k, v in log_data.items()]
        return " ".join(parts)


def setup_logging(level: int = logging.INFO) -> None:
    """
    Set up structured logging for the application.
    
    Args:
        level: Logging level (default: INFO)
    """
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create console handler with structured formatter
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(StructuredFormatter())
    
    logger.addHandler(handler)
    
    # Set levels for specific loggers
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("alembic").setLevel(logging.INFO)


def log_run_transition(run_id: str, from_status: str, to_status: str) -> None:
    """
    Log a run status transition.
    
    Args:
        run_id: Run ID
        from_status: Previous status
        to_status: New status
    """
    logger = logging.getLogger("core.runs")
    logger.info(
        "Run status transition",
        extra={
            "run_id": run_id,
            "from_status": from_status,
            "to_status": to_status,
        }
    )


def log_tool_execution(
    run_id: str,
    tool_name: str,
    duration_ms: int,
    success: bool,
    error: str | None = None
) -> None:
    """
    Log a tool execution.
    
    Args:
        run_id: Run ID
        tool_name: Tool name
        duration_ms: Execution duration in milliseconds
        success: Whether execution succeeded
        error: Error message if failed
    """
    logger = logging.getLogger("core.tools")
    
    extra: dict[str, Any] = {
        "run_id": run_id,
        "tool_name": tool_name,
        "duration_ms": duration_ms,
    }
    
    if success:
        logger.info("Tool executed successfully", extra=extra)
    else:
        extra["error"] = error
        logger.error("Tool execution failed", extra=extra)


def log_approval_request(run_id: str, approval_type: str) -> None:
    """
    Log an approval request.
    
    Args:
        run_id: Run ID
        approval_type: Type of approval requested
    """
    logger = logging.getLogger("core.approvals")
    logger.info(
        "Approval requested",
        extra={
            "run_id": run_id,
            "approval_type": approval_type,
        }
    )


def log_approval_response(run_id: str, approved: bool, reason: str | None = None) -> None:
    """
    Log an approval response.
    
    Args:
        run_id: Run ID
        approved: Whether approved
        reason: Reason for decision
    """
    logger = logging.getLogger("core.approvals")
    
    extra: dict[str, Any] = {
        "run_id": run_id,
        "approved": approved,
    }
    
    if reason:
        extra["reason"] = reason
    
    logger.info("Approval response received", extra=extra)
