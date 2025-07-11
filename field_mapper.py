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
        
        self.logger.info(f"Field Mapper initialized with {len(self.field_mappings)} field mappings and {len(self.email_field_mappings)} email field mappings")
    
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