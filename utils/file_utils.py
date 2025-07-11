"""
File utility functions for the migration demo.
"""

import json
import logging
from typing import Any, Dict, Optional


def load_json_file(file_path: str) -> Any:
    """
    Load JSON data from a file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Parsed JSON data or None if failed
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load JSON file {file_path}: {e}")
        return None


def save_json_file(data: Any, file_path: str, indent: int = 2) -> bool:
    """
    Save data to a JSON file.
    
    Args:
        data: Data to save
        file_path: Path to save the file
        indent: JSON indentation level
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=indent, default=str)
        logging.info(f"Data saved to {file_path}")
        return True
    except Exception as e:
        logging.error(f"Failed to save data to {file_path}: {e}")
        return False


def load_itglue_assets(file_path: str) -> Optional[Dict]:
    """
    Load IT Glue assets from a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Dictionary of IT Glue assets or None if failed
    """
    data = load_json_file(file_path)
    
    if not data or "data" not in data:
        logging.error(f"Invalid IT Glue asset data format in {file_path}")
        return None
    
    return data


def load_servicenow_data(file_path: str) -> Optional[list]:
    """
    Load ServiceNow data from a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        List of ServiceNow records or None if failed
    """
    data = load_json_file(file_path)
    
    if not data or not isinstance(data, list):
        logging.error(f"Invalid ServiceNow data format in {file_path}")
        return None
    
    return data