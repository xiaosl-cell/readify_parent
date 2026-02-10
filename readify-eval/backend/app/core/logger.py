"""
Logging configuration with daily rotating file handler
"""
import logging
import os
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    log_dir: str = "logs",
    log_file: str = "app.log",
    backup_count: int = 30,
    console_output: bool = True,
    console_level: Optional[str] = None,
    file_level: Optional[str] = None
) -> None:
    """
    Setup logging with daily rotating file handler
    
    Args:
        log_level: Default logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log message format
        log_dir: Directory to store log files
        log_file: Base name of the log file
        backup_count: Number of backup files to keep (days)
        console_output: Whether to output logs to console
        console_level: Console logging level (if None, uses log_level)
        file_level: File logging level (if None, uses log_level)
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Determine effective levels
    effective_console_level = console_level if console_level else log_level
    effective_file_level = file_level if file_level else log_level
    
    # Get the root logger
    # Set to the lowest level among console and file to capture all messages
    min_level = min(
        getattr(logging, effective_console_level.upper()),
        getattr(logging, effective_file_level.upper())
    )
    root_logger = logging.getLogger()
    root_logger.setLevel(min_level)
    
    # Remove existing handlers to avoid duplication
    root_logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Create and configure file handler (daily rotation)
    file_handler = TimedRotatingFileHandler(
        filename=os.path.join(log_dir, log_file),
        when='midnight',  # Rotate at midnight
        interval=1,  # Every day
        backupCount=backup_count,  # Keep N days of logs
        encoding='utf-8',
        utc=False  # Use local time
    )
    file_handler.setLevel(getattr(logging, effective_file_level.upper()))
    file_handler.setFormatter(formatter)
    
    # Set the suffix for rotated files (YYYY-MM-DD format)
    file_handler.suffix = "%Y-%m-%d"
    
    # Add file handler to root logger
    root_logger.addHandler(file_handler)
    
    # Optionally add console handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, effective_console_level.upper()))
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # Configure SQLAlchemy logging level
    # SQLAlchemy emits SQL logs at INFO level, so we need to control it separately
    sqlalchemy_logger = logging.getLogger('sqlalchemy.engine')
    
    # If console is DEBUG, allow SQL logs to console (they'll be filtered by console handler)
    # If file is not DEBUG, we need to raise sqlalchemy logger level to prevent SQL in file
    if effective_console_level.upper() == 'DEBUG' and effective_file_level.upper() != 'DEBUG':
        # Console shows SQL, but file doesn't - this is tricky
        # We keep sqlalchemy at INFO, but add a filter to file handler
        sqlalchemy_logger.setLevel(logging.INFO)
        
        # Add filter to file handler to exclude sqlalchemy.engine logs
        class NoSQLAlchemyFilter(logging.Filter):
            def filter(self, record):
                return not record.name.startswith('sqlalchemy.engine')
        
        file_handler.addFilter(NoSQLAlchemyFilter())
        sql_config_msg = "SQL logs enabled in console only (filtered from file)"
    elif effective_console_level.upper() == 'DEBUG' or effective_file_level.upper() == 'DEBUG':
        # At least one is DEBUG, show SQL everywhere
        sqlalchemy_logger.setLevel(logging.INFO)
        sql_config_msg = "SQL logs enabled (DEBUG level active)"
    else:
        # Neither is DEBUG, suppress SQL logs completely
        sqlalchemy_logger.setLevel(logging.WARNING)
        sql_config_msg = "SQL logs disabled (set console_level or file_level to DEBUG to enable)"
    
    # Log the setup completion
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured: console_level={effective_console_level}, file_level={effective_file_level}, log_dir={log_dir}, file={log_file}")
    if effective_console_level != effective_file_level:
        logger.info(f"Console and file using different log levels (Console: {effective_console_level}, File: {effective_file_level})")
    logger.info(sql_config_msg)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance
    
    Args:
        name: Name of the logger (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

