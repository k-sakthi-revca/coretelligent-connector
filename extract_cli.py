"""
Command-line interface for extracting data from ITGlue
"""
import os
import sys
import argparse
import logging
from itglue_data_extractor import ITGlueDataExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('extract_cli')

# Define configuration type mappings
CONFIG_TYPES = {
    'servers': 703409,
    'workstations': 328008,
    'laptops': 122621,
    'desktops': 328015,
    'network_devices': 124327,
    'printers': 122627,
    'mobile_devices': 328022,
    'storage_devices': 124328,
    'application_servers': 124324,
    'uc_equipment': 124329,
    'ssl_certificates': 328026,
    'ups': 328029
}

# Define flexible asset type mappings
# Note: These IDs may vary between ITGlue instances
ASSET_TYPES = {
    'voice_pbx': 43489,
    'wireless_networks': 43822,
    'business_applications': 43815,
    'email_systems': 43816,
    'identity_services': 39796,
    'backup_solutions': 45360,
    'security_systems': 44104,
    'licensing_renewals': 44090
}

def main():
    """
    Main function to parse arguments and run the extraction
    """
    parser = argparse.ArgumentParser(description='Extract data from ITGlue')
    
    # API key argument
    parser.add_argument('--api-key', help='ITGlue API key (can also be set via ITGLUE_API_KEY environment variable)')
    
    # Output directory
    parser.add_argument('--output-dir', default='extracted_data', help='Directory to save extracted data')
    
    # Data type arguments
    parser.add_argument('--all', action='store_true', help='Extract all data types')
    parser.add_argument('--organizations', action='store_true', help='Extract organizations')
    parser.add_argument('--domains', action='store_true', help='Extract domains')
    parser.add_argument('--asset-types', action='store_true', help='Extract flexible asset types')
    
    # Configuration types
    parser.add_argument('--configs', nargs='*', choices=list(CONFIG_TYPES.keys()) + ['all'], 
                        help='Extract configurations of specified types')
    
    # Flexible asset types
    parser.add_argument('--assets', nargs='*', choices=list(ASSET_TYPES.keys()) + ['all'], 
                        help='Extract flexible assets of specified types')
    
    args = parser.parse_args()
    
    # Get API key from arguments or environment variable
    api_key = args.api_key or os.environ.get('ITGLUE_API_KEY')
    
    if not api_key:
        logger.error("API key not provided. Use --api-key or set ITGLUE_API_KEY environment variable.")
        sys.exit(1)
    
    # Initialize the data extractor
    extractor = ITGlueDataExtractor(api_key, output_dir=args.output_dir)
    
    # Check if any extraction option was selected
    extraction_requested = (args.all or args.organizations or args.domains or 
                           args.asset_types or args.configs or args.assets)
    
    if not extraction_requested:
        logger.error("No data types specified for extraction. Use --all or specify data types.")
        parser.print_help()
        sys.exit(1)
    
    # Extract all data if requested
    if args.all:
        logger.info("Extracting all data types")
        extractor.extract_all_data()
        return
    
    # Extract organizations if requested
    if args.organizations:
        logger.info("Extracting organizations")
        organizations = extractor.extract_organizations()
        logger.info("Extracted {} organizations".format(len(organizations)))
    
    # Extract domains if requested
    if args.domains:
        logger.info("Extracting domains")
        domains = extractor.extract_domains()
        logger.info("Extracted {} domains".format(len(domains)))
    
    # Extract flexible asset types if requested
    if args.asset_types:
        logger.info("Extracting flexible asset types")
        asset_types = extractor.extract_flexible_asset_types()
        logger.info("Extracted {} flexible asset types".format(len(asset_types)))
    
    # Extract configurations if requested
    if args.configs:
        if 'all' in args.configs:
            config_types = CONFIG_TYPES.items()
        else:
            config_types = {k: CONFIG_TYPES[k] for k in args.configs}.items()
        
        for config_name, config_id in config_types:
            logger.info("Extracting {}".format(config_name))
            configs = extractor.extract_configurations(
                config_type_id=config_id,
                config_type_name=config_name
            )
            logger.info("Extracted {} {}".format(len(configs), config_name))
    
    # Extract flexible assets if requested
    if args.assets:
        if 'all' in args.assets:
            asset_types = ASSET_TYPES.items()
        else:
            asset_types = {k: ASSET_TYPES[k] for k in args.assets}.items()
        
        for asset_name, asset_id in asset_types:
            logger.info("Extracting {}".format(asset_name))
            try:
                assets = extractor.extract_flexible_assets(
                    asset_type_id=asset_id,
                    asset_type_name=asset_name
                )
                logger.info("Extracted {} {}".format(len(assets), asset_name))
            except Exception as e:
                logger.error("Error extracting {}: {}".format(asset_name, str(e)))
    
    logger.info("Data extraction completed. Files saved to {}".format(args.output_dir))

if __name__ == "__main__":
    main()