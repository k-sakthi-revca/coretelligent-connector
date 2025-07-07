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
    output_dir = "extracted_data_sample"
    
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
    
    # Extract servers
    logger.info("Extracting servers...")
    servers = extractor.extract_configurations(
        config_type_id=703409, 
        config_type_name="servers"
    )
    display_data_sample(servers, "Servers")
    
    # Extract network devices
    logger.info("Extracting network devices...")
    network_devices = extractor.extract_configurations(
        config_type_id=124327, 
        config_type_name="network_devices"
    )
    display_data_sample(network_devices, "Network Devices")
    
    # Extract Voice/PBX flexible assets if available
    logger.info("Extracting Voice/PBX assets...")
    try:
        voice_pbx = extractor.extract_flexible_assets(
            asset_type_id=43489, 
            asset_type_name="voice_pbx"
        )
        display_data_sample(voice_pbx, "Voice/PBX Assets")
    except Exception as e:
        logger.warning("Could not extract Voice/PBX assets: {}".format(str(e)))
    
    # Print summary of extracted data
    print("\nExtraction Summary:")
    print("Organizations: {}".format(len(organizations)))
    print("Flexible Asset Types: {}".format(len(asset_types)))
    print("Domains: {}".format(len(domains)))
    print("Servers: {}".format(len(servers)))
    print("Network Devices: {}".format(len(network_devices)))
    
    logger.info("Data extraction completed. Files saved to {}".format(output_dir))
    logger.info("You can find the extracted data in CSV and JSON formats in the output directory")

if __name__ == "__main__":
    main()