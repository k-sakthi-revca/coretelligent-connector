"""
Script to run the email migration process.
"""

import logging
import os
from datetime import datetime

from utils.logging_utils import setup_logging, get_timestamped_log_file
from migrators.email_migrator import EmailMigrator


def main():
    """Main function to run the email migration."""
    # Set up logging
    log_file = get_timestamped_log_file("email_migration")
    setup_logging(log_level="INFO", log_file=log_file)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting email migration process...")
    
    # Create output directory if it doesn't exist
    output_dir = "reports"
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize email migrator
    # Use mock data by default (set to False to use real API calls)
    use_mock_data = True
    migrator = EmailMigrator(use_mock_data=use_mock_data)
    
    # Run the migration
    logger.info("Running email migration...")
    results, statistics = migrator.migrate_emails()
    
    # Log completion
    total = statistics.get("total_emails", 0)
    successful = statistics.get("successful", 0)
    failed = statistics.get("failed", 0)
    
    logger.info("Email migration completed. Total: {}, Successful: {}, Failed: {}".format(total, successful, failed))
    logger.info("Report saved to: {}".format(migrator.report_file))


if __name__ == "__main__":
    main()