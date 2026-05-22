"""
Structured JSON logging with loguru
"""

from loguru import logger
import sys

# Remove default handler
logger.remove()

# Console output (human readable)
logger.add(sys.stdout, format="{time} | {level} | {message}", level="INFO")

# JSON file output (for telemetry)
logger.add(
    "logs/orchestrator.json",
    format="{time} | {level} | {message}",
    serialize=True,
    retention="30 days",
    level="DEBUG"
)

def log_event(device_id: str, operation: str, severity: str, message: str, **extra):
    logger.log(
        severity.upper(),
        message,
        device_id=device_id,
        operation=operation,
        **extra
    )

# Create logs directory
import os
os.makedirs("logs", exist_ok=True)
