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
        self.mock_servers_file = config.get("servicenow.mock_servers_file", "mock_servicenow_servers.json")
        self.mock_email_services_file = "mock_servicenow_email_services.json"
        self.mock_applications_file = "mock_servicenow_applications.json"
        self.create_missing = config.get("servicenow.create_missing", True)
        self.logger = logging.getLogger(__name__)
        
        # Load or create mock data
        self.companies = self._load_mock_data()
        self.email_services = self._load_mock_email_services()
        self.applications = self._load_mock_applications()
        
        self.logger.info(f"Initialized ServiceNow mock client with {len(self.companies)} companies, {len(self.email_services)} email services, and {len(self.applications)} applications")
    
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
    
    def _load_mock_email_services(self) -> List[Dict]:
        """
        Load mock email services data from file or create default data.
        
        Returns:
            List of mock email service data
        """
        if os.path.exists(self.mock_email_services_file):
            try:
                with open(self.mock_email_services_file, 'r') as f:
                    data = json.load(f)
                self.logger.info(f"Loaded mock email services from {self.mock_email_services_file}")
                return data
            except Exception as e:
                self.logger.error(f"Error loading mock email services: {e}")
        
        # Create default mock email services
        self.logger.info(f"Creating default mock email services")
        mock_data = self._create_default_mock_email_services()
        
        # Save mock data
        try:
            with open(self.mock_email_services_file, 'w') as f:
                json.dump(mock_data, f, indent=2)
            self.logger.info(f"Saved mock email services to {self.mock_email_services_file}")
        except Exception as e:
            self.logger.error(f"Error saving mock email services: {e}")
        
        return mock_data
    
    def _load_mock_applications(self) -> List[Dict]:
        """
        Load mock applications data from file or create default data.
        
        Returns:
            List of mock application data
        """
        if os.path.exists(self.mock_applications_file):
            try:
                with open(self.mock_applications_file, 'r') as f:
                    data = json.load(f)
                self.logger.info(f"Loaded mock applications from {self.mock_applications_file}")
                return data
            except Exception as e:
                self.logger.error(f"Error loading mock applications: {e}")
        
        # Create default mock applications
        self.logger.info(f"Creating default mock applications")
        mock_data = self._create_default_mock_applications()
        
        # Save mock data
        try:
            with open(self.mock_applications_file, 'w') as f:
                json.dump(mock_data, f, indent=2)
            self.logger.info(f"Saved mock applications to {self.mock_applications_file}")
        except Exception as e:
            self.logger.error(f"Error saving mock applications: {e}")
        
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
    
    def _create_default_mock_email_services(self) -> List[Dict]:
        """
        Create default mock email service data.
        
        Returns:
            List of mock email service data
        """
        return [
            {
                "sys_id": "email_1001",
                "name": "Microsoft 365",
                "sys_class_name": "cmdb_ci_service_email",
                "company": "sn_1001",
                "service_classification": "Microsoft 365",
                "u_hosting_location": "Cloud",
                "u_webmail_url": "https://outlook.office.com",
                "u_admin_url": "https://admin.microsoft.com",
                "u_domains": "acme.com",
                "u_spf_enabled": "true",
                "u_dkim_enabled": "true",
                "u_dmarc_enabled": "true",
                "operational_status": "1",
                "install_status": "1",
                "comments": "Mock email service for demo purposes"
            },
            {
                "sys_id": "email_1002",
                "name": "Google Workspace",
                "sys_class_name": "cmdb_ci_service_email",
                "company": "sn_1002",
                "service_classification": "Google Apps",
                "u_hosting_location": "Cloud",
                "u_webmail_url": "https://mail.google.com",
                "u_admin_url": "https://admin.google.com",
                "u_domains": "globex.com",
                "u_spf_enabled": "true",
                "u_dkim_enabled": "true",
                "u_dmarc_enabled": "false",
                "operational_status": "1",
                "install_status": "1",
                "comments": "Mock email service for demo purposes"
            },
            {
                "sys_id": "email_1003",
                "name": "Exchange Server",
                "sys_class_name": "cmdb_ci_service_email",
                "company": "sn_1003",
                "service_classification": "Exchange 2019",
                "u_hosting_location": "On-Premises",
                "u_webmail_url": "https://mail.initech.com/owa",
                "u_admin_url": "https://mail.initech.com/ecp",
                "u_domains": "initech.com",
                "u_email_servers": "MAIL01, MAIL02",
                "u_spf_enabled": "true",
                "u_dkim_enabled": "false",
                "u_dmarc_enabled": "false",
                "operational_status": "1",
                "install_status": "1",
                "comments": "Mock email service for demo purposes"
            }
        ]
    
    def _create_default_mock_applications(self) -> List[Dict]:
        """
        Create default mock application data.
        
        Returns:
            List of mock application data
        """
        return [
            {
                "sys_id": "app_1001",
                "name": "Microsoft Office",
                "sys_class_name": "cmdb_ci_appl",
                "company": "sn_1001",
                "version": "2019",
                "category": "Productivity",
                "subcategory": "Office Suite",
                "operational_status": "1",
                "install_status": "1",
                "comments": "Mock application for demo purposes",
                "short_description": "Microsoft Office productivity suite",
                "vendor": "Microsoft",
                "manufacturer": "Microsoft",
                "environment": "On-Premises"
            },
            {
                "sys_id": "app_1002",
                "name": "QuickBooks",
                "sys_class_name": "cmdb_ci_appl",
                "company": "sn_1002",
                "version": "2022",
                "category": "Finance",
                "subcategory": "Accounting",
                "operational_status": "1",
                "install_status": "1",
                "comments": "Mock application for demo purposes",
                "short_description": "QuickBooks accounting software",
                "vendor": "Intuit",
                "manufacturer": "Intuit",
                "environment": "On-Premises"
            },
            {
                "sys_id": "app_1003",
                "name": "Salesforce",
                "sys_class_name": "cmdb_ci_appl",
                "company": "sn_1003",
                "version": "Enterprise",
                "category": "CRM",
                "subcategory": "Sales",
                "operational_status": "1",
                "install_status": "1",
                "comments": "Mock application for demo purposes",
                "short_description": "Salesforce CRM platform",
                "vendor": "Salesforce",
                "manufacturer": "Salesforce",
                "environment": "Cloud",
                "u_application_url": "https://login.salesforce.com"
            },
            {
                "sys_id": "app_1004",
                "name": "Adobe Creative Cloud",
                "sys_class_name": "cmdb_ci_appl",
                "company": "sn_1004",
                "version": "2023",
                "category": "Productivity",
                "subcategory": "Design",
                "operational_status": "1",
                "install_status": "1",
                "comments": "Mock application for demo purposes",
                "short_description": "Adobe Creative Cloud suite",
                "vendor": "Adobe",
                "manufacturer": "Adobe",
                "environment": "Cloud",
                "u_application_url": "https://account.adobe.com"
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
    
    def get_email_services(self) -> List[Dict]:
        """
        Get email services from ServiceNow.
        
        Returns:
            List of email service data
        """
        return self.email_services
    
    def get_applications(self) -> List[Dict]:
        """
        Get applications from ServiceNow.
        
        Returns:
            List of application data
        """
        return self.applications
    
    def create_email_service(self, email_service_data: Dict) -> Dict:
        """
        Create a new email service.
        
        Args:
            email_service_data: Email service data
            
        Returns:
            Created email service data
        """
        # Generate a new sys_id
        sys_id = f"email_{uuid.uuid4().hex[:8]}"
        
        # Create new email service
        new_email_service = {
            "sys_id": sys_id,
            **email_service_data
        }
        
        # Add to email services list
        self.email_services.append(new_email_service)
        
        # Save updated mock data
        try:
            with open(self.mock_email_services_file, 'w') as f:
                json.dump(self.email_services, f, indent=2)
            self.logger.info(f"Saved updated mock email services to {self.mock_email_services_file}")
        except Exception as e:
            self.logger.error(f"Error saving updated mock email services: {e}")
        
        return new_email_service
    
    def create_application(self, application_data: Dict) -> Dict:
        """
        Create a new application.
        
        Args:
            application_data: Application data
            
        Returns:
            Created application data
        """
        # Generate a new sys_id
        sys_id = f"app_{uuid.uuid4().hex[:8]}"
        
        # Create new application
        new_application = {
            "sys_id": sys_id,
            **application_data
        }
        
        # Add to applications list
        self.applications.append(new_application)
        
        # Save updated mock data
        try:
            with open(self.mock_applications_file, 'w') as f:
                json.dump(self.applications, f, indent=2)
            self.logger.info(f"Saved updated mock applications to {self.mock_applications_file}")
        except Exception as e:
            self.logger.error(f"Error saving updated mock applications: {e}")
        
        return new_application
    
    def update_email_service(self, sys_id: str, email_service_data: Dict) -> Optional[Dict]:
        """
        Update an existing email service.
        
        Args:
            sys_id: Email service sys_id
            email_service_data: Updated email service data
            
        Returns:
            Updated email service data or None if not found
        """
        for i, email_service in enumerate(self.email_services):
            if email_service.get("sys_id") == sys_id:
                # Update email service data
                updated_email_service = {
                    **email_service,
                    **email_service_data
                }
                self.email_services[i] = updated_email_service
                
                # Save updated mock data
                try:
                    with open(self.mock_email_services_file, 'w') as f:
                        json.dump(self.email_services, f, indent=2)
                    self.logger.info(f"Saved updated mock email services to {self.mock_email_services_file}")
                except Exception as e:
                    self.logger.error(f"Error saving updated mock email services: {e}")
                
                return updated_email_service
        
        return None
    
    def update_application(self, sys_id: str, application_data: Dict) -> Optional[Dict]:
        """
        Update an existing application.
        
        Args:
            sys_id: Application sys_id
            application_data: Updated application data
            
        Returns:
            Updated application data or None if not found
        """
        for i, application in enumerate(self.applications):
            if application.get("sys_id") == sys_id:
                # Update application data
                updated_application = {
                    **application,
                    **application_data
                }
                self.applications[i] = updated_application
                
                # Save updated mock data
                try:
                    with open(self.mock_applications_file, 'w') as f:
                        json.dump(self.applications, f, indent=2)
                    self.logger.info(f"Saved updated mock applications to {self.mock_applications_file}")
                except Exception as e:
                    self.logger.error(f"Error saving updated mock applications: {e}")
                
                return updated_application
        
        return None
    
    def test_connection(self) -> bool:
        """
        Test the connection to the mock ServiceNow API.
        
        Returns:
            Always returns True for the mock client
        """
        return True