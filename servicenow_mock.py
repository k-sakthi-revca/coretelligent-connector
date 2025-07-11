"""
Mock ServiceNow client for the migration demo.
"""

import json
import os
import logging
import uuid
from typing import Dict, List, Any, Optional
from config import config


class ServiceNowMock:
    """Mock client for simulating ServiceNow API."""
    
    def __init__(self):
        """Initialize the mock ServiceNow client."""
        self.mock_data_file = config.get("servicenow.mock_data_file", "mock_servicenow_companies.json")
        self.create_missing = config.get("servicenow.create_missing", True)
        self.logger = logging.getLogger(__name__)
        
        # Load or create mock data
        self.companies = self._load_mock_data()
        
        self.logger.info(f"Initialized ServiceNow mock client with {len(self.companies)} companies")
    
    def _load_mock_data(self) -> List[Dict]:
        """
        Load mock data from file or create default data.
        
        Returns:
            List of mock company data
        """
        if os.path.exists(self.mock_data_file):
            try:
                with open(self.mock_data_file, 'r') as f:
                    data = json.load(f)
                self.logger.info(f"Loaded mock data from {self.mock_data_file}")
                return data
            except Exception as e:
                self.logger.error(f"Error loading mock data: {e}")
        
        # Create default mock data
        self.logger.info(f"Creating default mock data")
        mock_data = self._create_default_mock_data()
        
        # Save mock data
        try:
            with open(self.mock_data_file, 'w') as f:
                json.dump(mock_data, f, indent=2)
            self.logger.info(f"Saved mock data to {self.mock_data_file}")
        except Exception as e:
            self.logger.error(f"Error saving mock data: {e}")
        
        return mock_data
    
    def _create_default_mock_data(self) -> List[Dict]:
        """
        Create default mock company data.
        
        Returns:
            List of mock company data
        """
        return [
            {
                "sys_id": "sn_1001",
                "name": "Acme Corporation",
                "u_core_id": "CORE001",
                "email_domain": "acme.com",
                "phone": "555-123-4567",
                "website": "https://www.acme.com",
                "street": "123 Main St",
                "city": "New York",
                "state": "NY",
                "country": "USA",
                "zip": "10001",
                "notes": "Mock company for demo purposes"
            },
            {
                "sys_id": "sn_1002",
                "name": "Globex Corporation",
                "u_core_id": "CORE002",
                "email_domain": "globex.com",
                "phone": "555-987-6543",
                "website": "https://www.globex.com",
                "street": "456 Tech Blvd",
                "city": "San Francisco",
                "state": "CA",
                "country": "USA",
                "zip": "94107",
                "notes": "Mock company for demo purposes"
            },
            {
                "sys_id": "sn_1003",
                "name": "Initech",
                "u_core_id": "CORE003",
                "email_domain": "initech.com",
                "phone": "555-555-5555",
                "website": "https://www.initech.com",
                "street": "789 Office Park",
                "city": "Austin",
                "state": "TX",
                "country": "USA",
                "zip": "78701",
                "notes": "Mock company for demo purposes"
            },
            {
                "sys_id": "sn_1004",
                "name": "Umbrella Corporation",
                "u_core_id": "CORE004",
                "email_domain": "umbrella.com",
                "phone": "555-666-7777",
                "website": "https://www.umbrella.com",
                "street": "101 Research Dr",
                "city": "Raccoon City",
                "state": "MI",
                "country": "USA",
                "zip": "48201",
                "notes": "Mock company for demo purposes"
            },
            {
                "sys_id": "sn_1005",
                "name": "Stark Industries",
                "u_core_id": "CORE005",
                "email_domain": "stark.com",
                "phone": "555-888-9999",
                "website": "https://www.stark.com",
                "street": "200 Park Avenue",
                "city": "New York",
                "state": "NY",
                "country": "USA",
                "zip": "10166",
                "notes": "Mock company for demo purposes"
            }
        ]
    
    def get_companies(self, name_filter: str = None) -> List[Dict]:
        """
        Get companies with optional name filter.
        
        Args:
            name_filter: Optional name filter
            
        Returns:
            List of matching companies
        """
        if not name_filter:
            return self.companies
        
        name_filter = name_filter.lower()
        return [
            company for company in self.companies
            if name_filter in company.get("name", "").lower()
        ]
    
    def get_company_by_name(self, name: str) -> Optional[Dict]:
        """
        Get a company by exact name.
        
        Args:
            name: Company name
            
        Returns:
            Company data or None if not found
        """
        for company in self.companies:
            if company.get("name", "").lower() == name.lower():
                return company
        return None
    
    def get_company_by_coreid(self, coreid: str) -> Optional[Dict]:
        """
        Get a company by CoreID.
        
        Args:
            coreid: CoreID
            
        Returns:
            Company data or None if not found
        """
        for company in self.companies:
            if company.get("u_core_id", "") == coreid:
                return company
        return None
    
    def create_company(self, company_data: Dict) -> Dict:
        """
        Create a new company.
        
        Args:
            company_data: Company data
            
        Returns:
            Created company data
        """
        # Generate a new sys_id
        sys_id = f"sn_{uuid.uuid4().hex[:8]}"
        
        # Create new company
        new_company = {
            "sys_id": sys_id,
            **company_data
        }
        
        # Add to companies list
        self.companies.append(new_company)
        
        # Save updated mock data
        try:
            with open(self.mock_data_file, 'w') as f:
                json.dump(self.companies, f, indent=2)
            self.logger.info(f"Saved updated mock data to {self.mock_data_file}")
        except Exception as e:
            self.logger.error(f"Error saving updated mock data: {e}")
        
        return new_company
    
    def update_company(self, sys_id: str, company_data: Dict) -> Optional[Dict]:
        """
        Update an existing company.
        
        Args:
            sys_id: Company sys_id
            company_data: Updated company data
            
        Returns:
            Updated company data or None if not found
        """
        for i, company in enumerate(self.companies):
            if company.get("sys_id") == sys_id:
                # Update company data
                updated_company = {
                    **company,
                    **company_data
                }
                self.companies[i] = updated_company
                
                # Save updated mock data
                try:
                    with open(self.mock_data_file, 'w') as f:
                        json.dump(self.companies, f, indent=2)
                    self.logger.info(f"Saved updated mock data to {self.mock_data_file}")
                except Exception as e:
                    self.logger.error(f"Error saving updated mock data: {e}")
                
                return updated_company
        
        return None
    
    def test_connection(self) -> bool:
        """
        Test the connection to the mock ServiceNow API.
        
        Returns:
            Always returns True for the mock client
        """
        return True