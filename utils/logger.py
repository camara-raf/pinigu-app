"""
Centralized logging configuration for the Pinigu Finance Analyzer application.
Provides a logger that writes to both console and rotating log files.
"""
import logging
import os
from datetime import datetime


# Create logs directory if it doesn't exist
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# Generate log filename with timestamp for this session
LOG_FILENAME = f"pinigu_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
LOG_PATH = os.path.join(LOGS_DIR, LOG_FILENAME)

# Define log formats
# File format: best practices with datetime, level, logger name, and message
FILE_LOG_FORMAT = "%(asctime)s %(levelname)s [%(filename)s - %(funcName)s] %(message)s"
FILE_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Console format: simplified with time only (HH:MM:SS) and func name
CONSOLE_LOG_FORMAT = "%(asctime)s %(levelname)s [%(funcName)s] %(message)s"
CONSOLE_DATE_FORMAT = "%H:%M:%S"

# Global logger instance
_logger = None


def get_logger(name=None):
    """
    Get or create the application logger.
    
    Args:
        name: Optional logger name. If None, uses root logger.
        
    Returns:
        logging.Logger: Configured logger instance
    """
    global _logger
    
    if _logger is not None:
        return _logger
    
    # Create logger
    logger = logging.getLogger(name or "pinigu")
    logger.setLevel(logging.INFO)
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        _logger = logger
        return _logger
    
    # Create formatters
    console_formatter = logging.Formatter(CONSOLE_LOG_FORMAT, datefmt=CONSOLE_DATE_FORMAT)
    file_formatter = logging.Formatter(FILE_LOG_FORMAT, datefmt=FILE_DATE_FORMAT)
    
    # Console handler (stdout) - simplified format with time only
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler - best practices format with full datetime
    file_handler = logging.FileHandler(LOG_PATH, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Prevent propagation to avoid duplicate logs
    logger.propagate = False
    
    _logger = logger
    return _logger
