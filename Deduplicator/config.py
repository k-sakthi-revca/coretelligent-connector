#!/usr/bin/env python3
"""
Configuration settings for the ITGlue to ServiceNow Deduplication Tool.

This module defines default configuration settings that can be overridden
by a configuration file provided at runtime.

Author: Coretelligent Migration Team
Date: July 2023
"""

# Default configuration settings
DEFAULT_CONFIG = {
    # Logging configuration
    "logging": {
        "level": "INFO",  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "log_to_file": False,
        "log_file": "deduplication.log"
    },
    
    # Confidence thresholds for match scoring
    "confidence_thresholds": {
        "high": 0.8,    # Scores >= 0.8 are high confidence (automatic update)
        "medium": 0.6   # Scores >= 0.6 but < 0.8 are medium confidence (manual review)
                        # Scores < 0.6 are low confidence (create new)
    },
    
    # Weights for the match score calculation
    "match_weights": {
        "serial_number": 0.4,  # 40% weight for serial number
        "mac_address": 0.3,    # 30% weight for MAC address
        "hostname": 0.2,       # 20% weight for hostname
        "name": 0.1            # 10% weight for name
    },
    
    # ITGlue API configuration
    "itglue_api": {
        "base_url": "https://api.itglue.com/v1",
        "rate_limit": 1000,  # Requests per minute
        "timeout": 30,       # Seconds
        "retry_attempts": 3
    },
    
    # ServiceNow API configuration
    "servicenow_api": {
        "base_url": "https://{instance}.service-now.com/api/now/v1",
        "batch_size": 100,   # Records per batch
        "timeout": 30,       # Seconds
        "retry_attempts": 3
    },
    
    # Data filtering settings
    "data_filters": {
        # Organization statuses to include
        "allowed_org_statuses": [
            "Active", 
            "Active - Popup", 
            "Credit Hold", 
            "Product Only", 
            "Presales", 
            "Service Hold Phase 1", 
            "Service Hold Phase 2", 
            "Service Hold Phase 3", 
            "Pre-Pay Only", 
            "Staff Augmentation"
        ],
        
        # Skip Product Only assets with this text
        "skip_product_only_text": "Not Managed By Coretelligent",
        
        # Skip archived records
        "skip_archived": True
    },
    
    # Output settings
    "output": {
        "report_format": "json",  # Options: json, csv
        "manual_review_format": "csv",
        "include_timestamps": True
    },
    
    # Error handling settings
    "error_handling": {
        "continue_on_error": True,  # Continue processing if an error occurs
        "max_errors": 100,          # Maximum number of errors before aborting
        "retry_on_api_error": True,
        "retry_delay": 5            # Seconds between retries
    }
}


def get_default_config():
    """
    Get the default configuration settings.
    
    Returns:
        dict: Default configuration settings
    """
    return DEFAULT_CONFIG.copy()
