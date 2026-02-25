"""
Gold Tier Utilities
Shared utility functions for the Gold Tier system
"""

import logging
import sys
from pathlib import Path


class Utf8StreamHandler(logging.StreamHandler):
    """
    Stream handler that handles UTF-8 encoding for Windows console.
    
    This prevents UnicodeEncodeError when logging emoji characters
    on Windows systems with cp1252 encoding.
    """
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            if hasattr(stream, 'buffer'):
                stream.buffer.write((msg + self.terminator).encode('utf-8', errors='replace'))
                stream.flush()
            else:
                stream.write(msg + self.terminator)
                stream.flush()
        except Exception:
            self.handleError(record)


def setup_logging(log_file: str, logger_name: str = None) -> logging.Logger:
    """
    Set up logging with UTF-8 support for Windows console.
    
    Args:
        log_file: Path to the log file
        logger_name: Name for the logger (default: root logger)
    
    Returns:
        Configured logger instance
    """
    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # File handler with UTF-8 encoding
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    # Console handler with UTF-8 support
    console_handler = Utf8StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def ensure_directories():
    """Create all required directories for the Gold Tier system"""
    dirs = [
        'Inbox',
        'Needs_Action',
        'Plans',
        'Done',
        'Logs',
        'Pending_Approval',
        'Approved',
        'Error',
        'Accounting',
        'Scheduled_Tasks',
        'Gmail_Inbox',
        'WhatsApp_Inbox',
        'LinkedIn_Posts',
        'tokens',
        'Gmail_Archive',
        'Approval_History'
    ]
    
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
    
    return dirs


__all__ = ['Utf8StreamHandler', 'setup_logging', 'ensure_directories']
