"""Centralized logging configuration using loguru."""
import sys
from pathlib import Path
from loguru import logger
from core.config import settings


def setup_logger():
    """Configure loguru logger with file and console handlers."""
    # Remove default handler
    logger.remove()
    
    # Console handler with color
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True
    )
    
    # File handler with rotation
    logger.add(
        settings.log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        compression="zip"
    )
    
    return logger


# Initialize logger
log = setup_logger()


def log_agent_action(agent_name: str, action: str, details: dict = None):
    """Log agent actions with structured context."""
    msg = f"[{agent_name}] {action}"
    if details:
        msg += f" | {details}"
    log.info(msg)


def log_validation_result(validator: str, passed: bool, errors: list = None):
    """Log validation results."""
    if passed:
        log.success(f"✓ {validator} validation passed")
    else:
        log.error(f"✗ {validator} validation failed")
        if errors:
            for error in errors:
                log.error(f"  - {error}")