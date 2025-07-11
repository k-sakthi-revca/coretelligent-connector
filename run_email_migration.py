"""
Script to run the email migration process.
"""

import logging
import os
import sys

# Add the current directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from email_migrator import EmailMigrator


def main():
    """Main function to run the email migration."""
    # Set up basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting email migration process...")
    
    # Create output directory if it doesn't exist
    output_dir = "reports"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
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
    
    logger.info("Email migration completed. Total: %s, Successful: %s, Failed: %s", 
                total, successful, failed)
    logger.info("Report saved to: %s", migrator.report_file)


if __name__ == "__main__":
    main()