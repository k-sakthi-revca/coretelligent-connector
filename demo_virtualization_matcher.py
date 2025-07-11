"""
Demo script for the virtualization matcher.
"""

import os
import logging
from datetime import datetime

from utils.logging_utils import setup_logging, get_timestamped_log_file
from utils.file_utils import load_itglue_assets, load_servicenow_data
from matchers.virtualization_matcher import VirtualizationMatcher
from reports.report_generator import ReportGenerator


def main():
    """Main function."""
    # Set up logging
    log_file = get_timestamped_log_file("virtualization_matcher")
    setup_logging(log_level="INFO", log_file=log_file)
    logger = logging.getLogger(__name__)
    
    # Create reports directory if it doesn't exist
    os.makedirs("reports", exist_ok=True)
    
    # Load virtualization data
    logger.info("Loading virtualization data...")
    virtualization_data_path = os.path.join("data", "virtualization", "virtualization_data.json")
    virtualization_data = load_itglue_assets(virtualization_data_path)
    
    if not virtualization_data:
        logger.error("Failed to load virtualization data")
        return
    
    # Load ServiceNow server data
    logger.info("Loading ServiceNow server data...")
    servicenow_servers_path = "mock_servicenow_servers.json"
    servicenow_servers = load_servicenow_data(servicenow_servers_path)
    
    if not servicenow_servers:
        logger.error("Failed to load ServiceNow server data")
        return
    
    # Initialize matcher
    logger.info("Initializing virtualization matcher...")
    matcher = VirtualizationMatcher()
    
    # Match virtualization assets
    logger.info("Matching virtualization assets...")
    matches, quality_issues = matcher.match_virtualization_assets(
        virtualization_data["data"], servicenow_servers
    )
    
    # Generate statistics
    stats = matcher.generate_matching_statistics(matches)
    
    # Initialize report generator
    report_generator = ReportGenerator(output_dir="reports")
    
    # Print report summary
    report_generator.print_virtualization_report_summary(matches, quality_issues, stats)
    
    # Generate report file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"virtualization_migration_report_{timestamp}.json"
    report_path = report_generator.generate_virtualization_report(
        matches, quality_issues, stats, report_file
    )
    
    logger.info(f"Virtualization matching demo completed. Report saved to {report_path}")


if __name__ == "__main__":
    main()