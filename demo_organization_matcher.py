"""
Demo script for the organization matcher.
"""

import os
import logging
from datetime import datetime

from utils.logging_utils import setup_logging, get_timestamped_log_file
from utils.file_utils import load_json_file, load_servicenow_data
from matchers.organization_matcher import OrganizationMatcher
from reports.report_generator import ReportGenerator


def main():
    """Main function."""
    # Set up logging
    log_file = get_timestamped_log_file("organization_matcher")
    setup_logging(log_level="INFO", log_file=log_file)
    logger = logging.getLogger(__name__)
    
    # Create reports directory if it doesn't exist
    os.makedirs("reports", exist_ok=True)
    
    # Load IT Glue organization data
    logger.info("Loading IT Glue organization data...")
    itglue_orgs_path = "mock_itglue_organizations.json"
    itglue_orgs = load_json_file(itglue_orgs_path)
    
    if not itglue_orgs:
        logger.error("Failed to load IT Glue organization data")
        return
    
    # Load ServiceNow company data
    logger.info("Loading ServiceNow company data...")
    servicenow_companies_path = "mock_servicenow_companies.json"
    servicenow_companies = load_servicenow_data(servicenow_companies_path)
    
    if not servicenow_companies:
        logger.error("Failed to load ServiceNow company data")
        return
    
    # Load Site Summary data
    logger.info("Loading Site Summary data...")
    site_summaries_path = "mock_site_summaries.json"
    site_summaries = load_json_file(site_summaries_path)
    
    if not site_summaries:
        logger.warning("No Site Summary data found, CoreID matching will not be available")
        site_summaries = []
    
    # Initialize matcher
    logger.info("Initializing organization matcher...")
    matcher = OrganizationMatcher()
    
    # Match organizations
    logger.info("Matching organizations...")
    matches, quality_issues = matcher.match_organizations(
        itglue_orgs, servicenow_companies, site_summaries
    )
    
    # Generate statistics
    stats = matcher.generate_matching_statistics(matches)
    
    # Initialize report generator
    report_generator = ReportGenerator(output_dir="reports")
    
    # Print report summary
    report_generator.print_organization_report_summary(matches, quality_issues, stats)
    
    # Generate report file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"organization_migration_report_{timestamp}.json"
    report_path = report_generator.generate_organization_report(
        matches, quality_issues, stats, report_file
    )
    
    logger.info(f"Organization matching demo completed. Report saved to {report_path}")


if __name__ == "__main__":
    main()