"""
Utility functions for the migration demo.
"""

import os
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from colorama import init, Fore, Style


# Initialize colorama for colored console output
init()


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path
    """
    # Create logs directory if it doesn't exist
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
    
    # Set up logging format
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Set up logging level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure logging
    if log_file:
        logging.basicConfig(
            level=numeric_level,
            format=log_format,
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    else:
        logging.basicConfig(
            level=numeric_level,
            format=log_format
        )
    
    # Suppress verbose logging from libraries
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def print_colored(message: str, color: str = Fore.WHITE, bold: bool = False) -> None:
    """
    Print colored message to console.
    
    Args:
        message: Message to print
        color: Text color
        bold: Whether to print in bold
    """
    style = Style.BRIGHT if bold else ""
    print(f"{style}{color}{message}{Style.RESET_ALL}")


def print_header(title: str) -> None:
    """
    Print a header with the given title.
    
    Args:
        title: Header title
    """
    print_colored("\n" + "=" * 80, Fore.CYAN, bold=True)
    print_colored(f" {title}", Fore.CYAN, bold=True)
    print_colored("=" * 80, Fore.CYAN, bold=True)


def print_subheader(title: str) -> None:
    """
    Print a subheader with the given title.
    
    Args:
        title: Subheader title
    """
    print_colored("\n" + "-" * 80, Fore.CYAN)
    print_colored(f" {title}", Fore.CYAN)
    print_colored("-" * 80, Fore.CYAN)


def print_success(message: str) -> None:
    """
    Print a success message.
    
    Args:
        message: Success message
    """
    print_colored(f"✅ {message}", Fore.GREEN)


def print_error(message: str) -> None:
    """
    Print an error message.
    
    Args:
        message: Error message
    """
    print_colored(f"❌ {message}", Fore.RED)


def print_warning(message: str) -> None:
    """
    Print a warning message.
    
    Args:
        message: Warning message
    """
    print_colored(f"⚠️  {message}", Fore.YELLOW)


def print_info(message: str) -> None:
    """
    Print an info message.
    
    Args:
        message: Info message
    """
    print_colored(f"ℹ️  {message}", Fore.BLUE)


def save_json(data: Any, file_path: str, indent: int = 2) -> bool:
    """
    Save data to JSON file.
    
    Args:
        data: Data to save
        file_path: File path
        indent: JSON indentation
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=indent)
        
        return True
    except Exception as e:
        logging.error(f"Failed to save JSON file {file_path}: {e}")
        return False


def load_json(file_path: str) -> Optional[Any]:
    """
    Load data from JSON file.
    
    Args:
        file_path: File path
        
    Returns:
        Loaded data or None if failed
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load JSON file {file_path}: {e}")
        return None


def format_timestamp(timestamp: Optional[str] = None) -> str:
    """
    Format timestamp for file names.
    
    Args:
        timestamp: Optional timestamp string
        
    Returns:
        Formatted timestamp
    """
    if timestamp:
        try:
            dt = datetime.fromisoformat(timestamp)
        except ValueError:
            dt = datetime.now()
    else:
        dt = datetime.now()
    
    return dt.strftime("%Y%m%d_%H%M%S")


def truncate_string(s: str, max_length: int = 50) -> str:
    """
    Truncate string to maximum length.
    
    Args:
        s: String to truncate
        max_length: Maximum length
        
    Returns:
        Truncated string
    """
    if not s:
        return ""
    
    if len(s) <= max_length:
        return s
    
    return s[:max_length-3] + "..."