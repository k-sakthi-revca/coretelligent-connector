#!/usr/bin/env python3
"""
Utility functions for the ITGlue to ServiceNow Deduplication Tool.

This module provides helper functions for data normalization, similarity calculation,
logging setup, configuration loading, and result saving.

Author: Coretelligent Migration Team
Date: July 2023
"""

import os
import re
import json
import yaml
import logging
import difflib
# Remove type hints for compatibility with older Python versions
# from typing import Dict, List, Any, Union, Optional
from datetime import datetime


def normalize_data(data):
    """
    Normalize data fields for consistent comparison.
    
    Performs the following normalizations:
    - Trim whitespace from text fields
    - Normalize MAC address formats (XX:XX:XX:XX:XX:XX)
    - Validate IP address formats
    - Convert date strings to proper date objects
    
    Args:
        data: List of record dictionaries to normalize
        
    Returns:
        List[Dict]: Normalized data records
    """
    normalized_data = []
    
    for record in data:
        normalized_record = record.copy()
        
        # Normalize text fields
        for field in ["name", "hostname", "serial_number", "asset_tag", "notes"]:
            if field in normalized_record and normalized_record[field]:
                if isinstance(normalized_record[field], str):
                    normalized_record[field] = normalized_record[field].strip()
        
        # Normalize MAC address
        if "mac_address" in normalized_record and normalized_record["mac_address"]:
            normalized_record["mac_address"] = normalize_mac_address(normalized_record["mac_address"])
        
        # Normalize IP address
        if "primary_ip" in normalized_record and normalized_record["primary_ip"]:
            normalized_record["primary_ip"] = normalize_ip_address(normalized_record["primary_ip"])
        
        # Normalize dates
        for field in ["created_at", "updated_at", "expires_on"]:
            if field in normalized_record and normalized_record[field]:
                normalized_record[field] = normalize_date(normalized_record[field])
        
        normalized_data.append(normalized_record)
    
    return normalized_data


def normalize_mac_address(mac):
    """
    Normalize MAC address to XX:XX:XX:XX:XX:XX format.
    
    Args:
        mac: MAC address string
        
    Returns:
        str: Normalized MAC address
    """
    if not mac or not isinstance(mac, str):
        return ""
    
    # Remove all non-hexadecimal characters
    mac = re.sub(r'[^0-9a-fA-F]', '', mac.upper())
    
    # Check if we have a valid MAC address (12 hex digits)
    if len(mac) != 12:
        return mac  # Return as is if not valid
    
    # Format as XX:XX:XX:XX:XX:XX
    return ':'.join(mac[i:i+2] for i in range(0, 12, 2))


def normalize_ip_address(ip):
    """
    Normalize IP address format.
    
    Args:
        ip: IP address string
        
    Returns:
        str: Normalized IP address
    """
    if not ip or not isinstance(ip, str):
        return ""
    
    # Remove any whitespace
    ip = ip.strip()
    
    # Check if it's an IPv4 address
    ipv4_pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})(/\d{1,2})?$'
    match = re.match(ipv4_pattern, ip)
    
    if match:
        # Extract the IP without subnet mask if present
        ip_parts = [int(match.group(i)) for i in range(1, 5)]
        
        # Validate each octet
        if all(0 <= part <= 255 for part in ip_parts):
            return '.'.join(str(part) for part in ip_parts)
    
    # For IPv6 or invalid formats, return as is
    return ip


