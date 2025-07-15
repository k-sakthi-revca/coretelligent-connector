"""
Voice PBX migrator for the migration demo.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from voice_pbx_matcher import VoicePBXMatch
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


class VoicePBXMigrator:
    """Migrates IT Glue Voice/PBX assets to ServiceNow voice gateway CIs."""
    
    def __init__(self, dry_run: bool = False):
        """
        Initialize voice PBX migrator.
        
        Args:
            dry_run: If True, don't actually create/update records
        """
        self.logger = logging.getLogger(__name__)
        self.dry_run = dry_run
        self.field_mappings = self._load_field_mappings()
        
        self.logger.info(f"Voice PBX Migrator initialized (dry_run={dry_run})")
    
    def migrate_voice_pbx_assets(self, 
                               itglue_assets: List[Dict], 
                               matches: List[VoicePBXMatch],
                               servicenow_gateways: List[Dict]) -> List[MigrationResult]:
        """
        Migrate IT Glue Voice/PBX assets to ServiceNow voice gateway CIs.
        
        Args:
            itglue_assets: List of IT Glue Voice/PBX data
            matches: List of match results
            servicenow_gateways: List of ServiceNow voice gateway CI data
            
        Returns:
            List of migration results
        """
        self.logger.info(f"Migrating {len(itglue_assets)} IT Glue Voice/PBX assets")
        
        # Create lookup dictionaries
        itglue_assets_by_id = {asset.get("id"): asset for asset in itglue_assets}
        servicenow_gateways_by_id = {gateway.get("sys_id"): gateway for gateway in servicenow_gateways}
        matches_by_itglue_id = {match.itglue_id: match for match in matches}
        
        # Migrate each voice PBX asset
        results = []
        
        for asset_id, asset in itglue_assets_by_id.items():
            match = matches_by_itglue_id.get(asset_id)
            
            if not match:
                self.logger.warning(f"No match found for asset {asset_id}")
                results.append(MigrationResult(
                    success=False,
                    itglue_id=asset_id,
                    itglue_name=asset.get("attributes", {}).get("name", "Unknown"),
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
                    itglue_id=asset_id,
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
            
            # Migrate the voice PBX asset
            if match.servicenow_id and match.servicenow_id in servicenow_gateways_by_id:
                # Update existing voice gateway CI
                result = self._update_voice_gateway_ci(asset, match, servicenow_gateways_by_id[match.servicenow_id])
            else:
                # Create new voice gateway CI
                result = self._create_voice_gateway_ci(asset, match)
            
            results.append(result)
        
        # Log summary
        success_count = sum(1 for r in results if r.success)
        self.logger.info(f"Migration completed: {success_count}/{len(results)} successful")
        
        return results
    
    def _create_voice_gateway_ci(self, 
                               itglue_asset: Dict, 
                               match: VoicePBXMatch) -> MigrationResult:
        """
        Create a new ServiceNow voice gateway CI.
        
        Args:
            itglue_asset: IT Glue Voice/PBX data
            match: Match result
            
        Returns:
            Migration result
        """
        try:
            # Transform IT Glue data to ServiceNow format
            servicenow_data = self._transform_voice_pbx_data(itglue_asset)
            
            # In a real implementation, this would call the ServiceNow API
            # For the demo, we'll just log the data
            self.logger.info(f"Creating new voice gateway CI: {servicenow_data.get('name')}")
            
            if self.dry_run:
                return MigrationResult(
                    success=True,
                    itglue_id=match.itglue_id,
                    itglue_name=match.itglue_name,
                    servicenow_id="new_gateway_" + match.itglue_id,
                    servicenow_name=servicenow_data.get("name"),
                    action="would_create",
                    message="Would create new voice gateway CI (dry run)"
                )
            
            # Simulate creating a new record
            new_sys_id = "new_gateway_" + match.itglue_id
            
            return MigrationResult(
                success=True,
                itglue_id=match.itglue_id,
                itglue_name=match.itglue_name,
                servicenow_id=new_sys_id,
                servicenow_name=servicenow_data.get("name"),
                action="created",
                message="Created new voice gateway CI"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to create voice gateway CI: {e}")
            return MigrationResult(
                success=False,
                itglue_id=match.itglue_id,
                itglue_name=match.itglue_name,
                servicenow_id=None,
                servicenow_name=None,
                action="failed",
                message=f"Failed to create voice gateway CI: {str(e)}"
            )
    
    def _update_voice_gateway_ci(self, 
                               itglue_asset: Dict, 
                               match: VoicePBXMatch,
                               servicenow_gateway: Dict) -> MigrationResult:
        """
        Update an existing ServiceNow voice gateway CI.
        
        Args:
            itglue_asset: IT Glue Voice/PBX data
            match: Match result
            servicenow_gateway: Existing ServiceNow voice gateway CI data
            
        Returns:
            Migration result
        """
        try:
            # Transform IT Glue data to ServiceNow format
            servicenow_data = self._transform_voice_pbx_data(itglue_asset)
            
            # In a real implementation, this would call the ServiceNow API
            # For the demo, we'll just log the data
            self.logger.info(f"Updating voice gateway CI: {servicenow_gateway.get('name')}")
            
            if self.dry_run:
                return MigrationResult(
                    success=True,
                    itglue_id=match.itglue_id,
                    itglue_name=match.itglue_name,
                    servicenow_id=match.servicenow_id,
                    servicenow_name=servicenow_gateway.get("name"),
                    action="would_update",
                    message="Would update voice gateway CI (dry run)"
                )
            
            return MigrationResult(
                success=True,
                itglue_id=match.itglue_id,
                itglue_name=match.itglue_name,
                servicenow_id=match.servicenow_id,
                servicenow_name=servicenow_gateway.get("name"),
                action="updated",
                message="Updated voice gateway CI"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to update voice gateway CI: {e}")
            return MigrationResult(
                success=False,
                itglue_id=match.itglue_id,
                itglue_name=match.itglue_name,
                servicenow_id=match.servicenow_id,
                servicenow_name=servicenow_gateway.get("name"),
                action="failed",
                message=f"Failed to update voice gateway CI: {str(e)}"
            )
    
    def _transform_voice_pbx_data(self, itglue_asset: Dict) -> Dict[str, Any]:
        """
        Transform IT Glue Voice/PBX data to ServiceNow voice gateway CI format.
        
        Args:
            itglue_asset: IT Glue Voice/PBX data
            
        Returns:
            Transformed ServiceNow voice gateway CI data
        """
        attributes = itglue_asset.get("attributes", {})
        traits = attributes.get("traits", {})
        
        # Extract basic information
        asset_name = attributes.get("name", "")
        org_id = attributes.get("organization-id", "")
        org_name = attributes.get("organization-name", "")
        
        # Extract manufacturer and model
        manufacturer = traits.get("manufacturer", "")
        model = traits.get("model", "")
        
        # Create short description
        short_description = f"{manufacturer} {model}"
        if not short_description.strip():
            short_description = asset_name
        
        # Create ServiceNow data
        servicenow_data = {
            "name": asset_name,
            "company": {
                "value": f"org_{org_id}",  # This would be the actual sys_id in a real implementation
                "display_value": org_name
            },
            "short_description": short_description,
            "operational_status": "1"  # Operational
        }
        
        # Add manufacturer if available
        if manufacturer:
            servicenow_data["manufacturer"] = {
                "value": f"manufacturer_{manufacturer.lower().replace(' ', '_')}",  # This would be the actual sys_id in a real implementation
                "display_value": manufacturer
            }
        
        # Add model if available
        if model:
            servicenow_data["model_id"] = {
                "value": f"model_{model.lower().replace(' ', '_')}",  # This would be the actual sys_id in a real implementation
                "display_value": model
            }
        
        # Apply field mappings
        for mapping in self.field_mappings:
            itglue_field = mapping.get("itglue_field")
            servicenow_field = mapping.get("servicenow_field")
            
            if not itglue_field or not servicenow_field:
                continue
            
            # Extract value from traits
            if itglue_field in traits:
                value = traits.get(itglue_field)
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
            {"itglue_field": "system-type", "servicenow_field": "u_system_type"},
            {"itglue_field": "version", "servicenow_field": "version"},
            {"itglue_field": "serial-number", "servicenow_field": "serial_number"},
            {"itglue_field": "ip-address", "servicenow_field": "ip_address"},
            {"itglue_field": "mac-address", "servicenow_field": "mac_address"},
            {"itglue_field": "phone-numbers", "servicenow_field": "u_phone_numbers"},
            {"itglue_field": "service-provider", "servicenow_field": "u_service_provider"},
            {"itglue_field": "support-contact", "servicenow_field": "u_support_contact"},
            {"itglue_field": "admin-portal", "servicenow_field": "u_admin_portal"},
            {"itglue_field": "notes", "servicenow_field": "comments"}
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