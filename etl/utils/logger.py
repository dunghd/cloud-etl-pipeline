"""Logging utilities for the ETL pipeline"""

import logging
import os
from pathlib import Path
from typing import Optional
from datetime import datetime


def setup_logger(
    name: str,
    log_level: str = "INFO",
    log_dir: Optional[str] = None,
    log_to_console: bool = True,
    log_to_file: bool = True
) -> logging.Logger:
    """
    Set up a logger with console and file handlers
    
    Args:
        name: Logger name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files
        log_to_console: Whether to log to console
        log_to_file: Whether to log to file
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_to_file:
        if log_dir is None:
            log_dir = os.path.join(
                Path(__file__).parent.parent.parent,
                "logs"
            )
        
        os.makedirs(log_dir, exist_ok=True)
        
        # Create log file with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(log_dir, f"{name}_{timestamp}.log")
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


class LoggerMixin:
    """Mixin class to add logging capabilities to any class"""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger for the class"""
        if not hasattr(self, '_logger'):
            self._logger = setup_logger(
                self.__class__.__name__,
                log_level=os.getenv('LOG_LEVEL', 'INFO')
            )
        return self._logger
