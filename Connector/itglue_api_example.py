"""
Simple example script demonstrating direct usage of the ITGlue connector
"""
import os
import json
import logging
from itglue_connector import ITGlueConnector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('itglue_api_example')

def main():
    """
    Main function demonstrating direct usage of the ITGlue connector
    """
    # Get API key from environment variable or use the default one
    api_key = os.environ.get(
        'ITGLUE_API_KEY', 
        'ITG.005c32616f608910a8f1dfa40a7bdf73.TaTMBpSXUsJFEKlcJE7BRFL2m-CN4KAJbntZ9iFxpb0SUwteUS3wDjJl4yhkgWpP'
    )
    
    logger.info("Initializing ITGlue connector")
    
    # Initialize the connector
    connector = ITGlueConnector(api_key)
    
    # Example 1: Get organizations
    logger.info("Example 1: Get organizations")
    organizations = connector.get_organizations()
    logger.info("Found {} organizations".format(len(organizations)))
    
    # Print the first organization (if available)
    if organizations:
        org = organizations[0]
        logger.info("First organization: {}".format(org.get('attributes', {}).get('name')))
    
    # Example 2: Get flexible asset types
    logger.info("Example 2: Get flexible asset types")
    asset_types = connector.get_flexible_asset_types()
    logger.info("Found {} flexible asset types".format(len(asset_types)))
    
    # Print the first few asset types
    for i, asset_type in enumerate(asset_types[:5]):
        logger.info("Asset type {}: {}".format(i+1, asset_type.get('attributes', {}).get('name')))
    
    # Example 3: Get configurations of a specific type (servers)
    logger.info("Example 3: Get server configurations")
    servers = connector.get_configurations(config_type_id=703409)
    logger.info("Found {} servers".format(len(servers)))
    
    # Example 4: Get flexible assets of a specific type (Voice/PBX)
    logger.info("Example 4: Get Voice/PBX flexible assets")
    voice_pbx = connector.get_flexible_assets(asset_type_id=43489)
    logger.info("Found {} Voice/PBX assets".format(len(voice_pbx)))
    
    # Example 5: Get domains
    logger.info("Example 5: Get domains")
    domains = connector.get_domains()
    logger.info("Found {} domains".format(len(domains)))
    
    # Example 6: Get attachments for a specific resource
    # Note: You need to provide a valid resource ID
    if voice_pbx:
        resource_id = voice_pbx[0]['id']
        logger.info("Example 6: Get attachments for Voice/PBX asset {}".format(resource_id))
        attachments = connector.get_attachments('flexible_assets', int(resource_id))
        logger.info("Found {} attachments".format(len(attachments)))
    
    logger.info("Examples completed")

if __name__ == "__main__":
    main()