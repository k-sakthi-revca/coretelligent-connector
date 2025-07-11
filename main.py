"""
Main script for the IT Glue to ServiceNow migration demo.
"""

import os
import sys
import logging
import argparse
from datetime import datetime

from utils.logging_utils import setup_logging, get_timestamped_log_file
from utils.file_utils import load_itglue_assets, load_json_file, load_servicenow_data
from matchers.organization_matcher import OrganizationMatcher
from matchers.virtualization_matcher import VirtualizationMatcher
from reports.report_generator import ReportGenerator


def run_organization_matcher(args):
    """
    Run the organization matcher.
    
    Args:
        args: Command line arguments
    """
    logger = logging.getLogger(__name__)
    logger.info("Running organization matcher...")
    
    # Load IT Glue organization data
    logger.info("Loading IT Glue organization data...")
    itglue_orgs_path = args.itglue_orgs or "mock_itglue_organizations.json"
    itglue_orgs = load_json_file(itglue_orgs_path)
    
    if not itglue_orgs:
        logger.error("Failed to load IT Glue organization data")
        return
    
    # Load ServiceNow company data
    logger.info("Loading ServiceNow company data...")
    servicenow_companies_path = args.servicenow_companies or "mock_servicenow_companies.json"
    servicenow_companies = load_servicenow_data(servicenow_companies_path)
    
    if not servicenow_companies:
        logger.error("Failed to load ServiceNow company data")
        return
    
    # Load Site Summary data
    logger.info("Loading Site Summary data...")
    site_summaries_path = args.site_summaries or "mock_site_summaries.json"
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
    report_generator = ReportGenerator(output_dir=args.output_dir)
    
    # Print report summary
    if not args.quiet:
        report_generator.print_organization_report_summary(matches, quality_issues, stats)
    
    # Generate report file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = args.report_file or f"organization_migration_report_{timestamp}.json"
    report_path = report_generator.generate_organization_report(
        matches, quality_issues, stats, report_file
    )
    
    logger.info(f"Organization matching completed. Report saved to {report_path}")


def run_virtualization_matcher(args):
    """
    Run the virtualization matcher.
    
    Args:
        args: Command line arguments
    """
    logger = logging.getLogger(__name__)
    logger.info("Running virtualization matcher...")
    
    # Load virtualization data
    logger.info("Loading virtualization data...")
    virtualization_data_path = args.itglue_assets or os.path.join("data", "virtualization", "virtualization_data.json")
    virtualization_data = load_itglue_assets(virtualization_data_path)
    
    if not virtualization_data:
        logger.error("Failed to load virtualization data")
        return
    
    # Load ServiceNow server data
    logger.info("Loading ServiceNow server data...")
    servicenow_servers_path = args.servicenow_servers or "mock_servicenow_servers.json"
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
    report_generator = ReportGenerator(output_dir=args.output_dir)
    
    # Print report summary
    if not args.quiet:
        report_generator.print_virtualization_report_summary(matches, quality_issues, stats)
    
    # Generate report file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = args.report_file or f"virtualization_migration_report_{timestamp}.json"
    report_path = report_generator.generate_virtualization_report(
        matches, quality_issues, stats, report_file
    )
    
    logger.info(f"Virtualization matching completed. Report saved to {report_path}")


def main():
    """Main function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="IT Glue to ServiceNow Migration Demo")
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Organization matcher command
    org_parser = subparsers.add_parser("organizations", help="Match organizations")
    org_parser.add_argument("--itglue-orgs", help="Path to IT Glue organizations JSON file")
    org_parser.add_argument("--servicenow-companies", help="Path to ServiceNow companies JSON file")
    org_parser.add_argument("--site-summaries", help="Path to Site Summary JSON file")
    org_parser.add_argument("--output-dir", default="reports", help="Output directory for reports")
    org_parser.add_argument("--report-file", help="Report file name")
    org_parser.add_argument("--log-file", help="Log file path")
    org_parser.add_argument("--log-level", default="INFO", help="Logging level")
    org_parser.add_argument("--quiet", action="store_true", help="Suppress console output")
    
    # Virtualization matcher command
    virt_parser = subparsers.add_parser("virtualization", help="Match virtualization assets")
    virt_parser.add_argument("--itglue-assets", help="Path to IT Glue virtualization assets JSON file")
    virt_parser.add_argument("--servicenow-servers", help="Path to ServiceNow servers JSON file")
    virt_parser.add_argument("--output-dir", default="reports", help="Output directory for reports")
    virt_parser.add_argument("--report-file", help="Report file name")
    virt_parser.add_argument("--log-file", help="Log file path")
    virt_parser.add_argument("--log-level", default="INFO", help="Logging level")
    virt_parser.add_argument("--quiet", action="store_true", help="Suppress console output")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set up logging
    log_file = args.log_file if hasattr(args, 'log_file') and args.log_file else get_timestamped_log_file("migration")
    log_level = args.log_level if hasattr(args, 'log_level') else "INFO"
    setup_logging(log_level=log_level, log_file=log_file)
    
    # Create output directory if it doesn't exist
    output_dir = args.output_dir if hasattr(args, 'output_dir') else "reports"
    os.makedirs(output_dir, exist_ok=True)
    
    # Run the appropriate command
    if args.command == "organizations":
        run_organization_matcher(args)
    elif args.command == "virtualization":
        run_virtualization_matcher(args)
    else:
        # If no command specified, show help
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()