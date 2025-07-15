"""
ServiceNow API client for the migration.
"""

import json
import os
import logging
import requests
import base64
from typing import Dict, List, Any, Optional
from config import config


class ServiceNowClient:
    """Client for interacting with the ServiceNow API."""
    
    def __init__(self):
        """Initialize the ServiceNow API client."""
        self.api_url = config.get("servicenow.api_url", "https://coretelligentdev.service-now.com/api/now")
        self.username = config.get("servicenow.username")
        self.password = config.get("servicenow.password")
        self.timeout = config.get("servicenow.timeout", 30)
        
        self.logger = logging.getLogger(__name__)
        
        # Validate credentials
        if not self.username or not self.password:
            self.logger.error("ServiceNow credentials not configured. Please set SERVICENOW_USERNAME and SERVICENOW_PASSWORD environment variables or update config.yaml.")
            raise ValueError("ServiceNow credentials not configured")
        
        self.logger.info(f"Initialized ServiceNow client with API URL: {self.api_url}")
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers for API requests.
        
        Returns:
            Dictionary of request headers
        """
        auth = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
        return {
            "Authorization": f"Basic {auth}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
    
    def _make_request(self, endpoint: str, method: str = "GET", params: Dict = None, data: Dict = None) -> Dict:
        """
        Make a request to the ServiceNow API.
        
        Args:
            endpoint: API endpoint (without leading slash)
            method: HTTP method (GET, POST, etc.)
            params: Query parameters
            data: Request body data
            
        Returns:
            API response as dictionary
        """
        url = f"{self.api_url}/{endpoint}"
        headers = self._get_headers()
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data,
                timeout=self.timeout
            )
            
            # Raise for errors
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            raise
    
    def get_companies(self, name_filter: str = None) -> List[Dict]:
        """
        Get companies with optional name filter.
        
        Args:
            name_filter: Optional name filter
            
        Returns:
            List of matching companies
        """
        params = {}
        if name_filter:
            params["sysparm_query"] = f"nameLIKE{name_filter}"
        
        response = self._make_request("table/core_company", params=params)
        return response.get("result", [])
    
    def get_company_by_sys_id(self, sys_id: str) -> Optional[Dict]:
        """
        Get a company by sys_id.
        
        Args:
            sys_id: ServiceNow sys_id
            
        Returns:
            Company data or None if not found
        """
        try:
            # Direct endpoint for getting a specific company by sys_id
            params = {
                "sysparm_query": f"sys_id={sys_id}"
            }
            
            response = self._make_request("table/core_company", params=params)
            
            # Log the response for debugging
            self.logger.debug(f"ServiceNow API response for company sys_id {sys_id}: {str(response)[:200]}...")
            
            results = response.get("result", [])
            
            if results:
                return results[0]
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get company by sys_id {sys_id}: {e}")
            return None
    
    def get_company_by_name(self, name: str) -> Optional[Dict]:
        """
        Get a company by exact name.
        
        Args:
            name: Company name
            
        Returns:
            Company data or None if not found
        """
        try:
            params = {
                "sysparm_query": f"name={name}"
            }
            response = self._make_request("table/core_company", params=params)
            results = response.get("result", [])
            
            if results:
                return results[0]
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get company by name {name}: {e}")
            return None
    
    def get_company_by_coreid(self, coreid: str) -> Optional[Dict]:
        """
        Get a company by CoreID.
        
        Args:
            coreid: CoreID
            
        Returns:
            Company data or None if not found
        """
        try:
            params = {
                "sysparm_query": f"u_core_id={coreid}"
            }
            response = self._make_request("table/core_company", params=params)
            results = response.get("result", [])
            
            if results:
                return results[0]
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get company by CoreID {coreid}: {e}")
            return None
    
    def create_company(self, company_data: Dict) -> Dict:
        """
        Create a new company.
        
        Args:
            company_data: Company data
            
        Returns:
            Created company data
        """
        response = self._make_request("table/core_company", method="POST", data=company_data)
        return response.get("result", {})
    
    def update_company(self, sys_id: str, company_data: Dict) -> Optional[Dict]:
        """
        Update an existing company.
        
        Args:
            sys_id: Company sys_id
            company_data: Updated company data
            
        Returns:
            Updated company data or None if not found
        """
        try:
            response = self._make_request(f"table/core_company/{sys_id}", method="PATCH", data=company_data)
            return response.get("result", {})
        except Exception as e:
            self.logger.error(f"Failed to update company {sys_id}: {e}")
            return None
    
    def test_connection(self) -> bool:
        """
        Test the connection to the ServiceNow API.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Try to get a single company to test connection
            params = {
                "sysparm_limit": 1
            }
            response = self._make_request("table/core_company", params=params)
            return "result" in response
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False