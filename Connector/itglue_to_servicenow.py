"""
ITGlue to ServiceNow Migration Tool

This script orchestrates the migration of data from ITGlue to ServiceNow.
It extracts data from ITGlue, transforms it to match ServiceNow's data model,
and provides a framework for loading it into ServiceNow.
"""
import os
import sys
import json
import logging
import argparse
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
from itglue_connector import ITGlueConnector
from itglue_data_extractor import ITGlueDataExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("migration.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('itglue_to_servicenow')

class ITGlueToServiceNowMigration:
    """
    Class to handle the migration of data from ITGlue to ServiceNow
    """
    def __init__(self, itglue_api_key: str, servicenow_instance: str = None, 
                 servicenow_username: str = None, servicenow_password: str = None):
        """
        Initialize the migration tool
        
        Args:
            itglue_api_key: ITGlue API key
            servicenow_instance: ServiceNow instance URL (optional for now)
            servicenow_username: ServiceNow username (optional for now)
            servicenow_password: ServiceNow password (optional for now)
        """
        self.itglue_extractor = ITGlueDataExtractor(itglue_api_key)
        
        # ServiceNow credentials (to be implemented later)
        self.servicenow_instance = servicenow_instance
        self.servicenow_username = servicenow_username
        self.servicenow_password = servicenow_password
        
        # Create directories for transformed data
        self.transformed_dir = "transformed_data"
        os.makedirs(self.transformed_dir, exist_ok=True)
        
        logger.info("ITGlue to ServiceNow Migration Tool initialized")
    
    def transform_organizations(self, organizations: List[Dict]) -> List[Dict]:
        """
        Transform ITGlue organizations to ServiceNow companies
        
        Args:
            organizations: List of ITGlue organizations
            
        Returns:
            List of transformed organizations for ServiceNow
        """
        logger.info("Transforming organizations data for ServiceNow")
        
        transformed = []
        for org in organizations:
            # Map ITGlue organization fields to ServiceNow company fields
            # This is a placeholder mapping - adjust based on ServiceNow's actual schema
            transformed_org = {
                'name': org.get('name'),
                'description': org.get('description'),
                'website': org.get('website'),
                'u_itglue_id': org.get('id'),  # Store original ITGlue ID as reference
                'sys_created_on': org.get('created_at'),
                'sys_updated_on': org.get('updated_at')
            }
            transformed.append(transformed_org)
        
        # Save transformed data
        df = pd.DataFrame(transformed)
        output_path = os.path.join(self.transformed_dir, "servicenow_companies.csv")
        df.to_csv(output_path, index=False)
        
        return transformed
    
    def transform_configurations(self, configurations: List[Dict], config_type: str) -> List[Dict]:
        """
        Transform ITGlue configurations to ServiceNow CIs
        
        Args:
            configurations: List of ITGlue configurations
            config_type: Type of configuration (e.g., 'servers', 'workstations')
            
        Returns:
            List of transformed configurations for ServiceNow
        """
        logger.info("Transforming {} configurations for ServiceNow".format(config_type))
        
        # Map ITGlue configuration types to ServiceNow CI classes
        ci_class_mapping = {
            'servers': 'cmdb_ci_server',
            'workstations': 'cmdb_ci_pc',
            'laptops': 'cmdb_ci_pc',
            'desktops': 'cmdb_ci_pc',
            'network_devices': 'cmdb_ci_netgear',
            'printers': 'cmdb_ci_printer',
            'mobile_devices': 'cmdb_ci_mobile_device',
            'storage_devices': 'cmdb_ci_storage_device'
        }
        
        ci_class = ci_class_mapping.get(config_type, 'cmdb_ci')
        
        transformed = []
        for config in configurations:
            # Map ITGlue configuration fields to ServiceNow CI fields
            # This is a placeholder mapping - adjust based on ServiceNow's actual schema
            transformed_config = {
                'name': config.get('name'),
                'serial_number': config.get('serial_number'),
                'asset_tag': config.get('asset_tag'),
                'manufacturer': config.get('manufacturer'),
                'model_id': config.get('model'),
                'company': config.get('organization_id'),  # Will need to be mapped to ServiceNow company sys_id
                'sys_class_name': ci_class,
                'u_itglue_id': config.get('id'),  # Store original ITGlue ID as reference
                'sys_created_on': config.get('created_at'),
                'sys_updated_on': config.get('updated_at')
            }
            transformed.append(transformed_config)
        
        # Save transformed data
        df = pd.DataFrame(transformed)
        output_path = os.path.join(self.transformed_dir, "servicenow_{}.csv".format(config_type))
        df.to_csv(output_path, index=False)
        
        return transformed
    
    def transform_flexible_assets(self, assets: List[Dict], asset_type_name: str) -> List[Dict]:
        """
        Transform ITGlue flexible assets to ServiceNow records
        
        Args:
            assets: List of ITGlue flexible assets
            asset_type_name: Type of flexible asset
            
        Returns:
            List of transformed assets for ServiceNow
        """
        logger.info("Transforming {} flexible assets for ServiceNow".format(asset_type_name))
        
        # Map ITGlue flexible asset types to ServiceNow tables
        # This is a placeholder mapping - adjust based on ServiceNow's actual schema
        table_mapping = {
            'voice_pbx': 'cmdb_ci_voice_gateway',
            'wireless_networks': 'cmdb_ci_wlan',
            'line_of_business_applications': 'cmdb_ci_appl',
            'email_systems': 'cmdb_ci_email_server',
            'identity_services': 'cmdb_ci_directory_server',
            'backup_solutions': 'cmdb_ci_backup',
            'security_systems': 'cmdb_ci_security_system',
            'licensing_renewals': 'cmdb_software_license'
        }
        
        table = table_mapping.get(asset_type_name, 'x_custom_itglue_assets')
        
        transformed = []
        for asset in assets:
            # Start with basic fields
            transformed_asset = {
                'name': asset.get('name'),
                'company': asset.get('organization_id'),  # Will need to be mapped to ServiceNow company sys_id
                'u_itglue_id': asset.get('id'),  # Store original ITGlue ID as reference
                'sys_created_on': asset.get('created_at'),
                'sys_updated_on': asset.get('updated_at'),
                'sys_class_name': table
            }
            
            # Add trait fields (custom fields from ITGlue)
            # We'll prefix them with u_itglue_trait_ to avoid conflicts
            for key, value in asset.items():
                if key.startswith('trait_'):
                    field_name = "u_itglue_{}".format(key)
                    transformed_asset[field_name] = value
            
            transformed.append(transformed_asset)
        
        # Save transformed data
        df = pd.DataFrame(transformed)
        output_path = os.path.join(self.transformed_dir, "servicenow_{}.csv".format(asset_type_name))
        df.to_csv(output_path, index=False)
        
        return transformed
    
    def run_migration(self, extract_only: bool = False):
        """
        Run the full migration process
        
        Args:
            extract_only: If True, only extract data from ITGlue without transforming or loading
        """
        logger.info("Starting migration process")
        
        # Step 1: Extract data from ITGlue
        logger.info("Step 1: Extracting data from ITGlue")
        
        # Extract organizations
        organizations = self.itglue_extractor.extract_organizations()
        
        # Extract flexible asset types
        asset_types = self.itglue_extractor.extract_flexible_asset_types()
        
        # Extract domains
        domains = self.itglue_extractor.extract_domains()
        
        # Extract configurations for common types
        config_types = {
            '703409': 'servers',
            '328008': 'workstations',
            '122621': 'laptops',
            '328015': 'desktops',
            '124327': 'network_devices',
            '122627': 'printers',
            '328022': 'mobile_devices',
            '124328': 'storage_devices'
        }
        
        configurations = {}
        for type_id, type_name in config_types.items():
            configurations[type_name] = self.itglue_extractor.extract_configurations(
                config_type_id=int(type_id),
                config_type_name=type_name
            )
        
        # Extract flexible assets for each type
        flexible_assets = {}
        for asset_type in asset_types:
            type_id = int(asset_type['id'])
            type_name = asset_type['name'].replace(' ', '_').lower()
            flexible_assets[type_name] = self.itglue_extractor.extract_flexible_assets(
                asset_type_id=type_id, 
                asset_type_name=type_name
            )
        
        if extract_only:
            logger.info("Extract-only mode: Skipping transformation and loading steps")
            return
        
        # Step 2: Transform data for ServiceNow
        logger.info("Step 2: Transforming data for ServiceNow")
        
        # Transform organizations
        transformed_orgs = self.transform_organizations(organizations)
        
        # Transform configurations
        transformed_configs = {}
        for config_type, configs in configurations.items():
            transformed_configs[config_type] = self.transform_configurations(configs, config_type)
        
        # Transform flexible assets
        transformed_assets = {}
        for asset_type, assets in flexible_assets.items():
            transformed_assets[asset_type] = self.transform_flexible_assets(assets, asset_type)
        
        # Step 3: Load data into ServiceNow (placeholder for now)
        logger.info("Step 3: Loading data into ServiceNow (not implemented yet)")
        logger.info("Data has been transformed and saved to CSV files in the 'transformed_data' directory")
        logger.info("To complete the migration, you'll need to implement the ServiceNow API integration")
        
        # Create a summary file
        summary = {
            'migration_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'data_counts': {
                'organizations': len(organizations),
                'configurations': {k: len(v) for k, v in configurations.items()},
                'flexible_assets': {k: len(v) for k, v in flexible_assets.items()}
            }
        }
        
        with open(os.path.join(self.transformed_dir, 'migration_summary.json'), 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info("Migration process completed successfully")

def main():
    """
    Main function to run the migration tool from command line
    """
    parser = argparse.ArgumentParser(description='ITGlue to ServiceNow Migration Tool')
    parser.add_argument('--itglue-api-key', required=True, help='ITGlue API key')
    parser.add_argument('--servicenow-instance', help='ServiceNow instance URL')
    parser.add_argument('--servicenow-username', help='ServiceNow username')
    parser.add_argument('--servicenow-password', help='ServiceNow password')
    parser.add_argument('--extract-only', action='store_true', help='Only extract data from ITGlue without transforming or loading')
    
    args = parser.parse_args()
    
    migration = ITGlueToServiceNowMigration(
        itglue_api_key=args.itglue_api_key,
        servicenow_instance=args.servicenow_instance,
        servicenow_username=args.servicenow_username,
        servicenow_password=args.servicenow_password
    )
    
    migration.run_migration(extract_only=args.extract_only)

if __name__ == "__main__":
    # Example usage
    API_KEY = "ITG.005c32616f608910a8f1dfa40a7bdf73.TaTMBpSXUsJFEKlcJE7BRFL2m-CN4KAJbntZ9iFxpb0SUwteUS3wDjJl4yhkgWpP"
    
    # For command-line usage:
    # main()
    
    # For direct usage:
    migration = ITGlueToServiceNowMigration(itglue_api_key=API_KEY)
    migration.run_migration(extract_only=True)  # Set to False when ServiceNow integration is implemented