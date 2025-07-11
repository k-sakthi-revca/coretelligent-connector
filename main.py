#!/usr/bin/env python3
"""
IT Glue to ServiceNow Migration Demo
Main entry point for the migration demo.
"""

import os
import sys
import argparse
import logging
from datetime import datetime

from organization_migrator import OrganizationMigrator
from utils import setup_logging, print_header, print_subheader, print_success, print_error, print_info
from config import config


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="IT Glue to ServiceNow Migration Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run the migration demo with mock data
  python main.py
  
  # Run with live API (requires IT Glue API key)
  python main.py --live-api
  
  # Run with custom config file
  python main.py --config custom_config.yaml
  
  # Run with debug logging
  python main.py --log-level DEBUG
        """
    )
    
    # API options
    parser.add_argument(
        "--live-api", 
        action="store_true",
        help="Use live IT Glue API instead of mock data"
    )
    
    # Configuration options
    parser.add_argument(
        "--config", 
        type=str,
        default="config.yaml",
        help="Configuration file path (default: config.yaml)"
    )
    
    # Logging options
    parser.add_argument(
        "--log-level", 
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    parser.add_argument(
        "--log-file", 
        type=str,
        default=f"logs/migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
        help="Log file path (default: logs/migration_YYYYMMDD_HHMMSS.log)"
    )
    
    return parser.parse_args()


def main():
    """Main function."""
    # Parse arguments
    args = parse_arguments()
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    logger = logging.getLogger(__name__)
    
    try:
        # Print welcome message
        print_header("IT Glue to ServiceNow Migration Demo")
        
        # Determine if we're using mock data or live API
        use_mock_data = not args.live_api
        
        if use_mock_data:
            print_info("This demo uses mock data to simulate both IT Glue and ServiceNow.")
            print_info("No real API calls will be made.")
        else:
            print_info("This demo will connect to the IT Glue API using your credentials.")
            print_info("ServiceNow will still be simulated with mock data.")
        
        # Create migrator
        migrator = OrganizationMigrator(use_mock_data=use_mock_data)
        
        # Run migration
        print_subheader("Starting Migration")
        results, statistics = migrator.migrate_organizations()
        
        # Print completion message
        total = statistics["total_organizations"]
        successful = statistics["successful"]
        
        if total > 0:
            print_success(f"Migration completed: {successful}/{total} organizations successfully migrated")
        else:
            print_info("No organizations were found to migrate. Please check your data source.")
        
        return 0
        
    except KeyboardInterrupt:
        print_error("\nMigration interrupted by user")
        logger.info("Migration interrupted by user")
        return 1
        
    except Exception as e:
        print_error(f"\nUnexpected error: {str(e)}")
        logger.exception("Unexpected error during migration")
        return 1


if __name__ == "__main__":
    sys.exit(main())