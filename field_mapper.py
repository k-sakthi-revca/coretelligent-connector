"""
Field mapper for the migration demo.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from config import config


class FieldMapper:
    """Maps IT Glue fields to ServiceNow fields."""
    
    def __init__(self):
        """Initialize field mapper."""
        self.logger = logging.getLogger(__name__)
        self.field_mappings = config.get_field_mappings()
        self.email_field_mappings = config.get("email_field_mappings", {})
        self.lob_application_field_mappings = config.get("lob_application_field_mappings", {})
        
        self.logger.info(f"Field Mapper initialized with {len(self.field_mappings)} field mappings, {len(self.email_field_mappings)} email field mappings, and {len(self.lob_application_field_mappings)} LoB application field mappings")
    
    def map_organization(self, itglue_org: Dict[str, Any], match_result: Any = None) -> Dict[str, Any]:
        """
        Map IT Glue organization to ServiceNow company.
        
        Args:
            itglue_org: IT Glue organization data
            match_result: Optional match result for additional context
            
        Returns:
            ServiceNow company data
        """
        attributes = itglue_org.get("attributes", {})
        
        # Initialize ServiceNow company data
        servicenow_data = {
            "sys_class_name": "core_company",
            "sys_created_by": "itglue_migration",
            "sys_updated_by": "itglue_migration"
        }
        
        # If we have a match, use the existing sys_id
        if match_result and match_result.servicenow_id:
            servicenow_data["sys_id"] = match_result.servicenow_id
        
        # Add CoreID if available
        if match_result and match_result.coreid:
            servicenow_data["u_core_id"] = match_result.coreid
        
        # Map fields according to the defined mappings
        for itglue_field, servicenow_field in self.field_mappings.items():
            if itglue_field in attributes:
                value = attributes[itglue_field]
                
                # Handle date fields
                if itglue_field in ["created-at", "updated-at"] and value:
                    value = self._format_date(value)
                
                if value is not None:
                    servicenow_data[servicenow_field] = value
        
        # Extract additional information from quick notes if available
        quick_notes = attributes.get("quick-notes")
        if quick_notes:
            contact_info = self._extract_contact_info_from_quick_notes(quick_notes)
            servicenow_data.update(contact_info)
            
            # Add the full quick notes to the notes field
            if "notes" in servicenow_data:
                servicenow_data["notes"] += "\n\nQuick Notes:\n" + quick_notes
            else:
                servicenow_data["notes"] = "Quick Notes:\n" + quick_notes
        
        # Add alert as a note if available
        alert = attributes.get("alert")
        if alert:
            if "notes" in servicenow_data:
                servicenow_data["notes"] += "\n\nAlert:\n" + alert
            else:
                servicenow_data["notes"] = "Alert:\n" + alert
        
        # Handle relationships
        relationships = itglue_org.get("relationships", {})
        
        # RMM companies relationship
        rmm_companies = relationships.get("rmm-companies", {}).get("data", [])
        if rmm_companies:
            rmm_ids = [company.get("id") for company in rmm_companies]
            servicenow_data["u_rmm_company_ids"] = ", ".join(rmm_ids)
            
            # Add a note about RMM companies
            rmm_note = f"RMM Companies: {len(rmm_companies)} linked companies"
            if "notes" in servicenow_data:
                servicenow_data["notes"] += "\n\n" + rmm_note
            else:
                servicenow_data["notes"] = rmm_note
        
        return servicenow_data
    
    def map_email(self, itglue_email: Dict[str, Any], match_result: Any = None) -> Dict[str, Any]:
        """
        Map IT Glue email asset to ServiceNow email service.
        
        Args:
            itglue_email: IT Glue email asset data
            match_result: Optional match result for additional context
            
        Returns:
            ServiceNow email service data
        """
        attributes = itglue_email.get("attributes", {})
        traits = attributes.get("traits", {})
        
        # Initialize ServiceNow email service data
        servicenow_data = {
            "sys_class_name": "cmdb_ci_service_email",
            "sys_created_by": "itglue_migration",
            "sys_updated_by": "itglue_migration"
        }
        
        # If we have a match, use the existing sys_id
        if match_result and match_result.servicenow_id:
            servicenow_data["sys_id"] = match_result.servicenow_id
        
        # Map basic fields
        servicenow_data["name"] = attributes.get("name", "Unknown Email Service")
        servicenow_data["short_description"] = f"{attributes.get('name', 'Email')} - {traits.get('type', 'Unknown Type')}"
        
        # Map organization
        org_id = attributes.get("organization-id")
        org_name = attributes.get("organization-name", "Unknown Organization")
        if org_id:
            servicenow_data["company"] = org_id
            servicenow_data["u_organization_name"] = org_name
        
        # Map email type
        email_type = traits.get("type")
        if email_type:
            servicenow_data["service_classification"] = email_type
        
        # Map hosting location
        hosting_location = traits.get("hosting-location")
        if hosting_location:
            servicenow_data["u_hosting_location"] = hosting_location
        
        # Map URLs
        webmail_url = traits.get("webmail-url")
        if webmail_url:
            servicenow_data["u_webmail_url"] = webmail_url
        
        admin_url = traits.get("administrator-url")
        if admin_url:
            servicenow_data["u_admin_url"] = admin_url
        
        # Map security settings
        spf_enabled = traits.get("spf-enabled")
        if spf_enabled is not None:
            servicenow_data["u_spf_enabled"] = spf_enabled
        
        dkim_enabled = traits.get("dkim-enabled")
        if dkim_enabled is not None:
            servicenow_data["u_dkim_enabled"] = dkim_enabled
        
        dmarc_enabled = traits.get("dmarc-enabled")
        if dmarc_enabled is not None:
            servicenow_data["u_dmarc_enabled"] = dmarc_enabled
        
        # Map notes
        notes = traits.get("notes")
        if notes:
            servicenow_data["comments"] = notes
        
        # Map domains
        domains = self._extract_domains(traits.get("domain-s", {}))
        if domains:
            servicenow_data["u_domains"] = ", ".join(domains)
        
        # Map email servers
        email_servers = self._extract_email_servers(traits.get("email-server-s", {}))
        if email_servers:
            servicenow_data["u_email_servers"] = ", ".join(email_servers)
        
        # Map spam filtering
        spam_filtering = self._extract_spam_filtering(traits.get("spam-filtering", {}))
        if spam_filtering:
            servicenow_data["u_spam_filtering"] = spam_filtering
        
        # Map additional fields according to the defined mappings
        for itglue_field, servicenow_field in self.email_field_mappings.items():
            if itglue_field in traits:
                value = traits[itglue_field]
                
                if value is not None:
                    servicenow_data[servicenow_field] = value
        
        # Add creation and update timestamps
        created_at = attributes.get("created-at")
        if created_at:
            servicenow_data["sys_created_on"] = self._format_date(created_at)
        
        updated_at = attributes.get("updated-at")
        if updated_at:
            servicenow_data["sys_updated_on"] = self._format_date(updated_at)
        
        # Set operational status to active by default
        servicenow_data["operational_status"] = "1"  # 1 = Operational
        
        # Set service status based on archived flag
        if attributes.get("archived", False):
            servicenow_data["install_status"] = "7"  # 7 = Retired
        else:
            servicenow_data["install_status"] = "1"  # 1 = Installed
        
        return servicenow_data
    
    def map_lob_application(self, itglue_application: Dict[str, Any], match_result: Any = None) -> Dict[str, Any]:
        """
        Map IT Glue LoB application asset to ServiceNow application CI.
        
        Args:
            itglue_application: IT Glue LoB application asset data
            match_result: Optional match result for additional context
            
        Returns:
            ServiceNow application CI data
        """
        attributes = itglue_application.get("attributes", {})
        traits = attributes.get("traits", {})
        
        # Initialize ServiceNow application CI data
        servicenow_data = {
            "sys_class_name": "cmdb_ci_appl",
            "sys_created_by": "itglue_migration",
            "sys_updated_by": "itglue_migration"
        }
        
        # If we have a match, use the existing sys_id
        if match_result and match_result.servicenow_id:
            servicenow_data["sys_id"] = match_result.servicenow_id
        
        # Map basic fields
        servicenow_data["name"] = attributes.get("name", "Unknown Application")
        
        # Map organization
        org_id = attributes.get("organization-id")
        org_name = attributes.get("organization-name", "Unknown Organization")
        if org_id:
            servicenow_data["company"] = org_id
            servicenow_data["u_organization_name"] = org_name
        
        # Map version
        version = traits.get("version")
        if version:
            servicenow_data["version"] = version
        
        # Map category and subcategory
        category = traits.get("category")
        if category:
            servicenow_data["category"] = category
        
        # Map importance to business criticality
        importance = traits.get("importance")
        if importance:
            # Map importance to operational status
            importance_map = {
                "Critical": "1",  # 1 = Operational/High
                "High": "1",      # 1 = Operational/High
                "Medium": "2",    # 2 = Non-operational/Medium
                "Low": "3"        # 3 = Retired/Low
            }
            servicenow_data["operational_status"] = importance_map.get(importance, "1")
            
            # Add importance to short description
            servicenow_data["short_description"] = f"{attributes.get('name', 'Application')} - {importance} Importance"
        else:
            servicenow_data["short_description"] = f"{attributes.get('name', 'Application')}"
        
        # Map business impact
        business_impact = traits.get("business-impact")
        if business_impact:
            if "short_description" in servicenow_data:
                servicenow_data["short_description"] += f" - {business_impact}"
            else:
                servicenow_data["short_description"] = business_impact
        
        # Map application champion to owned by
        application_champion = self._extract_application_champion(traits.get("application-champion", {}))
        if application_champion:
            servicenow_data["owned_by"] = application_champion
        
        # Map application manager
        application_manager = traits.get("application-manager")
        if application_manager:
            servicenow_data["managed_by"] = application_manager
        
        # Map hosting location
        hosting_location = traits.get("hosting-location")
        if hosting_location:
            servicenow_data["environment"] = hosting_location
        
        # Map application URL
        application_url = traits.get("application-url")
        if application_url:
            servicenow_data["u_application_url"] = application_url
        
        # Map vendor
        vendor = self._extract_vendor(traits.get("vendor", {}))
        if vendor:
            servicenow_data["vendor"] = vendor
            servicenow_data["manufacturer"] = vendor
        
        # Map notes and install instructions
        notes = traits.get("notes", "")
        install_instructions = traits.get("install-instructions", "")
        
        comments = ""
        if notes:
            comments += f"Notes:\n{notes}\n\n"
        
        if install_instructions:
            comments += f"Install Instructions:\n{install_instructions}\n\n"
        
        if comments:
            servicenow_data["comments"] = comments
        
        # Map application servers
        application_servers = self._extract_application_servers(traits.get("application-server-s", {}))
        if application_servers:
            servicenow_data["u_application_servers"] = ", ".join(application_servers)
        
        # Map additional fields according to the defined mappings
        for itglue_field, servicenow_field in self.lob_application_field_mappings.items():
            if itglue_field in traits:
                value = traits[itglue_field]
                
                if value is not None:
                    servicenow_data[servicenow_field] = value
        
        # Add creation and update timestamps
        created_at = attributes.get("created-at")
        if created_at:
            servicenow_data["sys_created_on"] = self._format_date(created_at)
            servicenow_data["install_date"] = self._format_date(created_at)
        
        updated_at = attributes.get("updated-at")
        if updated_at:
            servicenow_data["sys_updated_on"] = self._format_date(updated_at)
        
        # Set install status based on archived flag
        if attributes.get("archived", False):
            servicenow_data["install_status"] = "7"  # 7 = Retired
        else:
            servicenow_data["install_status"] = "1"  # 1 = Installed
        
        return servicenow_data
    
    def _extract_domains(self, domain_data: Dict[str, Any]) -> List[str]:
        """
        Extract domain names from IT Glue domain tag data.
        
        Args:
            domain_data: IT Glue domain tag data
            
        Returns:
            List of domain names
        """
        domains = []
        
        if not domain_data:
            return domains
        
        values = domain_data.get("values", [])
        for value in values:
            if isinstance(value, dict) and "name" in value:
                domains.append(value["name"])
        
        return domains
    
    def _extract_email_servers(self, server_data: Dict[str, Any]) -> List[str]:
        """
        Extract email server names from IT Glue server tag data.
        
        Args:
            server_data: IT Glue server tag data
            
        Returns:
            List of server names
        """
        servers = []
        
        if not server_data:
            return servers
        
        values = server_data.get("values", [])
        for value in values:
            if isinstance(value, dict) and "name" in value:
                servers.append(value["name"])
        
        return servers
    
    def _extract_application_servers(self, server_data: Dict[str, Any]) -> List[str]:
        """
        Extract application server names from IT Glue server tag data.
        
        Args:
            server_data: IT Glue server tag data
            
        Returns:
            List of server names
        """
        servers = []
        
        if not server_data:
            return servers
        
        values = server_data.get("values", [])
        for value in values:
            if isinstance(value, dict) and "name" in value:
                servers.append(value["name"])
        
        return servers
    
    def _extract_application_champion(self, champion_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract application champion from IT Glue contact tag data.
        
        Args:
            champion_data: IT Glue contact tag data
            
        Returns:
            Contact ID or None
        """
        if not champion_data:
            return None
        
        values = champion_data.get("values", [])
        if values and isinstance(values[0], dict) and "id" in values[0]:
            return values[0]["id"]
        
        return None
    
    def _extract_vendor(self, vendor_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract vendor from IT Glue vendor tag data.
        
        Args:
            vendor_data: IT Glue vendor tag data
            
        Returns:
            Vendor ID or None
        """
        if not vendor_data:
            return None
        
        values = vendor_data.get("values", [])
        if values and isinstance(values[0], dict) and "id" in values[0]:
            return values[0]["id"]
        
        return None
    
    def _extract_spam_filtering(self, spam_data: Dict[str, Any]) -> str:
        """
        Extract spam filtering vendor from IT Glue spam filtering tag data.
        
        Args:
            spam_data: IT Glue spam filtering tag data
            
        Returns:
            Spam filtering vendor name or empty string
        """
        if not spam_data:
            return ""
        
        values = spam_data.get("values", [])
        if values and isinstance(values[0], dict) and "name" in values[0]:
            return values[0]["name"]
        
        return ""
    
    def _format_date(self, date_str: str) -> Optional[str]:
        """
        Format date string from IT Glue to ServiceNow format.
        
        Args:
            date_str: ISO format date string
            
        Returns:
            ServiceNow format date string or None if invalid
        """
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, AttributeError):
            return None
    
    def _extract_contact_info_from_quick_notes(self, quick_notes: str) -> Dict[str, str]:
        """
        Extract contact information from quick notes field if available.
        
        Args:
            quick_notes: Quick notes HTML content
            
        Returns:
            Dictionary of extracted contact information
        """
        contact_info = {}
        
        if not quick_notes:
            return contact_info
        
        # This is a simplified extraction - in a real implementation,
        # you would use HTML parsing and more sophisticated pattern matching
        
        # Look for common patterns in the quick notes
        if "Email" in quick_notes:
            contact_info["email_domain"] = "extracted_from_notes"
        
        if "Phone" in quick_notes:
            contact_info["phone"] = "extracted_from_notes"
        
        if "Website" in quick_notes or "http" in quick_notes:
            contact_info["website"] = "extracted_from_notes"
        
        if "Address" in quick_notes:
            contact_info["street"] = "extracted_from_notes"
            contact_info["city"] = "extracted_from_notes"
            contact_info["state"] = "extracted_from_notes"
            contact_info["country"] = "extracted_from_notes"
            contact_info["zip"] = "extracted_from_notes"
        
        return contact_info
    
    def get_field_mapping_details(self) -> Dict[str, str]:
        """
        Get field mapping details for reporting.
        
        Returns:
            Dictionary of field mappings with descriptions
        """
        mapping_details = {}
        
        # Organization field mappings
        for itglue_field, servicenow_field in self.field_mappings.items():
            description = self._get_field_description(itglue_field, servicenow_field)
            mapping_details[f"org:{itglue_field} -> {servicenow_field}"] = description
        
        # Email field mappings
        for itglue_field, servicenow_field in self.email_field_mappings.items():
            description = self._get_email_field_description(itglue_field, servicenow_field)
            mapping_details[f"email:{itglue_field} -> {servicenow_field}"] = description
        
        # Add built-in email mappings
        email_built_in_mappings = {
            "name -> name": "Email service name",
            "type -> service_classification": "Email service type",
            "hosting-location -> u_hosting_location": "Where email is hosted",
            "webmail-url -> u_webmail_url": "URL for webmail access",
            "administrator-url -> u_admin_url": "URL for admin portal",
            "spf-enabled -> u_spf_enabled": "SPF enabled flag",
            "dkim-enabled -> u_dkim_enabled": "DKIM enabled flag",
            "dmarc-enabled -> u_dmarc_enabled": "DMARC enabled flag",
            "notes -> comments": "Additional notes",
            "domain-s -> u_domains": "Associated domains",
            "email-server-s -> u_email_servers": "Email servers",
            "spam-filtering -> u_spam_filtering": "Spam filtering vendor"
        }
        
        for mapping, description in email_built_in_mappings.items():
            mapping_details[f"email:{mapping}"] = description
        
        # LoB application field mappings
        for itglue_field, servicenow_field in self.lob_application_field_mappings.items():
            description = self._get_lob_application_field_description(itglue_field, servicenow_field)
            mapping_details[f"lob_application:{itglue_field} -> {servicenow_field}"] = description
        
        # Add built-in LoB application mappings
        lob_application_built_in_mappings = {
            "name -> name": "Application name",
            "version -> version": "Application version",
            "category -> category": "Application category",
            "importance -> operational_status": "Application importance/criticality",
            "business-impact -> short_description": "Business impact description",
            "application-champion -> owned_by": "Application owner/champion",
            "application-manager -> managed_by": "Application manager",
            "hosting-location -> environment": "Where application is hosted",
            "application-url -> u_application_url": "URL for application access",
            "vendor -> vendor": "Application vendor",
            "notes -> comments": "Additional notes",
            "install-instructions -> comments": "Installation instructions",
            "application-server-s -> u_application_servers": "Application servers"
        }
        
        for mapping, description in lob_application_built_in_mappings.items():
            mapping_details[f"lob_application:{mapping}"] = description
        
        return mapping_details
    
    def _get_field_description(self, itglue_field: str, servicenow_field: str) -> str:
        """
        Get description for a field mapping.
        
        Args:
            itglue_field: IT Glue field name
            servicenow_field: ServiceNow field name
            
        Returns:
            Description of the field mapping
        """
        # Basic descriptions for common fields
        descriptions = {
            "name": "Organization name",
            "description": "Organization description",
            "short-name": "Short name/abbreviation",
            "organization-status-name": "Active/Inactive status",
            "organization-type-name": "Organization type",
            "created-at": "Creation date",
            "updated-at": "Last update date"
        }
        
        return descriptions.get(itglue_field, "Custom field mapping")
    
    def _get_email_field_description(self, itglue_field: str, servicenow_field: str) -> str:
        """
        Get description for an email field mapping.
        
        Args:
            itglue_field: IT Glue field name
            servicenow_field: ServiceNow field name
            
        Returns:
            Description of the field mapping
        """
        # Basic descriptions for common email fields
        descriptions = {
            "type": "Email service type",
            "hosting-location": "Where email is hosted",
            "webmail-url": "URL for webmail access",
            "administrator-url": "URL for admin portal",
            "spf-enabled": "SPF enabled flag",
            "dkim-enabled": "DKIM enabled flag",
            "dmarc-enabled": "DMARC enabled flag",
            "notes": "Additional notes",
            "domain-s": "Associated domains",
            "email-server-s": "Email servers",
            "spam-filtering": "Spam filtering vendor"
        }
        
        return descriptions.get(itglue_field, "Custom email field mapping")
    
    def map_printing(self, itglue_printing: Dict[str, Any], match_result: Any = None) -> Dict[str, Any]:
        """
        Map IT Glue printing asset to ServiceNow printer CI.
        
        Args:
            itglue_printing: IT Glue printing asset data
            match_result: Optional match result for additional context
            
        Returns:
            ServiceNow printer CI data
        """
        attributes = itglue_printing.get("attributes", {})
        traits = attributes.get("traits", {})
        
        # Initialize ServiceNow printer CI data
        servicenow_data = {
            "sys_class_name": "cmdb_ci_printer",
            "sys_created_by": "itglue_migration",
            "sys_updated_by": "itglue_migration"
        }
        
        # If we have a match, use the existing sys_id
        if match_result and match_result.servicenow_id:
            servicenow_data["sys_id"] = match_result.servicenow_id
        
        # Map basic fields
        servicenow_data["name"] = match_result.itglue_name if match_result else attributes.get("name", "Unknown Printer")
        
        # Map organization
        org_id = attributes.get("organization-id")
        org_name = attributes.get("organization-name", "Unknown Organization")
        if org_id:
            servicenow_data["company"] = org_id
            servicenow_data["u_organization_name"] = org_name
        
        # Map title to short description
        title = traits.get("title")
        if title:
            servicenow_data["short_description"] = title
        
        # Map location
        location_data = traits.get("location", {})
        if location_data and isinstance(location_data, dict) and "values" in location_data:
            location_values = location_data.get("values", [])
            if location_values and isinstance(location_values[0], dict):
                location = location_values[0].get("name")
                if location:
                    servicenow_data["location"] = location
        
        # Map IP address
        ip_address = traits.get("ip-address") or traits.get("ip-address-dns-path")
        if ip_address:
            servicenow_data["ip_address"] = ip_address
        
        # Map deployment to comments
        deployment = traits.get("deployment")
        if deployment:
            servicenow_data["comments"] = f"Deployment Method: {deployment}"
        
        # Map notes
        notes = traits.get("notes")
        if notes:
            if "comments" in servicenow_data:
                servicenow_data["comments"] += f"\n\nNotes:\n{notes}"
            else:
                servicenow_data["comments"] = f"Notes:\n{notes}"
        
        # Map support information
        support_info = traits.get("support-information")
        if support_info:
            if "comments" in servicenow_data:
                servicenow_data["comments"] += f"\n\nSupport Information:\n{support_info}"
            else:
                servicenow_data["comments"] = f"Support Information:\n{support_info}"
        
        # Map drivers path
        drivers_path = traits.get("drivers-path")
        if drivers_path:
            servicenow_data["u_drivers_path"] = drivers_path
            
            # Add to comments as well
            if "comments" in servicenow_data:
                servicenow_data["comments"] += f"\n\nDrivers Path: {drivers_path}"
            else:
                servicenow_data["comments"] = f"Drivers Path: {drivers_path}"
        
        # Map vendor
        vendor_data = traits.get("vendor", {})
        if vendor_data and isinstance(vendor_data, dict) and "values" in vendor_data:
            vendor_values = vendor_data.get("values", [])
            if vendor_values and isinstance(vendor_values[0], dict):
                vendor = vendor_values[0].get("name")
                if vendor:
                    servicenow_data["vendor"] = vendor
                    servicenow_data["manufacturer"] = vendor
        
        # Map print servers
        print_servers_data = traits.get("print-server-s", {})
        if print_servers_data and isinstance(print_servers_data, dict) and "values" in print_servers_data:
            print_server_values = print_servers_data.get("values", [])
            if print_server_values:
                print_servers = []
                for server in print_server_values:
                    if isinstance(server, dict) and "name" in server:
                        print_servers.append(server["name"])
                
                if print_servers:
                    servicenow_data["u_print_servers"] = ", ".join(print_servers)
        
        # Map published to AD
        published_to_ad = traits.get("published-to-ad")
        if published_to_ad is not None:
            servicenow_data["u_published_to_ad"] = "true" if published_to_ad else "false"
        
        # Map CoreSecret URL
        coresecret_url = traits.get("coresecret-url")
        if coresecret_url:
            servicenow_data["u_coresecret_url"] = coresecret_url
        
        # Add creation and update timestamps
        created_at = attributes.get("created-at")
        if created_at:
            servicenow_data["sys_created_on"] = self._format_date(created_at)
            servicenow_data["install_date"] = self._format_date(created_at)
        
        updated_at = attributes.get("updated-at")
        if updated_at:
            servicenow_data["sys_updated_on"] = self._format_date(updated_at)
        
        # Set operational status to active by default
        servicenow_data["operational_status"] = "1"  # 1 = Operational
        
        # Set install status based on archived flag
        if attributes.get("archived", False):
            servicenow_data["install_status"] = "7"  # 7 = Retired
        else:
            servicenow_data["install_status"] = "1"  # 1 = Installed
        
        # Set printer type if available from match result
        if match_result and match_result.printer_type:
            servicenow_data["u_printer_type"] = match_result.printer_type
        
        return servicenow_data
    
    def _get_lob_application_field_description(self, itglue_field: str, servicenow_field: str) -> str:
        """
        Get description for a LoB application field mapping.
        
        Args:
            itglue_field: IT Glue field name
            servicenow_field: ServiceNow field name
            
        Returns:
            Description of the field mapping
        """
        # Basic descriptions for common LoB application fields
        descriptions = {
            "name": "Application name",
            "version": "Application version",
            "category": "Application category",
            "importance": "Application importance/criticality",
            "business-impact": "Business impact description",
            "application-champion": "Application owner/champion",
            "application-manager": "Application manager",
            "hosting-location": "Where application is hosted",
            "application-url": "URL for application access",
            "vendor": "Application vendor",
            "notes": "Additional notes",
            "install-instructions": "Installation instructions",
            "application-server-s": "Application servers"
        }
        
        return descriptions.get(itglue_field, "Custom LoB application field mapping")