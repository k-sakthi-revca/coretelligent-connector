"""
ITGlue Connector - Main module for connecting to ITGlue API
"""
import os
import requests
import json
import logging
from typing import Dict, List, Any, Optional, Union
from dotenv import load_dotenv

load_dotenv()
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('itglue_connector')

class ITGlueConnector:
    """
    Main connector class for ITGlue API
    """
    BASE_URL = "https://api.itglue.com"
    API_VERSION = "2"
    
    def __init__(self, api_key: str):
        """
        Initialize the ITGlue connector with API key
        
        Args:
            api_key: ITGlue API key
        """
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'x-api-key': api_key,
            'Content-Type': 'application/vnd.api+json',
            'x-api-version': self.API_VERSION
        })
        logger.info("ITGlue connector initialized")
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        Make a GET request to the ITGlue API
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
            
        Returns:
            API response as dictionary
        """
        url = "{}/{}".format(self.BASE_URL, endpoint)
        logger.info("Making GET request to {}".format(url))
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error("Error making request to {}: {}".format(url, str(e)))
            if hasattr(e.response, 'text'):
                logger.error("Response: {}".format(e.response.text))
            raise
    
    def get_all_pages(self, endpoint: str, params: Optional[Dict] = None) -> List[Dict]:
        """
        Get all pages of results for a paginated endpoint
        
        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters
            
        Returns:
            List of all items across all pages
        """
        if params is None:
            params = {}
        
        all_items = []
        page = 1
        more_pages = True
        
        while more_pages:
            page_params = {**params, 'page[number]': page}
            response = self.get(endpoint, page_params)
            
            if 'data' in response:
                all_items.extend(response['data'])
            
            # Check if there are more pages
            if ('links' in response and 
                'next' in response['links'] and 
                response['links']['next'] is not None):
                page += 1
            else:
                more_pages = False
        
        return all_items
    
    def get_flexible_assets(self, asset_type_id: Optional[int] = None) -> List[Dict]:
        """
        Get flexible assets, optionally filtered by asset type ID
        
        Args:
            asset_type_id: Optional filter for specific asset type
            
        Returns:
            List of flexible assets
        """
        params = {}
        if asset_type_id:
            params['filter[flexible-asset-type-id]'] = asset_type_id
        
        return self.get_all_pages('flexible_assets', params)
    
    def get_flexible_asset_types(self) -> List[Dict]:
        """
        Get all flexible asset types
        
        Returns:
            List of flexible asset types
        """
        return self.get_all_pages('flexible_asset_types')
    
    def get_configuration_types(self) -> List[Dict]:
        """
        Get all configuration types
        
        Returns:
            List of configuration types
        """
        return self.get_all_pages('configuration_types')
    
    def get_configurations(self, config_type_id: Optional[int] = None) -> List[Dict]:
        """
        Get configurations, optionally filtered by configuration type ID
        
        Args:
            config_type_id: Optional filter for specific configuration type
            
        Returns:
            List of configurations
        """
        params = {}
        if config_type_id:
            params['filter[configuration_type_id]'] = config_type_id
        
        return self.get_all_pages('configurations', params)
    
    def get_organizations(self) -> List[Dict]:
        """
        Get all organizations (companies)
        
        Returns:
            List of organizations
        """
        return self.get_all_pages('organizations')
    
    def get_domains(self) -> List[Dict]:
        """
        Get all domains
        
        Returns:
            List of domains
        """
        return self.get_all_pages('domains')
    
    
    
    def get_attachments(self, resource_type: str, resource_id: int) -> List[Dict]:
        """
        Get attachments for a specific resource
        
        Args:
            resource_type: Type of resource (e.g., 'flexible_assets', 'configurations')
            resource_id: ID of the resource
            
        Returns:
            List of attachments
        """
        endpoint = "{}/{}".format(resource_type, resource_id)
        params = {'include': 'attachments'}
        
        response = self.get(endpoint, params)
        
        # Extract attachments from included data
        attachments = []
        if 'included' in response:
            attachments = [item for item in response['included'] 
                          if item['type'] == 'attachments']
        
        return attachments

if __name__ == "__main__":
    # Example usage
    API_KEY = os.getenv("API_KEY")
    connector = ITGlueConnector(API_KEY)
    
    # Example: Get all organizations
    # organizations = connector.get_organizations()
    # print("Found {} organizations".format(len(organizations)))