def normalize_date(date_str):
    """
    Normalize date string to ISO format.
    
    Args:
        date_str: Date string
        
    Returns:
        str: Normalized date string
    """
    if not date_str or not isinstance(date_str, str):
        return ""
    
    # Common date formats to try
    formats = [
        '%Y-%m-%d',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%dT%H:%M:%S.%fZ',
        '%Y/%m/%d',
        '%m/%d/%Y',
        '%d/%m/%Y',
        '%b %d, %Y',
        '%B %d, %Y'
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.isoformat()
        except ValueError:
            continue
    
    # Return as is if no format matches
    return date_str


def calculate_similarity(str1, str2):
    """
    Calculate similarity between two strings using difflib's SequenceMatcher.
    
    Args:
        str1: First string
        str2: Second string
        
    Returns:
        float: Similarity score between 0.0 and 1.0
    """
    if not str1 and not str2:
        return 1.0  # Both empty means they're identical
    
    if not str1 or not str2:
        return 0.0  # One empty means no similarity
    
    # Use difflib's SequenceMatcher for string similarity
    return difflib.SequenceMatcher(None, str1, str2).ratio()


def calculate_match_score(itg_record, sn_record):
    """
    Calculate the match score between an ITGlue record and a ServiceNow record.
    
    The weighted formula is:
    Match Score = (
        0.4 * serial_number_similarity +
        0.3 * mac_address_similarity +
        0.2 * hostname_similarity +
        0.1 * name_similarity
    )
    
    Args:
        itg_record: The ITGlue record
        sn_record: The ServiceNow record
        
    Returns:
        float: The match score (0.0 to 1.0)
    """
    # Extract fields for comparison
    itg_serial = itg_record.get("serial_number", "").strip()
    sn_serial = sn_record.get("serial_number", "").strip()
    
    itg_mac = itg_record.get("mac_address", "").strip()
    sn_mac = sn_record.get("mac_address", "").strip()
    
    itg_hostname = itg_record.get("hostname", "").strip()
    sn_hostname = sn_record.get("hostname", "").strip()
    
    itg_name = itg_record.get("name", "").strip()
    sn_name = sn_record.get("name", "").strip()
    
    # Calculate similarities
    serial_similarity = calculate_similarity(itg_serial, sn_serial)
    mac_similarity = calculate_similarity(itg_mac, sn_mac)
    hostname_similarity = calculate_similarity(itg_hostname, sn_hostname)
    name_similarity = calculate_similarity(itg_name, sn_name)
    
    # Apply weighted formula
    match_score = (
        0.4 * serial_similarity +
        0.3 * mac_similarity +
        0.2 * hostname_similarity +
        0.1 * name_similarity
    )
    
    return match_score


def setup_logging(log_level=logging.INFO, log_file=None):
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (default: INFO)
        log_file: Path to log file (optional)
    """
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # Add console handler to logger
    logger.addHandler(console_handler)
    
    # Add file handler if log_file is provided
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)


def load_config(config_path=None):
    """
    Load configuration from a YAML or JSON file.
    
    Args:
        config_path: Path to the configuration file (optional)
        
    Returns:
        Dict: Configuration settings
    """
    # Default configuration
    default_config = {
        "log_level": "INFO",
        "confidence_thresholds": {
            "high": 0.8,
            "medium": 0.6
        },
        "match_weights": {
            "serial_number": 0.4,
            "mac_address": 0.3,
            "hostname": 0.2,
            "name": 0.1
        },
        "api": {
            "itglue": {
                "base_url": "https://api.itglue.com",
                "rate_limit": 1000
            },
            "servicenow": {
                "base_url": "https://instance.service-now.com",
                "batch_size": 100
            }
        }
    }
    
    # If no config path provided, return default config
    if not config_path:
        return default_config
    
    # Check if config file exists
    if not os.path.exists(config_path):
        logging.warning("Config file not found: " + config_path + ". Using default configuration.")
        return default_config
    
    try:
        # Load config based on file extension
        _, ext = os.path.splitext(config_path)
        
        if ext.lower() in ['.yml', '.yaml']:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        elif ext.lower() == '.json':
            with open(config_path, 'r') as f:
                config = json.load(f)
        else:
            logging.warning("Unsupported config file format: {}. Using default configuration.".format(ext))
            return default_config
        
        # Merge with default config to ensure all required settings are present
        merged_config = default_config.copy()
        merged_config.update(config)
        
        return merged_config
        
    except Exception as e:
        logging.error("Error loading config file: {}. Using default configuration.".format(str(e)))
        return default_config


def save_results(results, output_path):
    """
    Save deduplication results to a file.
    
    Args:
        results: Deduplication results
        output_path: Path to save the results
    """
    try:
        # Create directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Save results to file
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logging.info("Results saved to {}".format(output_path))
        
    except Exception as e:
        logging.error("Error saving results: {}".format(str(e)))
        raise
