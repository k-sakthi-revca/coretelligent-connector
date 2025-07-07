"""
Script to run the ITGlue data extraction and display some of the extracted data
"""
import os
import json
import logging
import pandas as pd
from itglue_data_extractor import ITGlueDataExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('run_extraction')

def display_data_sample(data, title, max_items=5):
    """
    Display a sample of the extracted data
    
    Args:
        data: List of dictionaries containing the data
        title: Title to display
        max_items: Maximum number of items to display
    """
    print("\n{}".format('-'*80))
    print("{} ({} items found)".format(title, len(data)))
    print("{}".format('-'*80))
    
    for i, item in enumerate(data[:max_items]):
        print("Item {}:".format(i+1))
        for key, value in item.items():
            # Truncate long values for display
            if isinstance(value, str) and len(value) > 100:
                value = value[:100] + "..."
            print("  {}: {}".format(key, value))
        print()
    
    if len(data) > max_items:
        print("... and {} more items".format(len(data) - max_items))
    print("{}\n".format('-'*80))

def main():
    """
    Main function to run the extraction and display results
    """
    # Get API key from environment variable or use the default one
    api_key = os.environ.get(
        'ITGLUE_API_KEY', 
        'ITG.005c32616f608910a8f1dfa40a7bdf73.TaTMBpSXUsJFEKlcJE7BRFL2m-CN4KAJbntZ9iFxpb0SUwteUS3wDjJl4yhkgWpP'
    )
    
    # Create output directory for this run
    output_dir = "extracted_data"
    
    logger.info("Starting ITGlue data extraction to {}".format(output_dir))
    
    # Initialize the data extractor
    extractor = ITGlueDataExtractor(api_key, output_dir=output_dir)
    
    # Extract organizations
    logger.info("Extracting organizations...")
    organizations = extractor.extract_organizations()
    display_data_sample(organizations, "Organizations")
    
    # Extract flexible asset types
    logger.info("Extracting flexible asset types...")
    asset_types = extractor.extract_flexible_asset_types()
    display_data_sample(asset_types, "Flexible Asset Types")
    
    # Extract domains
    logger.info("Extracting domains...")
    domains = extractor.extract_domains()
    display_data_sample(domains, "Domains")
    
    # Extract vendors
    logger.info("Extracting vendors...")
    vendors = extractor.extract_vendors()
    display_data_sample(vendors, "Vendors")
    
    # Extract configuration types
    logger.info("Extracting configuration types...")
    config_types_data = extractor.extract_configuration_types()
    display_data_sample(config_types_data, "Configuration Types")
    
    # Extract Configuration Items
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
        logger.info("Extracting {}...".format(type_name))
        try:
            configs = extractor.extract_configurations(
                config_type_id=int(type_id), 
                config_type_name=type_name
            )
            display_data_sample(configs, "{}".format(type_name.replace('_', ' ').title()))
            logger.info(f"Successfully extracted {len(configs)} {type_name}")
        except Exception as e:
            logger.error(f"Error extracting {type_name}: {str(e)}")
    
    # Extract Flexible Assets
    flexible_asset_types = {
        '43489': 'voice_pbx',
        '43822': 'wireless_networks',
        '43815': 'line_of_business_applications',
        '43816': 'email_systems',
        '39796': 'identity_services',
        '45360': 'backup_solutions',
        '44104': 'security_systems',
        '44090': 'licensing_renewals'
    }
    
    for type_id, type_name in flexible_asset_types.items():
        logger.info("Extracting {}...".format(type_name))
        try:
            assets = extractor.extract_flexible_assets(
                asset_type_id=int(type_id), 
                asset_type_name=type_name
            )
            display_data_sample(assets, "{}".format(type_name.replace('_', ' ').title()))
            logger.info(f"Successfully extracted {len(assets)} {type_name}")
        except Exception as e:
            logger.error("Could not extract {} assets: {}".format(type_name, str(e)))
    
    # Print summary of extracted data
    print("\nExtraction Summary:")
    print("Organizations: {}".format(len(organizations)))
    print("Flexible Asset Types: {}".format(len(asset_types)))
    print("Configuration Types: {}".format(len(config_types_data)))
    print("Domains: {}".format(len(domains)))
    print("Vendors: {}".format(len(vendors)))
    
    for type_name in config_types.values():
        try:
            data_path = os.path.join(output_dir, "configurations_{}.csv".format(type_name))
            if os.path.exists(data_path):
                df = pd.read_csv(data_path)
                print("{}: {}".format(type_name.replace('_', ' ').title(), len(df)))
        except Exception:
            pass
    
    for type_name in flexible_asset_types.values():
        try:
            data_path = os.path.join(output_dir, "flexible_assets_{}.csv".format(type_name))
            if os.path.exists(data_path):
                df = pd.read_csv(data_path)
                print("{}: {}".format(type_name.replace('_', ' ').title(), len(df)))
        except Exception:
            pass
    
    logger.info("Data extraction completed. Files saved to {}".format(output_dir))
    logger.info("You can find the extracted data in CSV and JSON formats in the output directory")

if __name__ == "__main__":
    main()