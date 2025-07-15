"""
Script to run the organization migration from IT Glue to ServiceNow using real APIs.
"""

import os
import json
import logging
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

from itglue_client import ITGlueClient
from servicenow_client import ServiceNowClient
from organization_migrator import OrganizationMigrator, MigrationResult
from config import config

# Configure logging
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = os.path.join(log_dir, f"organization_migration_{timestamp}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def load_org_connector_relationships() -> List[Dict]:
    """
    Load organization connector relationships from JSON file.
    
    Returns:
        List of organization connector relationships
    """
    try:
        with open(os.path.join("data", "org_connector_relationships.json"), 'r') as f:
            data = json.load(f)
        logger.info(f"Loaded {len(data)} organization connector relationships")
        return data
    except Exception as e:
        logger.error(f"Failed to load organization connector relationships: {e}")
        return []


def migrate_organizations_with_real_apis():
    """
    Migrate organizations from IT Glue to ServiceNow using real APIs.
    """
    logger.info("Starting organization migration with real APIs")
    
    # Load organization connector relationships
    relationships = load_org_connector_relationships()
    
    if not relationships:
        logger.error("No organization connector relationships found")
        return
    
    # Limit to 10 organizations as requested
    relationships = relationships[:10]
    
    # Initialize clients with real API mode
    itglue_client = ITGlueClient(use_mock_data=False)
    servicenow_client = ServiceNowClient()
    
    # Create report directory if it doesn't exist
    os.makedirs("reports", exist_ok=True)
    
    # Initialize migration results
    migration_results = []
    
    # Process each organization
    for i, relationship in enumerate(relationships, 1):
        org_name = relationship.get("name", "Unknown")
        itg_org_id = relationship.get("itg_org_id")
        sn_sys_id = relationship.get("sn_sys_id")
        
        logger.info(f"Processing organization {i}/{len(relationships)}: {org_name}")
        
        # Skip if missing required IDs
        if not itg_org_id or not sn_sys_id:
            logger.warning(f"Skipping {org_name} due to missing IDs: ITG ID={itg_org_id}, SN ID={sn_sys_id}")
            migration_results.append({
                "name": org_name,
                "itg_org_id": itg_org_id,
                "sn_sys_id": sn_sys_id,
                "status": "skipped",
                "reason": "Missing required IDs",
                "itglue_data": None,
                "servicenow_data": None
            })
            continue
        
        try:
            # Fetch organization data from IT Glue
            itglue_org = itglue_client.get_organization_by_id(str(itg_org_id))
            
            if not itglue_org:
                logger.warning(f"Organization not found in IT Glue: {org_name} (ID: {itg_org_id})")
                migration_results.append({
                    "name": org_name,
                    "itg_org_id": itg_org_id,
                    "sn_sys_id": sn_sys_id,
                    "status": "failed",
                    "reason": "Organization not found in IT Glue",
                    "itglue_data": None,
                    "servicenow_data": None
                })
                continue
            
            # Fetch company data from ServiceNow
            servicenow_company = servicenow_client.get_company_by_sys_id(sn_sys_id)
            
            if not servicenow_company:
                logger.warning(f"Company not found in ServiceNow: {org_name} (ID: {sn_sys_id})")
                migration_results.append({
                    "name": org_name,
                    "itg_org_id": itg_org_id,
                    "sn_sys_id": sn_sys_id,
                    "status": "failed",
                    "reason": "Company not found in ServiceNow",
                    "itglue_data": itglue_org,
                    "servicenow_data": None
                })
                continue
            
            # Map IT Glue data to ServiceNow format
            # This is a simplified mapping - in a real implementation, you would use a more sophisticated mapping
            mapped_data = map_itglue_to_servicenow(itglue_org, servicenow_company)
            
            # Update the ServiceNow company with the mapped data
            updated_company = servicenow_client.update_company(sn_sys_id, mapped_data)
            
            if updated_company:
                logger.info(f"Successfully updated ServiceNow company: {org_name}")
                status = "success"
                reason = "Successfully migrated data from IT Glue to ServiceNow"
            else:
                logger.warning(f"Failed to update ServiceNow company: {org_name}")
                status = "failed"
                reason = "Failed to update ServiceNow company"
            
            # Successfully fetched both sides
            logger.info(f"Successfully processed {org_name}")
            migration_results.append({
                "name": org_name,
                "itg_org_id": itg_org_id,
                "sn_sys_id": sn_sys_id,
                "status": status,
                "reason": reason,
                "itglue_data": itglue_org,
                "servicenow_data": servicenow_company,
                "mapped_data": mapped_data,
                "updated_company": updated_company
            })
            
        except Exception as e:
            logger.error(f"Error processing {org_name}: {e}")
            migration_results.append({
                "name": org_name,
                "itg_org_id": itg_org_id,
                "sn_sys_id": sn_sys_id,
                "status": "error",
                "reason": str(e),
                "itglue_data": None,
                "servicenow_data": None
            })
    
    # Generate report
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_organizations": len(relationships),
        "successful": len([r for r in migration_results if r["status"] == "success"]),
        "failed": len([r for r in migration_results if r["status"] in ["failed", "error"]]),
        "skipped": len([r for r in migration_results if r["status"] == "skipped"]),
        "results": migration_results
    }
    
    # Save report
    report_file = os.path.join("reports", f"organization_migration_report_{timestamp}.json")
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Migration completed. Report saved to {report_file}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("Migration Summary")
    print("=" * 80)
    print(f"Total Organizations: {report['total_organizations']}")
    print(f"Successful: {report['successful']}")
    print(f"Failed: {report['failed']}")
    print(f"Skipped: {report['skipped']}")
    print("-" * 80)
    print(f"Report saved to: {report_file}")
    print("=" * 80)


def map_itglue_to_servicenow(itglue_org: Dict, servicenow_company: Dict) -> Dict:
    """
    Map IT Glue organization data to ServiceNow company data.
    
    Args:
        itglue_org: IT Glue organization data
        servicenow_company: ServiceNow company data
        
    Returns:
        Mapped ServiceNow company data
    """
    # Extract IT Glue attributes
    itg_attributes = itglue_org.get("attributes", {})
    
    # Create a new dictionary with only the fields we want to update
    mapped_data = {}
    
    # Map name if it exists
    if "name" in itg_attributes:
        mapped_data["name"] = itg_attributes["name"]
    
    # Map description if it exists
    if "description" in itg_attributes and itg_attributes["description"]:
        mapped_data["notes"] = itg_attributes["description"]
    
    # Map organization status
    if "organization-status-name" in itg_attributes:
        status_name = itg_attributes["organization-status-name"]
        mapped_data["active"] = "true" if status_name == "Active" else "false"
    
    # Add a note about the migration
    notes = servicenow_company.get("notes", "")
    migration_note = f"\n\nMigrated from IT Glue on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    if "description" in itg_attributes and itg_attributes["description"]:
        migration_note += f"\n\nIT Glue Description: {itg_attributes['description']}"
    
    mapped_data["notes"] = notes + migration_note if notes else migration_note
    
    return mapped_data


if __name__ == "__main__":
    migrate_organizations_with_real_apis()