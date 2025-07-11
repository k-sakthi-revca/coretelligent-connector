"""
Script to run the LoB applications migration process.
"""

import logging
import os
from datetime import datetime

from utils.logging_utils import setup_logging, get_timestamped_log_file
from migrators.lob_applications_migrator import LoBApplicationsMigrator


def main():
    """Main function to run the LoB applications migration."""
    # Set up logging
    log_file = get_timestamped_log_file("lob_applications_migration")
    setup_logging(log_level="INFO", log_file=log_file)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting LoB applications migration process...")
    
    # Create output directory if it doesn't exist
    output_dir = "reports"
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize LoB applications migrator
    # Use mock data by default (set to False to use real API calls)
    use_mock_data = True
    migrator = LoBApplicationsMigrator(use_mock_data=use_mock_data)
    
    # Run the migration
    logger.info("Running LoB applications migration...")
    results, statistics = migrator.migrate_lob_applications()
    
    # Log completion
    total = statistics.get("total_applications", 0)
    successful = statistics.get("successful", 0)
    failed = statistics.get("failed", 0)
    
    logger.info("LoB applications migration completed. Total: {}, Successful: {}, Failed: {}".format(total, successful, failed))
    logger.info("Report saved to: {}".format(migrator.report_file))


if __name__ == "__main__":
    main()