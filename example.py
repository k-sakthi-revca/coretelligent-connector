"""
Example script demonstrating how to use the ITGlue data extraction tools
"""
import os
import logging
from itglue_data_extractor import ITGlueDataExtractor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('example')

def main():
    """
    Main function demonstrating the usage of the ITGlue data extraction tools
    """
    # Get API key from environment variable or use the default one
    api_key = os.environ.get(
        'ITGLUE_API_KEY', 
        'ITG.005c32616f608910a8f1dfa40a7bdf73.TaTMBpSXUsJFEKlcJE7BRFL2m-CN4KAJbntZ9iFxpb0SUwteUS3wDjJl4yhkgWpP'
    )
    
    logger.info("Initializing ITGlue data extractor")
    
    # Initialize the data extractor
    extractor = ITGlueDataExtractor(api_key)
    
    # Example 1: Extract all data
    logger.info("Example 1: Extract all data")
    # Uncomment the following line to run this example
    # extractor.extract_all_data()
    
    # Example 2: Extract specific data types
    logger.info("Example 2: Extract specific data types")
    
    # Extract organizations
    organizations = extractor.extract_organizations()
    logger.info("Extracted {} organizations".format(len(organizations)))
    
    # Extract flexible asset types
    asset_types = extractor.extract_flexible_asset_types()
    logger.info("Extracted {} flexible asset types".format(len(asset_types)))
    
    # Extract domains
    domains = extractor.extract_domains()
    logger.info("Extracted {} domains".format(len(domains)))
    
    # Extract servers
    servers = extractor.extract_configurations(
        config_type_id=703409, 
        config_type_name="servers"
    )
    logger.info("Extracted {} servers".format(len(servers)))
    
    # Extract network devices
    network_devices = extractor.extract_configurations(
        config_type_id=124327, 
        config_type_name="network_devices"
    )
    logger.info("Extracted {} network devices".format(len(network_devices)))
    
    # Extract Voice/PBX flexible assets
    voice_pbx = extractor.extract_flexible_assets(
        asset_type_id=43489, 
        asset_type_name="voice_pbx"
    )
    logger.info("Extracted {} Voice/PBX assets".format(len(voice_pbx)))
    
    logger.info("Examples completed")

if __name__ == "__main__":
    main()