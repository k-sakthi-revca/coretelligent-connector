"""
Site Summary migrator for the migration demo.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from site_summary_matcher import SiteSummaryMatch
from config import config


@dataclass
class MigrationResult:
    """Result of a migration operation."""
    success: bool
    itglue_id: str
    itglue_name: str
    servicenow_id: Optional[str]
    servicenow_name: Optional[str]
    action: str  # 'created', 'updated', 'skipped', 'failed'
    message: str


class SiteSummaryMigrator:
    """Migrates IT Glue Site Summary assets to ServiceNow site CIs."""
    
    def __init__(self, dry_run: bool = False):
        """
        Initialize site summary migrator.
        
        Args:
            dry_run: If True, don't actually create/update records
        """
        self.logger = logging.getLogger(__name__)
        self.dry_run = dry_run
        self.field_mappings = self._load_field_mappings()
        
        self.logger.info(f"Site Summary Migrator initialized (dry_run={dry_run})")
    
    def migrate_site_summaries(self, 
                             itglue_sites: List[Dict], 
                             matches: List[SiteSummaryMatch],
                             servicenow_sites: List[Dict]) -> List[MigrationResult]:
        """
        Migrate IT Glue Site Summary assets to ServiceNow site CIs.
        
        Args:
            itglue_sites: List of IT Glue Site Summary data
            matches: List of match results
            servicenow_sites: List of ServiceNow site CI data
            
        Returns:
            List of migration results
        """
        self.logger.info(f"Migrating {len(itglue_sites)} IT Glue Site Summaries")
        
        # Create lookup dictionaries
        itglue_sites_by_id = {site.get("id"): site for site in itglue_sites}
        servicenow_sites_by_id = {site.get("sys_id"): site for site in servicenow_sites}
        matches_by_itglue_id = {match.itglue_id: match for match in matches}
        
        # Migrate each site summary
        results = []
        
        for site_id, site in itglue_sites_by_id.items():
            match = matches_by_itglue_id.get(site_id)
            
            if not match:
                self.logger.warning(f"No match found for site {site_id}")
                results.append(MigrationResult(
                    success=False,
                    itglue_id=site_id,
                    itglue_name=site.get("attributes", {}).get("name", "Unknown"),
                    servicenow_id=None,
                    servicenow_name=None,
                    action="skipped",
                    message="No match information available"
                ))
                continue
            
            # Determine action based on match
            if match.recommended_action == "Skip":
                results.append(MigrationResult(
                    success=True,
                    itglue_id=site_id,
                    itglue_name=match.itglue_name,
                    servicenow_id=None,
                    servicenow_name=None,
                    action="skipped",
                    message=f"Skipped: {match.notes}"
                ))
                continue
            
            if match.recommended_action == "Review Match":
                # In a real implementation, this would be handled by human review
                # For the demo, we'll proceed with the match
                self.logger.info(f"Proceeding with review match for {match.itglue_name}")
            
            # Migrate the site summary
            if match.servicenow_id and match.servicenow_id in servicenow_sites_by_id:
                # Update existing site CI
                result = self._update_site_ci(site, match, servicenow_sites_by_id[match.servicenow_id])
            else:
                # Create new site CI
                result = self._create_site_ci(site, match)
            
            results.append(result)
        
        # Log summary
        success_count = sum(1 for r in results if r.success)
        self.logger.info(f"Migration completed: {success_count}/{len(results)} successful")
        
        return results
    
    def _create_site_ci(self, 
                      itglue_site: Dict, 
                      match: SiteSummaryMatch) -> MigrationResult:
        """
        Create a new ServiceNow site CI.
        
        Args:
            itglue_site: IT Glue Site Summary data
            match: Match result
            
        Returns:
            Migration result
        """
        try:
            # Transform IT Glue data to ServiceNow format
            servicenow_data = self._transform_site_data(itglue_site)
            
            # In a real implementation, this would call the ServiceNow API
            # For the demo, we'll just log the data
            self.logger.info(f"Creating new site CI: {servicenow_data.get('name')}")
            
            if self.dry_run:
                return MigrationResult(
                    success=True,
                    itglue_id=match.itglue_id,
                    itglue_name=match.itglue_name,
                    servicenow_id="new_site_" + match.itglue_id,
                    servicenow_name=servicenow_data.get("name"),
                    action="would_create",
                    message="Would create new site CI (dry run)"
                )
            
            # Simulate creating a new record
            new_sys_id = "new_site_" + match.itglue_id
            
            return MigrationResult(
                success=True,
                itglue_id=match.itglue_id,
                itglue_name=match.itglue_name,
                servicenow_id=new_sys_id,
                servicenow_name=servicenow_data.get("name"),
                action="created",
                message="Created new site CI"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create site CI: {e}")
            return MigrationResult(
                success=False,
                itglue_id=match.itglue_id,
                itglue_name=match.itglue_name,
                servicenow_id=None,
                servicenow_name=None,
                action="failed",
                message=f"Failed to create site CI: {str(e)}"
            )
    
    def _update_site_ci(self, 
                      itglue_site: Dict, 
                      match: SiteSummaryMatch,
                      servicenow_site: Dict) -> MigrationResult:
        """
        Update an existing ServiceNow site CI.
        
        Args:
            itglue_site: IT Glue Site Summary data
            match: Match result
            servicenow_site: Existing ServiceNow site CI data
            
        Returns:
            Migration result
        """
        try:
            # Transform IT Glue data to ServiceNow format
            servicenow_data = self._transform_site_data(itglue_site)
            
            # In a real implementation, this would call the ServiceNow API
            # For the demo, we'll just log the data
            self.logger.info(f"Updating site CI: {servicenow_site.get('name')}")
            
            if self.dry_run:
                return MigrationResult(
                    success=True,
                    itglue_id=match.itglue_id,
                    itglue_name=match.itglue_name,
                    servicenow_id=match.servicenow_id,
                    servicenow_name=servicenow_site.get("name"),
                    action="would_update",
                    message="Would update site CI (dry run)"
                )
            
            return MigrationResult(
                success=True,
                itglue_id=match.itglue_id,
                itglue_name=match.itglue_name,
                servicenow_id=match.servicenow_id,
                servicenow_name=servicenow_site.get("name"),
                action="updated",
                message="Updated site CI"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to update site CI: {e}")
            return MigrationResult(
                success=False,
                itglue_id=match.itglue_id,
                itglue_name=match.itglue_name,
                servicenow_id=match.servicenow_id,
                servicenow_name=servicenow_site.get("name"),
                action="failed",
                message=f"Failed to update site CI: {str(e)}"
            )
    
    def _transform_site_data(self, itglue_site: Dict) -> Dict[str, Any]:
        """
        Transform IT Glue Site Summary data to ServiceNow site CI format.
        
        Args:
            itglue_site: IT Glue Site Summary data
            
        Returns:
            Transformed ServiceNow site CI data
        """
        attributes = itglue_site.get("attributes", {})
        traits = attributes.get("traits", {})
        
        # Extract basic information
        site_name = attributes.get("name", "")
        org_id = attributes.get("organization-id", "")
        org_name = attributes.get("organization-name", "")
        
        # Extract CoreID
        coreid = None
        for field_name, field_data in traits.items():
            field_name_lower = field_name.lower()
            if "coreid" in field_name_lower or "core_id" in field_name_lower:
                if isinstance(field_data, dict):
                    values = field_data.get("values", [])
                    if values and isinstance(values[0], dict):
                        coreid = values[0].get("value", "").strip()
                elif isinstance(field_data, str):
                    coreid = field_data.strip()
                break
        
        # Extract location
        location = None
        location_name = None
        if "location" in traits:
            location_data = traits.get("location", {})
            if isinstance(location_data, dict) and "values" in location_data:
                values = location_data.get("values", [])
                if values and isinstance(values[0], dict) and not values[0].get("resource-deleted", False):
                    location = values[0].get("id", "")
                    location_name = values[0].get("name", "")
                    address = values[0].get("address-1", "")
                    city = values[0].get("city", "")
                    if address and city:
                        location_name = f"{address}, {city}"
        
        # Extract primary contact
        primary_contact = None
        if "primary-contact" in traits:
            contact_data = traits.get("primary-contact", {})
            if isinstance(contact_data, dict) and "values" in contact_data:
                values = contact_data.get("values", [])
                if values and isinstance(values[0], dict) and not values[0].get("resource-deleted", False):
                    first_name = values[0].get("first-name", "")
                    last_name = values[0].get("last-name", "")
                    if first_name and last_name:
                        primary_contact = f"{first_name} {last_name}"
        
        # Extract other fields
        website = traits.get("website", "")
        primary_contact_phone = traits.get("primary-contact-phone", "")
        
        # Create ServiceNow data
        servicenow_data = {
            "name": site_name,
            "company": {
                "value": f"org_{org_id}",  # This would be the actual sys_id in a real implementation
                "display_value": org_name
            },
            "short_description": f"Site for {org_name}",
            "site_identifier": coreid or "",
            "operational_status": "1",  # Operational
            "u_primary_contact": primary_contact or "",
            "u_primary_contact_phone": primary_contact_phone or "",
            "u_website": website or ""
        }
        
        # Add location if available
        if location and location_name:
            servicenow_data["location"] = {
                "value": f"loc_{location}",  # This would be the actual sys_id in a real implementation
                "display_value": location_name
            }
        
        # Apply custom field mappings
        for mapping in self.field_mappings:
            itglue_field = mapping.get("itglue_field")
            servicenow_field = mapping.get("servicenow_field")
            
            if not itglue_field or not servicenow_field:
                continue
            
            # Extract value from traits
            value = None
            if itglue_field in traits:
                field_data = traits.get(itglue_field)
                if isinstance(field_data, dict) and "values" in field_data:
                    values = field_data.get("values", [])
                    if values and isinstance(values[0], dict) and not values[0].get("resource-deleted", False):
                        value = values[0].get("name", "")
                else:
                    value = field_data
            
            if value:
                servicenow_data[servicenow_field] = value
        
        return servicenow_data
    
    def _load_field_mappings(self) -> List[Dict[str, str]]:
        """
        Load field mappings from configuration.
        
        Returns:
            List of field mappings
        """
        # In a real implementation, this would load from a configuration file
        # For the demo, we'll use a hardcoded list
        return [
            {"itglue_field": "title", "servicenow_field": "name"},
            {"itglue_field": "coreid", "servicenow_field": "site_identifier"},
            {"itglue_field": "website", "servicenow_field": "u_website"},
            {"itglue_field": "primary-contact-phone", "servicenow_field": "u_primary_contact_phone"},
            {"itglue_field": "known-issues", "servicenow_field": "comments"}
        ]
    
    def generate_migration_report(self, results: List[MigrationResult]) -> Dict[str, Any]:
        """
        Generate a report of the migration results.
        
        Args:
            results: List of migration results
            
        Returns:
            Migration report
        """
        total = len(results)
        if total == 0:
            return {}
        
        # Count by action
        actions = {}
        for result in results:
            action = result.action
            if action not in actions:
                actions[action] = {"count": 0, "percentage": 0.0}
            actions[action]["count"] += 1
        
        # Calculate percentages
        for action in actions:
            actions[action]["percentage"] = actions[action]["count"] / total * 100
        
        # Count success/failure
        success_count = sum(1 for r in results if r.success)
        failure_count = total - success_count
        
        return {
            "total": total,
            "success_count": success_count,
            "success_percentage": (success_count / total * 100) if total > 0 else 0,
            "failure_count": failure_count,
            "failure_percentage": (failure_count / total * 100) if total > 0 else 0,
            "by_action": actions
        }