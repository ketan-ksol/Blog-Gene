"""Centralized logging configuration for the blog generator application.

All logs are configured to output to stdout/stderr for Docker container visibility.
"""
import logging
import sys
import os
from typing import Optional, Callable
from pathlib import Path


# Global logger cache
_loggers = {}

# Global step callback for Streamlit integration
_step_callback: Optional[Callable[[str], None]] = None


def set_step_callback(callback: Optional[Callable[[str], None]]):
    """Set a callback function to handle step updates for Streamlit UI.
    
    Args:
        callback: Function that takes a message string and handles step updates
    """
    global _step_callback
    _step_callback = callback


def setup_logging(
    log_level: Optional[str] = "INFO",
    log_format: Optional[str] = None,
    enable_file_logging: bool = False,
    log_file_path: Optional[str] = None
) -> None:
    """Configure application-wide logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                  Defaults to INFO, or DEBUG if LOG_LEVEL env var is set.
        log_format: Custom log format string. If None, uses default format.
        enable_file_logging: If True, also write logs to a file.
        log_file_path: Path to log file. Defaults to ./logs/blog_generator.log
    """
    # Determine log level from environment or parameter
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    numeric_level = getattr(logging, log_level, logging.INFO)
    
    # Default format: timestamp, level, module, message
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Store original stdout/stderr references for Docker visibility
    # These will be used even if stdout is redirected by Streamlit
    _original_stdout = sys.__stdout__  # Use __stdout__ which is the original, not redirected
    _original_stderr = sys.__stderr__  # Use __stderr__ which is the original, not redirected
    
    # Console handler (stdout) - for Docker visibility
    # Use stdout for INFO and below, stderr for WARNING and above
    # Use __stdout__ to ensure logs always go to Docker, even if stdout is redirected
    stdout_handler = logging.StreamHandler(_original_stdout)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.addFilter(lambda record: record.levelno <= logging.INFO)
    stdout_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(stdout_handler)
    
    # Add a handler that writes raw messages for Streamlit step detection
    # This writes the message directly to stdout without formatting for step pattern matching
    class StreamlitStepHandler(logging.Handler):
        """Handler that writes step messages in format StreamlitStream can parse."""
        def emit(self, record):
            try:
                msg = record.getMessage()
                # Write raw message to current stdout (which may be redirected by Streamlit)
                # Only for step-related messages
                if "Step" in msg and "/7" in msg:
                    # Get current stdout (which may be redirected)
                    current_stdout = sys.stdout
                    # Write directly to current stdout for Streamlit capture
                    current_stdout.write(msg + "\n")
                    current_stdout.flush()
                # Also call step callback if set
                global _step_callback
                if _step_callback and ("Step" in msg or "✓" in msg or "complete" in msg.lower()):
                    _step_callback(msg)
            except Exception:
                pass
    
    step_handler = StreamlitStepHandler()
    step_handler.setLevel(logging.INFO)
    root_logger.addHandler(step_handler)
    
    # Stderr handler - always use original stderr for Docker
    stderr_handler = logging.StreamHandler(_original_stderr)
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(stderr_handler)
    
    # Optional file logging (for persistent logs)
    if enable_file_logging:
        if log_file_path is None:
            log_file_path = os.getenv("LOG_FILE_PATH", "./logs/blog_generator.log")
        
        log_file = Path(log_file_path)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(logging.Formatter(log_format))
        root_logger.addHandler(file_handler)
    
    # Suppress noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance for a module.
    
    Args:
        name: Logger name (typically __name__). If None, returns root logger.
    
    Returns:
        Logger instance configured for the application.
    """
    if name is None:
        name = "root"
    
    # Return cached logger if available
    if name in _loggers:
        return _loggers[name]
    
    # Create new logger
    logger = logging.getLogger(name)
    
    # Cache it
    _loggers[name] = logger
    
    return logger


# Initialize logging on module import
# Check if logging has already been configured
if not logging.getLogger().handlers:
    setup_logging(
        enable_file_logging=os.getenv("ENABLE_FILE_LOGGING", "false").lower() == "true"
    )

