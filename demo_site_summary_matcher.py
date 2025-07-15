#!/usr/bin/env python3
"""
Demo script for Site Summary migration.
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, List, Any

from site_summary_matcher import SiteSummaryMatcher
from site_summary_migrator import SiteSummaryMigrator
from config import config


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def load_json_file(file_path: str) -> List[Dict]:
    """
    Load JSON data from file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Loaded JSON data
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Failed to load JSON file {file_path}: {e}")
        return []


def save_json_file(file_path: str, data: Any) -> bool:
    """
    Save data to JSON file.
    
    Args:
        file_path: Path to JSON file
        data: Data to save
        
    Returns:
        True if successful, False otherwise
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logging.error(f"Failed to save JSON file {file_path}: {e}")
        return False


def print_match_results(matches, quality_issues):
    """
    Print match results in a readable format.
    
    Args:
        matches: List of match results
        quality_issues: List of data quality issues
    """
    print("\n=== Site Summary Matching Results ===")
    print(f"Total matches: {len(matches)}")
    
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
    
    # Count by recommended action
    actions = {}
    for match in matches:
        action = match.recommended_action
        if action not in actions:
            actions[action] = 0
        actions[action] += 1
    
    print("\nRecommended Actions:")
    for action, count in actions.items():
        print(f"  {action}: {count} ({count/len(matches)*100:.1f}%)")
    
    # Count by data quality
    quality = {}
    for match in matches:
        quality_label = match.data_quality
        if quality_label not in quality:
            quality[quality_label] = 0
        quality[quality_label] += 1
    
    print("\nData Quality:")
    for quality_label, count in quality.items():
        print(f"  {quality_label}: {count} ({count/len(matches)*100:.1f}%)")
    
    # Print quality issues
    if quality_issues:
        print(f"\nData Quality Issues ({len(quality_issues)}):")
        for issue in quality_issues[:5]:  # Show only first 5 issues
            print(f"  {issue.site_name} ({issue.organization_name}): {issue.issue_type} - {issue.description}")
        
        if len(quality_issues) > 5:
            print(f"  ... and {len(quality_issues) - 5} more issues")


def print_migration_results(results):
    """
    Print migration results in a readable format.
    
    Args:
        results: List of migration results
    """
    print("\n=== Site Summary Migration Results ===")
    print(f"Total migrations: {len(results)}")
    
    # Count by action
    actions = {}
    for result in results:
        action = result.action
        if action not in actions:
            actions[action] = 0
        actions[action] += 1
    
    print("\nActions:")
    for action, count in actions.items():
        print(f"  {action}: {count} ({count/len(results)*100:.1f}%)")
    
    # Count success/failure
    success_count = sum(1 for r in results if r.success)
    failure_count = len(results) - success_count
    
    print(f"\nSuccess: {success_count} ({success_count/len(results)*100:.1f}%)")
    print(f"Failure: {failure_count} ({failure_count/len(results)*100:.1f}%)")
    
    # Print some examples
    if results:
        print("\nExample Results:")
        for result in results[:5]:  # Show only first 5 results
            status = "✅" if result.success else "❌"
            print(f"  {status} {result.itglue_name}: {result.action} - {result.message}")
        
        if len(results) > 5:
            print(f"  ... and {len(results) - 5} more results")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Demo Site Summary Matcher')
    parser.add_argument('--itglue-sites', default='data/Site-Summary/site-summary.json',
                        help='Path to IT Glue Site Summary JSON file')
    parser.add_argument('--servicenow-sites', default='mock_servicenow_sites.json',
                        help='Path to ServiceNow sites JSON file')
    parser.add_argument('--output-dir', default='reports',
                        help='Output directory for reports')
    parser.add_argument('--dry-run', action='store_true',
                        help='Perform a dry run (no actual migration)')
    parser.add_argument('--migrate', action='store_true',
                        help='Perform migration after matching')
    args = parser.parse_args()
    
    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Load configuration
    config.load_config()
    
    # Load IT Glue Site Summary data
    logger.info("Loading IT Glue Site Summary data...")
    itglue_sites = load_json_file(args.itglue_sites)
    if not itglue_sites:
        logger.error("No IT Glue Site Summary data found")
        return 1
    
    # Load ServiceNow sites data
    logger.info("Loading ServiceNow sites data...")
    servicenow_sites = load_json_file(args.servicenow_sites)
    if not servicenow_sites:
        logger.warning("No ServiceNow sites data found, will create new records")
    
    # Create matcher
    matcher = SiteSummaryMatcher()
    
    # Match site summaries
    logger.info("Matching site summaries...")
    matches, quality_issues = matcher.match_site_summaries(itglue_sites, servicenow_sites)
    
    # Print match results
    print_match_results(matches, quality_issues)
    
    # Generate match statistics
    match_stats = matcher.generate_matching_statistics(matches)
    
    # Save match results
    os.makedirs(args.output_dir, exist_ok=True)
    save_json_file(os.path.join(args.output_dir, 'site_summary_matches.json'), 
                  [match.__dict__ for match in matches])
    save_json_file(os.path.join(args.output_dir, 'site_summary_quality_issues.json'), 
                  [issue.__dict__ for issue in quality_issues])
    save_json_file(os.path.join(args.output_dir, 'site_summary_match_stats.json'), match_stats)
    
    # Perform migration if requested
    if args.migrate:
        logger.info("Migrating site summaries...")
        
        # Create migrator
        migrator = SiteSummaryMigrator(dry_run=args.dry_run)
        
        # Migrate site summaries
        migration_results = migrator.migrate_site_summaries(itglue_sites, matches, servicenow_sites)
        
        # Print migration results
        print_migration_results(migration_results)
        
        # Generate migration report
        migration_report = migrator.generate_migration_report(migration_results)
        
        # Save migration results
        save_json_file(os.path.join(args.output_dir, 'site_summary_migration_results.json'), 
                      [result.__dict__ for result in migration_results])
        save_json_file(os.path.join(args.output_dir, 'site_summary_migration_report.json'), 
                      migration_report)
    
    logger.info("Done")
    return 0


if __name__ == '__main__':
    sys.exit(main())