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
from site_summary_matcher import SiteSummaryMatcher
from site_summary_migrator import SiteSummaryMigrator
from voice_pbx_matcher import VoicePBXMatcher
from voice_pbx_migrator import VoicePBXMigrator
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


def run_site_summary_matcher(args):
    """
    Run the site summary matcher.
    
    Args:
        args: Command line arguments
    """
    logger = logging.getLogger(__name__)
    logger.info("Running site summary matcher...")
    
    # Load IT Glue Site Summary data
    logger.info("Loading IT Glue Site Summary data...")
    itglue_sites_path = args.itglue_sites or os.path.join("data", "Site-Summary", "site-summary.json")
    itglue_sites = load_json_file(itglue_sites_path)
    
    if not itglue_sites:
        logger.error("Failed to load IT Glue Site Summary data")
        return
    
    # Load ServiceNow site data
    logger.info("Loading ServiceNow site data...")
    servicenow_sites_path = args.servicenow_sites or "mock_servicenow_sites.json"
    servicenow_sites = load_servicenow_data(servicenow_sites_path)
    
    if not servicenow_sites:
        logger.warning("No ServiceNow site data found, will create new records")
        servicenow_sites = []
    
    # Initialize matcher
    logger.info("Initializing site summary matcher...")
    matcher = SiteSummaryMatcher()
    
    # Match site summaries
    logger.info("Matching site summaries...")
    matches, quality_issues = matcher.match_site_summaries(
        itglue_sites, servicenow_sites
    )
    
    # Generate statistics
    stats = matcher.generate_matching_statistics(matches)
    
    # Initialize report generator
    report_generator = ReportGenerator(output_dir=args.output_dir)
    
    # Print report summary
    if not args.quiet:
        # For now, we'll just print a simple summary
        print(f"\n=== Site Summary Matching Results ===")
        print(f"Total matches: {len(matches)}")
        print(f"Data quality issues: {len(quality_issues)}")
        
        # Count by match type
        match_types = {}
        for match in matches:
            match_type = match.match_type
            if match_type not in match_types:
                match_types[match_type] = 0
            match_types[match_type] += 1
        
        print("\nMatch Types:")
        for match_type, count in match_types.items():
            print(f"  {match_type}: {count} ({count/len(matches)*100:.1f}%)")
    
    # Generate report file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = args.report_file or f"site_summary_migration_report_{timestamp}.json"
    
    # Save match results
    os.makedirs(args.output_dir, exist_ok=True)
    report_path = os.path.join(args.output_dir, report_file)
    
    with open(report_path, 'w') as f:
        import json
        json.dump({
            "matches": [match.__dict__ for match in matches],
            "quality_issues": [issue.__dict__ for issue in quality_issues],
            "statistics": stats
        }, f, indent=2)
    
    logger.info(f"Site Summary matching completed. Report saved to {report_path}")
    
    # Perform migration if requested
    if args.migrate:
        logger.info("Migrating site summaries...")
        
        # Initialize migrator
        migrator = SiteSummaryMigrator(dry_run=args.dry_run)
        
        # Migrate site summaries
        migration_results = migrator.migrate_site_summaries(
            itglue_sites, matches, servicenow_sites
        )
        
        # Generate migration report
        migration_report = migrator.generate_migration_report(migration_results)
        
        # Print migration summary
        if not args.quiet:
            print(f"\n=== Site Summary Migration Results ===")
            print(f"Total migrations: {len(migration_results)}")
            print(f"Successful: {sum(1 for r in migration_results if r.success)}")
            print(f"Failed: {sum(1 for r in migration_results if not r.success)}")
        
        # Save migration results
        migration_report_path = os.path.join(args.output_dir, f"site_summary_migration_details_{timestamp}.json")
        with open(migration_report_path, 'w') as f:
            import json
            json.dump({
                "results": [result.__dict__ for result in migration_results],
                "report": migration_report
            }, f, indent=2)
        
        logger.info(f"Site Summary migration completed. Report saved to {migration_report_path}")


