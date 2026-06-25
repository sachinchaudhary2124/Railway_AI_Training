import logging
import sys
from logging.handlers import RotatingFileHandler
from backend.utils.config import LOG_DIR

# Path to the primary application log file
LOG_FILE = LOG_DIR / "app.log"

# Define log format
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] [%(filename)s:%(lineno)d] - %(message)s"

def setup_logger(name: str = "railway_api") -> logging.Logger:
    """
    Configures and returns a professional logger that writes to both console and a rotating log file.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers if logger is already initialized
    if logger.handlers:
        return logger

    # Formatter
    formatter = logging.Formatter(LOG_FORMAT)

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    # Rotating File Handler (Max 10MB per file, keep last 5 logs)
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    # Make sure log messages propagate properly
    logger.propagate = False

    return logger

# Shared logger instance
logger = setup_logger()
