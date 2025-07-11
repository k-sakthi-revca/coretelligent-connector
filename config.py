"""
Configuration loader for the IT Glue to ServiceNow migration demo.
"""

import os
import yaml
from dotenv import load_dotenv
from typing import Dict, Any


class Config:
    """Configuration manager for the migration demo."""
    
    def __init__(self, config_file: str = "config.yaml"):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to the configuration file
        """
        # Load environment variables from .env file
        load_dotenv()
        
        # Load configuration from YAML file
        self.config_file = config_file
        self.config = self._load_config()
        
        # Override with environment variables
        self._override_from_env()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file.
        
        Returns:
            Configuration dictionary
        """
        try:
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
            return config or {}
        except Exception as e:
            print(f"Error loading configuration from {self.config_file}: {e}")
            return {}
    
    def _override_from_env(self):
        """Override configuration with environment variables."""
        # IT Glue API settings
        if os.getenv("ITGLUE_API_URL"):
            self.config.setdefault("itglue", {})["api_url"] = os.getenv("ITGLUE_API_URL")
        
        if os.getenv("ITGLUE_API_KEY"):
            self.config.setdefault("itglue", {})["api_key"] = os.getenv("ITGLUE_API_KEY")
        
        # Optional settings
        if os.getenv("ORGANIZATION_LIMIT"):
            self.config.setdefault("itglue", {})["organization_limit"] = int(os.getenv("ORGANIZATION_LIMIT"))
        
        if os.getenv("LOG_LEVEL"):
            self.config.setdefault("output", {})["log_level"] = os.getenv("LOG_LEVEL")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key (dot notation supported)
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        # Handle dot notation (e.g., "itglue.api_url")
        if "." in key:
            parts = key.split(".")
            value = self.config
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return default
            return value
        
        return self.config.get(key, default)
    
    def get_field_mappings(self) -> Dict[str, str]:
        """
        Get field mappings from IT Glue to ServiceNow.
        
        Returns:
            Dictionary of field mappings
        """
        return self.get("field_mappings", {})
    
    def get_matching_settings(self) -> Dict[str, Any]:
        """
        Get organization matching settings.
        
        Returns:
            Dictionary of matching settings
        """
        return self.get("matching", {})
    
    def get_valid_statuses(self) -> list:
        """
        Get list of valid organization statuses.
        
        Returns:
            List of valid status names
        """
        return self.get("valid_statuses", [])


# Create a global config instance
config = Config()