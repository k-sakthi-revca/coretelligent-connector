"""
ITGlue Data Extractor - Module for extracting data from ITGlue API
"""
import os
import json
import logging
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
from itglue_connector import ITGlueConnector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('itglue_data_extractor')

class ITGlueDataExtractor:
    """
    Class for extracting and processing data from ITGlue
    """
    def __init__(self, api_key: str, output_dir: str = "extracted_data"):
        """
        Initialize the data extractor
        
        Args:
            api_key: ITGlue API key
            output_dir: Directory to save extracted data
        """
        self.connector = ITGlueConnector(api_key)
        self.output_dir = output_dir
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Cache for organizations to avoid repeated API calls
        self.organizations_cache = None
        
        logger.info("ITGlue Data Extractor initialized with output directory: {}".format(output_dir))
    
    def _save_to_json(self, data: Any, filename: str) -> str:
        """
        Save data to a JSON file
        
        Args:
            data: Data to save
            filename: Name of the file (without extension)
            
        Returns:
            Path to the saved file
        """
        filepath = os.path.join(self.output_dir, "{}.json".format(filename))
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        logger.info("Saved data to {}".format(filepath))
        return filepath
    
    def _save_to_csv(self, data: List[Dict], filename: str) -> str:
        """
        Save data to a CSV file
        
        Args:
            data: List of dictionaries to save
            filename: Name of the file (without extension)
            
        Returns:
            Path to the saved file
        """
        filepath = os.path.join(self.output_dir, "{}.csv".format(filename))
        
        # Convert to DataFrame and save
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)
        
        logger.info("Saved data to {}".format(filepath))
        return filepath
    
    def extract_organizations(self) -> List[Dict]:
        """
        Extract organizations (companies) data
        
        Returns:
            List of processed organization data
        """
        logger.info("Extracting organizations data")
        
        if self.organizations_cache is None:
            raw_data = self.connector.get_organizations()
            
            # Process the data
            processed_data = []
            for item in raw_data:
                org = {
                    'id': item.get('id'),
                    'name': item.get('attributes', {}).get('name'),
                    'description': item.get('attributes', {}).get('description'),
                    'website': item.get('attributes', {}).get('website'),
                    'created_at': item.get('attributes', {}).get('created-at'),
                    'updated_at': item.get('attributes', {}).get('updated-at')
                }
                processed_data.append(org)
            
            # Cache the results
            self.organizations_cache = processed_data
            
            # Save the data
            self._save_to_json(raw_data, "organizations_raw")
            self._save_to_csv(processed_data, "organizations")
        
        return self.organizations_cache
    
    def extract_flexible_asset_types(self) -> List[Dict]:
        """
        Extract flexible asset types
        
        Returns:
            List of processed flexible asset types
        """
        logger.info("Extracting flexible asset types")
        
        raw_data = self.connector.get_flexible_asset_types()
        
        # Process the data
        processed_data = []
        for item in raw_data:
            asset_type = {
                'id': item.get('id'),
                'name': item.get('attributes', {}).get('name'),
                'description': item.get('attributes', {}).get('description'),
                'icon': item.get('attributes', {}).get('icon'),
                'created_at': item.get('attributes', {}).get('created-at'),
                'updated_at': item.get('attributes', {}).get('updated-at')
            }
            processed_data.append(asset_type)
        
        # Save the data
        self._save_to_json(raw_data, "flexible_asset_types_raw")
        self._save_to_csv(processed_data, "flexible_asset_types")
        
        return processed_data
    
    def extract_flexible_assets(self, asset_type_id: Optional[int] = None, asset_type_name: str = None) -> List[Dict]:
        """
        Extract flexible assets data
        
        Args:
            asset_type_id: Optional ID of the asset type to extract
            asset_type_name: Optional name for the output file
            
        Returns:
            List of processed flexible assets
        """
        type_name = asset_type_name or "type_{}".format(asset_type_id) if asset_type_id else "all"
        logger.info("Extracting flexible assets for {}".format(type_name))
        
        raw_data = self.connector.get_flexible_assets(asset_type_id)
        
        # Process the data
        processed_data = []
        for item in raw_data:
            # Extract traits (custom fields)
            traits = item.get('attributes', {}).get('traits', {})
            
            asset = {
                'id': item.get('id'),
                'name': item.get('attributes', {}).get('name'),
                'organization_id': item.get('attributes', {}).get('organization-id'),
                'flexible_asset_type_id': item.get('attributes', {}).get('flexible-asset-type-id'),
                'created_at': item.get('attributes', {}).get('created-at'),
                'updated_at': item.get('attributes', {}).get('updated-at')
            }
            
            # Add traits as flattened fields
            for key, value in traits.items():
                asset["trait_{}".format(key)] = value
            
            processed_data.append(asset)
        
        # Save the data
        self._save_to_json(raw_data, "flexible_assets_{}_raw".format(type_name))
        self._save_to_csv(processed_data, "flexible_assets_{}".format(type_name))
        
        return processed_data
    
    def extract_configurations(self, config_type_id: Optional[int] = None, config_type_name: str = None) -> List[Dict]:
        """
        Extract configurations data
        
        Args:
            config_type_id: Optional ID of the configuration type to extract
            config_type_name: Optional name for the output file
            
        Returns:
            List of processed configurations
        """
        type_name = config_type_name or "type_{}".format(config_type_id) if config_type_id else "all"
        logger.info("Extracting configurations for {}".format(type_name))
        
        raw_data = self.connector.get_configurations(config_type_id)
        
        # Process the data
        processed_data = []
        for item in raw_data:
            config = {
                'id': item.get('id'),
                'name': item.get('attributes', {}).get('name'),
                'organization_id': item.get('attributes', {}).get('organization-id'),
                'configuration_type_id': item.get('attributes', {}).get('configuration-type-id'),
                'configuration_status_id': item.get('attributes', {}).get('configuration-status-id'),
                'manufacturer': item.get('attributes', {}).get('manufacturer'),
                'model': item.get('attributes', {}).get('model'),
                'serial_number': item.get('attributes', {}).get('serial-number'),
                'asset_tag': item.get('attributes', {}).get('asset-tag'),
                'created_at': item.get('attributes', {}).get('created-at'),
                'updated_at': item.get('attributes', {}).get('updated-at')
            }
            processed_data.append(config)
        
        # Save the data
        self._save_to_json(raw_data, "configurations_{}_raw".format(type_name))
        self._save_to_csv(processed_data, "configurations_{}".format(type_name))
        
        return processed_data
    
    def extract_domains(self) -> List[Dict]:
        """
        Extract domains data
        
        Returns:
            List of processed domains
        """
        logger.info("Extracting domains data")
        
        raw_data = self.connector.get_domains()
        
        # Process the data
        processed_data = []
        for item in raw_data:
            domain = {
                'id': item.get('id'),
                'name': item.get('attributes', {}).get('name'),
                'organization_id': item.get('attributes', {}).get('organization-id'),
                'expires_on': item.get('attributes', {}).get('expires-on'),
                'created_at': item.get('attributes', {}).get('created-at'),
                'updated_at': item.get('attributes', {}).get('updated-at')
            }
            processed_data.append(domain)
        
        # Save the data
        self._save_to_json(raw_data, "domains_raw")
        self._save_to_csv(processed_data, "domains")
        
        return processed_data
    
    def extract_all_data(self) -> Dict[str, List[Dict]]:
        """
        Extract all available data from ITGlue
        
        Returns:
            Dictionary with all extracted data
        """
        logger.info("Starting extraction of all ITGlue data")
        
        # Create timestamp for this extraction
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extraction_dir = os.path.join(self.output_dir, "extraction_{}".format(timestamp))
        os.makedirs(extraction_dir, exist_ok=True)
        
        # Temporarily change output directory
        original_output_dir = self.output_dir
        self.output_dir = extraction_dir
        
        # Extract all data types
        result = {
            'organizations': self.extract_organizations(),
            'flexible_asset_types': self.extract_flexible_asset_types(),
            'domains': self.extract_domains()
        }
        
        # Extract flexible assets for each type
        asset_types = self.extract_flexible_asset_types()
        for asset_type in asset_types:
            type_id = int(asset_type['id'])
            type_name = asset_type['name'].replace(' ', '_').lower()
            result['flexible_assets_{}'.format(type_name)] = self.extract_flexible_assets(
                asset_type_id=type_id, 
                asset_type_name=type_name
            )
        
        # Extract configurations for common types
        config_types = {
            '703409': 'servers',
            '328008': 'workstations',
            '122621': 'laptops',
            '328015': 'desktops',
            '124327': 'network_devices',
            '122627': 'printers',
            '328022': 'mobile_devices',
            '124328': 'storage_devices',
            '124324': 'application_servers',
            '124329': 'unified_communication_equipment',
            '328026': 'ssl_certificates',
            '328029': 'ups'
        }
        
        for type_id, type_name in config_types.items():
            result['configurations_{}'.format(type_name)] = self.extract_configurations(
                config_type_id=int(type_id),
                config_type_name=type_name
            )
        
        # Restore original output directory
        self.output_dir = original_output_dir
        
        logger.info("Completed extraction of all ITGlue data to {}".format(extraction_dir))
        
        # Create a summary file
        summary = {
            'extraction_time': timestamp,
            'data_counts': {key: len(value) for key, value in result.items()}
        }
        
        with open(os.path.join(extraction_dir, 'extraction_summary.json'), 'w') as f:
            json.dump(summary, f, indent=2)
        
        return result

if __name__ == "__main__":
    # Example usage
    API_KEY = "ITG.005c32616f608910a8f1dfa40a7bdf73.TaTMBpSXUsJFEKlcJE7BRFL2m-CN4KAJbntZ9iFxpb0SUwteUS3wDjJl4yhkgWpP"
    extractor = ITGlueDataExtractor(API_KEY)
    
    # Extract all data
    # extractor.extract_all_data()
    
    # Or extract specific data types
    # extractor.extract_organizations()
    # extractor.extract_flexible_assets(asset_type_id=43489, asset_type_name="voice_pbx")