def run_voice_pbx_matcher(args):
    """
    Run the voice PBX matcher.
    
    Args:
        args: Command line arguments
    """
    logger = logging.getLogger(__name__)
    logger.info("Running voice PBX matcher...")
    
    # Load IT Glue Voice PBX data
    logger.info("Loading IT Glue Voice PBX data...")
    itglue_assets_path = args.itglue_assets or os.path.join("data", "Voice-PBX", "voice-pbx.json")
    itglue_assets = load_json_file(itglue_assets_path)
    
    if not itglue_assets:
        logger.error("Failed to load IT Glue Voice PBX data")
        return
    
    # Load ServiceNow voice gateway data
    logger.info("Loading ServiceNow voice gateway data...")
    servicenow_gateways_path = args.servicenow_gateways or "mock_servicenow_voice_gateways.json"
    servicenow_gateways = load_servicenow_data(servicenow_gateways_path)
    
    if not servicenow_gateways:
        logger.warning("No ServiceNow voice gateway data found, will create new records")
        servicenow_gateways = []
    
    # Initialize matcher
    logger.info("Initializing voice PBX matcher...")
    matcher = VoicePBXMatcher()
    
    # Match voice PBX assets
    logger.info("Matching voice PBX assets...")
    matches, quality_issues = matcher.match_voice_pbx_assets(
        itglue_assets, servicenow_gateways
    )
    
    # Generate statistics
    stats = matcher.generate_matching_statistics(matches)
    
    # Initialize report generator
    report_generator = ReportGenerator(output_dir=args.output_dir)
    
    # Print report summary
    if not args.quiet:
        # For now, we'll just print a simple summary
        print(f"\n=== Voice PBX Matching Results ===")
        print(f"Total matches: {len(matches)}")
        print(f"Data quality issues: {len(quality_issues)}")
        
        # Count by match type
        match_types = {}
        for match in matches:
            match_type = match.match_type
            if match_type not in match_types:
                match_types[match_type] = 0
            match_types[match_type] += 1
        
        print("\nMatch Types:")
        for match_type, count in match_types.items():
            print(f"  {match_type}: {count} ({count/len(matches)*100:.1f}%)")
    
    # Generate report file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = args.report_file or f"voice_pbx_migration_report_{timestamp}.json"
    
    # Save match results
    os.makedirs(args.output_dir, exist_ok=True)
    report_path = os.path.join(args.output_dir, report_file)
    
    with open(report_path, 'w') as f:
        import json
        json.dump({
            "matches": [match.__dict__ for match in matches],
            "quality_issues": [issue.__dict__ for issue in quality_issues],
            "statistics": stats
        }, f, indent=2)
    
    logger.info(f"Voice PBX matching completed. Report saved to {report_path}")
    
    # Perform migration if requested
    if args.migrate:
        logger.info("Migrating voice PBX assets...")
        
        # Initialize migrator
        migrator = VoicePBXMigrator(dry_run=args.dry_run)
        
        # Migrate voice PBX assets
        migration_results = migrator.migrate_voice_pbx_assets(
            itglue_assets, matches, servicenow_gateways
        )
        
        # Generate migration report
        migration_report = migrator.generate_migration_report(migration_results)
        
        # Print migration summary
        if not args.quiet:
            print(f"\n=== Voice PBX Migration Results ===")
            print(f"Total migrations: {len(migration_results)}")
            print(f"Successful: {sum(1 for r in migration_results if r.success)}")
            print(f"Failed: {sum(1 for r in migration_results if not r.success)}")
        
        # Save migration results
        migration_report_path = os.path.join(args.output_dir, f"voice_pbx_migration_details_{timestamp}.json")
        with open(migration_report_path, 'w') as f:
            import json
            json.dump({
                "results": [result.__dict__ for result in migration_results],
                "report": migration_report
            }, f, indent=2)
        
        logger.info(f"Voice PBX migration completed. Report saved to {migration_report_path}")


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
    
    # Site Summary matcher command
    site_parser = subparsers.add_parser("site-summary", help="Match site summary assets")
    site_parser.add_argument("--itglue-sites", help="Path to IT Glue Site Summary JSON file")
    site_parser.add_argument("--servicenow-sites", help="Path to ServiceNow sites JSON file")
    site_parser.add_argument("--output-dir", default="reports", help="Output directory for reports")
    site_parser.add_argument("--report-file", help="Report file name")
    site_parser.add_argument("--log-file", help="Log file path")
    site_parser.add_argument("--log-level", default="INFO", help="Logging level")
    site_parser.add_argument("--quiet", action="store_true", help="Suppress console output")
    site_parser.add_argument("--migrate", action="store_true", help="Perform migration after matching")
    site_parser.add_argument("--dry-run", action="store_true", help="Perform a dry run (no actual migration)")
    
    # Voice PBX matcher command
    voice_parser = subparsers.add_parser("voice-pbx", help="Match voice PBX assets")
    voice_parser.add_argument("--itglue-assets", help="Path to IT Glue Voice PBX JSON file")
    voice_parser.add_argument("--servicenow-gateways", help="Path to ServiceNow voice gateways JSON file")
    voice_parser.add_argument("--output-dir", default="reports", help="Output directory for reports")
    voice_parser.add_argument("--report-file", help="Report file name")
    voice_parser.add_argument("--log-file", help="Log file path")
    voice_parser.add_argument("--log-level", default="INFO", help="Logging level")
    voice_parser.add_argument("--quiet", action="store_true", help="Suppress console output")
    voice_parser.add_argument("--migrate", action="store_true", help="Perform migration after matching")
    voice_parser.add_argument("--dry-run", action="store_true", help="Perform a dry run (no actual migration)")
    
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
    elif args.command == "site-summary":
        run_site_summary_matcher(args)
    elif args.command == "voice-pbx":
        run_voice_pbx_matcher(args)
    else:
        # If no command specified, show help
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()