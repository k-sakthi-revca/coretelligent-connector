"""
Field mapper for the migration demo.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

from config import config


class FieldMapper:
    """Maps IT Glue fields to ServiceNow fields."""
    
    def __init__(self):
        """Initialize field mapper."""
        self.logger = logging.getLogger(__name__)
        self.field_mappings = config.get_field_mappings()
        
        self.logger.info(f"Field Mapper initialized with {len(self.field_mappings)} field mappings")
    
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
        
        for itglue_field, servicenow_field in self.field_mappings.items():
            description = self._get_field_description(itglue_field, servicenow_field)
            mapping_details[f"{itglue_field} -> {servicenow_field}"] = description
        
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