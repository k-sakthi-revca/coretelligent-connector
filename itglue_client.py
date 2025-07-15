"""
IT Glue API client for the migration demo.
"""

import json
import os
import time
import logging
from typing import Dict, List, Any, Optional
from config import config


class ITGlueClient:
    """Client for interacting with the IT Glue API."""
    
    def __init__(self, use_mock_data: bool = True):
        """
        Initialize the IT Glue API client.
        
        Args:
            use_mock_data: Whether to use mock data instead of making API calls
        """
        self.api_url = config.get("itglue.api_url", "https://api.itglue.com")
        self.api_key = config.get("itglue.api_key")
        self.rate_limit = config.get("itglue.rate_limit", 1000)
        self.timeout = config.get("itglue.timeout", 30)
        self.organization_limit = config.get("itglue.organization_limit")
        self.use_mock_data = use_mock_data
        
        self.logger = logging.getLogger(__name__)
        
        # Mock data file paths - hardcoded to the specific path
        self.mock_organizations_file = "/Users/swapnilmhatre/migration/organizations.json"
        self.mock_site_summaries_file = "mock_site_summaries.json"
        self.mock_emails_file = os.path.join("data", "emails", "emails.json")
        self.mock_lob_applications_file = os.path.join("data", "lob", "lob_applications.json")
        
        # If using mock data, check if files exist
        if self.use_mock_data:
            self.logger.info("Using mock data instead of making API calls")
            
            # Check if organizations.txt exists
            if not os.path.exists(self.mock_organizations_file):
                self.logger.warning(f"Mock organizations file not found: {self.mock_organizations_file}")
                self.mock_organizations_file = None
            
            # Check if mock_site_summaries.json exists
            if not os.path.exists(self.mock_site_summaries_file):
                self.mock_site_summaries_file = None
                self.logger.warning(f"Mock site summaries file not found: {self.mock_site_summaries_file}")
        else:
            # Validate API key
            if not self.api_key or self.api_key == "your_api_key_here":
                self.logger.error("IT Glue API key not configured. Please set ITGLUE_API_KEY environment variable or update config.yaml.")
                raise ValueError("IT Glue API key not configured")
        
        self.logger.info(f"Initialized IT Glue client with API URL: {self.api_url}")
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers for API requests.
        
        Returns:
            Dictionary of request headers
        """
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/vnd.api+json",
            "Accept": "application/vnd.api+json"
        }
    
    def _make_request(self, endpoint: str, method: str = "GET", params: Dict = None, data: Dict = None) -> Dict:
        """
        Make a request to the IT Glue API.
        
        Args:
            endpoint: API endpoint (without leading slash)
            method: HTTP method (GET, POST, etc.)
            params: Query parameters
            data: Request body data
            
        Returns:
            API response as dictionary
        """
        import requests
        
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
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                self.logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                return self._make_request(endpoint, method, params, data)
            
            # Raise for other errors
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"API request failed: {e}")
            raise
    
    def _paginate_results(self, endpoint: str, params: Dict = None) -> List[Dict]:
        """
        Paginate through API results.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            List of all results
        """
        if params is None:
            params = {}
        
        # Set page size
        params["page[size]"] = 100
        
        all_results = []
        page = 1
        total_pages = 1
        
        while page <= total_pages:
            params["page[number]"] = page
            response = self._make_request(endpoint, params=params)
            
            # Extract data and meta information
            data = response.get("data", [])
            meta = response.get("meta", {})
            
            all_results.extend(data)
            
            # Update pagination info
            total_pages = meta.get("total-pages", 1)
            page += 1
            
            self.logger.debug(f"Retrieved page {page-1}/{total_pages} from {endpoint}")
            
            # Apply organization limit if specified
            if self.organization_limit and len(all_results) >= self.organization_limit:
                self.logger.info(f"Reached organization limit of {self.organization_limit}")
                all_results = all_results[:self.organization_limit]
                break
        
        return all_results
    
    def _load_mock_organizations(self) -> List[Dict]:
        """
        Load mock organization data from file.
        
        Returns:
            List of organization data
        """
        if not self.mock_organizations_file:
            self.logger.warning("Mock organizations file not specified")
            return []
        
        try:
            with open(self.mock_organizations_file, 'r') as f:
                content = f.read()
                # Remove trailing single quote if present (from the file you provided)
                if content.endswith("'"):
                    content = content[:-1]
                # Parse JSON
                data = json.loads(content)
            
            # Ensure data is a list
            if not isinstance(data, list):
                self.logger.error(f"Mock organizations data is not a list: {type(data)}")
                return []
            
            self.logger.info(f"Loaded {len(data)} organizations from mock file: {self.mock_organizations_file}")
            
            # Apply organization limit if specified
            if self.organization_limit and len(data) > self.organization_limit:
                data = data[:self.organization_limit]
                self.logger.info(f"Limited to {len(data)} organizations")
            
            return data
        except Exception as e:
            self.logger.error(f"Failed to load mock organizations: {e}")
            return []
    
    def _load_mock_site_summaries(self) -> List[Dict]:
        """
        Load mock site summary data from file.
        
        Returns:
            List of site summary data
        """
        if not self.mock_site_summaries_file:
            self.logger.warning("Mock site summaries file not specified")
            return []
        
        try:
            with open(self.mock_site_summaries_file, 'r') as f:
                data = json.load(f)
            
            self.logger.info(f"Loaded {len(data)} site summaries from mock file: {self.mock_site_summaries_file}")
            return data
        except Exception as e:
            self.logger.error(f"Failed to load mock site summaries: {e}")
            return []
    
    def get_emails(self) -> List[Dict]:
        """
        Get email assets from IT Glue.
        
        Returns:
            List of email asset data
        """
        self.logger.info("Fetching email assets from IT Glue...")
        
        if self.use_mock_data:
            return self._load_mock_emails()
        
        # In a real implementation, this would fetch email assets from the IT Glue API
        # For now, we'll just return an empty list for non-mock mode
        self.logger.warning("Real API implementation for get_emails() not implemented")
        return []
    
    def get_lob_applications(self) -> List[Dict]:
        """
        Get LoB application assets from IT Glue.
        
        Returns:
            List of LoB application asset data
        """
        self.logger.info("Fetching LoB application assets from IT Glue...")
        
        if self.use_mock_data:
            return self._load_mock_lob_applications()
        
        # In a real implementation, this would fetch LoB application assets from the IT Glue API
        # For now, we'll just return an empty list for non-mock mode
        self.logger.warning("Real API implementation for get_lob_applications() not implemented")
        return []
    
    def _load_mock_emails(self) -> List[Dict]:
        """
        Load mock email data from file.
        
        Returns:
            List of email asset data
        """
        if not os.path.exists(self.mock_emails_file):
            self.logger.warning(f"Mock emails file not found: {self.mock_emails_file}")
            return []
        
        try:
            with open(self.mock_emails_file, 'r') as f:
                data = json.load(f)
            
            # Extract the data array
            emails = data.get("data", [])
            
            self.logger.info(f"Loaded {len(emails)} email assets from mock file: {self.mock_emails_file}")
            return emails
        except Exception as e:
            self.logger.error(f"Failed to load mock emails: {e}")
            return []
    
    def _load_mock_lob_applications(self) -> List[Dict]:
        """
        Load mock LoB application data from file.
        
        Returns:
            List of LoB application asset data
        """
        if not os.path.exists(self.mock_lob_applications_file):
            self.logger.warning(f"Mock LoB applications file not found: {self.mock_lob_applications_file}")
            return []
        
        try:
            # Use UTF-8 encoding to handle special characters
            with open(self.mock_lob_applications_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract the data array
            lob_applications = data.get("data", [])
            
            self.logger.info(f"Loaded {len(lob_applications)} LoB application assets from mock file: {self.mock_lob_applications_file}")
            return lob_applications
        except Exception as e:
            self.logger.error(f"Failed to load mock LoB applications: {e}")
            return []
    
    def get_printing_assets(self) -> List[Dict]:
        """
        Get printing assets from IT Glue.
        
        Returns:
            List of printing asset data
        """
        self.logger.info("Fetching printing assets from IT Glue...")
        
        if self.use_mock_data:
            return self._load_mock_printing_assets()
        
        # In a real implementation, this would fetch printing assets from the IT Glue API
        # For now, we'll just return an empty list for non-mock mode
        self.logger.warning("Real API implementation for get_printing_assets() not implemented")
        return []
    
    def _load_mock_printing_assets(self) -> List[Dict]:
        """
        Load mock printing data from file.
        
        Returns:
            List of printing asset data
        """
        mock_printing_file = os.path.join("data", "printing", "printing.json")
        
        if not os.path.exists(mock_printing_file):
            self.logger.warning(f"Mock printing file not found: {mock_printing_file}")
            return []
        
        try:
            # Use UTF-8 encoding to handle special characters
            with open(mock_printing_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract the data array
            printing_assets = data.get("data", [])
            
            self.logger.info(f"Loaded {len(printing_assets)} printing assets from mock file: {mock_printing_file}")
            return printing_assets
        except Exception as e:
            self.logger.error(f"Failed to load mock printing assets: {e}")
            return []
    
    def get_organizations(self) -> List[Dict]:
        """
        Get all organizations from IT Glue.
        
        Returns:
            List of organization data
        """
        self.logger.info("Fetching organizations from IT Glue...")
        
        if self.use_mock_data:
            return self._load_mock_organizations()
        
        # Set up filter parameters
        params = {
            "filter[name]": "",  # Empty filter to get all organizations
            "sort": "name"       # Sort by name
        }
        
        organizations = self._paginate_results("organizations", params)
        
        self.logger.info(f"Retrieved {len(organizations)} organizations from IT Glue")
        return organizations
    
    def get_organization_by_id(self, org_id: str) -> Optional[Dict]:
        """
        Get a specific organization by ID.
        
        Args:
            org_id: Organization ID
            
        Returns:
            Organization data or None if not found
        """
        if self.use_mock_data:
            organizations = self._load_mock_organizations()
            for org in organizations:
                if org.get("id") == org_id:
                    return org
            return None
        
        try:
            # Make API request to get organization by ID
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/vnd.api+json",
                "x-api-version": "2"
            }
            
            url = f"{self.api_url}/organizations/{org_id}"
            
            import requests
            response = requests.get(
                url=url,
                headers=headers,
                timeout=self.timeout
            )
            
            # Raise for errors
            response.raise_for_status()
            
            # Log the response for debugging
            self.logger.debug(f"IT Glue API response for org ID {org_id}: {response.text[:200]}...")
            
            # Return the data
            return response.json().get("data")
            
        except Exception as e:
            if hasattr(e, 'response') and getattr(e.response, 'status_code', None) == 404:
                self.logger.warning(f"Organization not found: {org_id}")
                return None
            self.logger.error(f"Failed to get organization by ID {org_id}: {e}")
            raise
    
    def get_organization_by_name(self, name: str) -> Optional[Dict]:
        """
        Get a specific organization by name.
        
        Args:
            name: Organization name
            
        Returns:
            Organization data or None if not found
        """
        if self.use_mock_data:
            organizations = self._load_mock_organizations()
            for org in organizations:
                if org.get("attributes", {}).get("name") == name:
                    return org
            return None
        
        params = {
            "filter[name]": name,
            "page[size]": 1
        }
        
        response = self._make_request("organizations", params=params)
        data = response.get("data", [])
        
        if data:
            return data[0]
        return None
    
    def get_flexible_assets(self, org_id: str, asset_type_id: Optional[str] = None) -> List[Dict]:
        """
        Get flexible assets for an organization.
        
        Args:
            org_id: Organization ID
            asset_type_id: Optional flexible asset type ID to filter by
            
        Returns:
            List of flexible asset data
        """
        if self.use_mock_data:
            # For the demo, we'll only return site summaries as flexible assets
            site_summaries = self._load_mock_site_summaries()
            return [s for s in site_summaries if s.get("attributes", {}).get("organization-id") == org_id]
        
        params = {
            "filter[organization_id]": org_id
        }
        
        if asset_type_id:
            params["filter[flexible_asset_type_id]"] = asset_type_id
        
        return self._paginate_results("flexible_assets", params)
    
    def get_flexible_asset_types(self) -> List[Dict]:
        """
        Get all flexible asset types.
        
        Returns:
            List of flexible asset type data
        """
        if self.use_mock_data:
            # Return a mock site summary asset type
            return [{
                "id": "site_summary_type",
                "type": "flexible-asset-types",
                "attributes": {
                    "name": "Site Summary",
                    "description": "Site Summary flexible asset type",
                    "icon": "building",
                    "enabled": True
                }
            }]
        
        return self._paginate_results("flexible_asset_types")
    
    def get_site_summaries(self, org_id: Optional[str] = None) -> List[Dict]:
        """
        Get Site Summary flexible assets.
        
        Args:
            org_id: Optional organization ID to filter by
            
        Returns:
            List of Site Summary flexible asset data
        """
        if self.use_mock_data:
            site_summaries = self._load_mock_site_summaries()
            if org_id:
                return [s for s in site_summaries if s.get("attributes", {}).get("organization-id") == org_id]
            return site_summaries
        
        # First, find the Site Summary flexible asset type
        asset_types = self.get_flexible_asset_types()
        site_summary_type = None
        
        for asset_type in asset_types:
            name = asset_type.get("attributes", {}).get("name", "")
            if "site summary" in name.lower():
                site_summary_type = asset_type.get("id")
                break
        
        if not site_summary_type:
            self.logger.warning("Site Summary flexible asset type not found")
            return []
        
        # Get Site Summary assets
        if org_id:
            return self.get_flexible_assets(org_id, site_summary_type)
        
        # Get for all organizations
        all_site_summaries = []
        organizations = self.get_organizations()
        
        for org in organizations:
            org_id = org.get("id")
            org_name = org.get("attributes", {}).get("name", "Unknown")
            
            self.logger.debug(f"Fetching Site Summaries for {org_name} (ID: {org_id})")
            site_summaries = self.get_flexible_assets(org_id, site_summary_type)
            all_site_summaries.extend(site_summaries)
        
        return all_site_summaries
    
    def test_connection(self) -> bool:
        """
        Test the connection to the IT Glue API.
        
        Returns:
            True if connection is successful, False otherwise
        """
        if self.use_mock_data:
            # Always return success when using mock data
            return True
        
        try:
            response = self._make_request("organizations", params={"page[size]": 1})
            return "data" in response
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False