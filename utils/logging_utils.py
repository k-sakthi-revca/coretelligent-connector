"""
Logging utility functions for the migration demo.
"""

import logging
import os
from datetime import datetime


def setup_logging(log_level: str = "INFO", log_file: str = None) -> None:
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
    """
    # Convert string log level to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create handlers list
    handlers = [logging.StreamHandler()]
    
    # Add file handler if log_file is specified
    if log_file:
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Add file handler
        handlers.append(logging.FileHandler(log_file))
    
    # Configure logging
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


def get_timestamped_log_file(base_name: str = "migration", log_dir: str = "logs") -> str:
    """
    Get a timestamped log file path.
    
    Args:
        base_name: Base name for the log file
        log_dir: Directory for log files
        
    Returns:
        Path to the log file
    """
    # Create timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Create log file name
    log_file = f"{base_name}_{timestamp}.log"
    
    # Return full path
    return os.path.join(log_dir, log_file)