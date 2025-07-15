#!/usr/bin/env python3
"""
Demo script for Voice PBX migration.
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, List, Any

from voice_pbx_matcher import VoicePBXMatcher
from voice_pbx_migrator import VoicePBXMigrator
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
    print("\n=== Voice PBX Matching Results ===")
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
            print(f"  {issue.asset_name} ({issue.organization_name}): {issue.issue_type} - {issue.description}")
        
        if len(quality_issues) > 5:
            print(f"  ... and {len(quality_issues) - 5} more issues")


def print_migration_results(results):
    """
    Print migration results in a readable format.
    
    Args:
        results: List of migration results
    """
    print("\n=== Voice PBX Migration Results ===")
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
    parser = argparse.ArgumentParser(description='Demo Voice PBX Matcher')
    parser.add_argument('--itglue-assets', default='data/Voice-PBX/voice-pbx.json',
                        help='Path to IT Glue Voice PBX JSON file')
    parser.add_argument('--servicenow-gateways', default='mock_servicenow_voice_gateways.json',
                        help='Path to ServiceNow voice gateways JSON file')
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
    
    # Load IT Glue Voice PBX data
    logger.info("Loading IT Glue Voice PBX data...")
    itglue_assets = load_json_file(args.itglue_assets)
    if not itglue_assets:
        logger.error("No IT Glue Voice PBX data found")
        return 1
    
    # Load ServiceNow voice gateways data
    logger.info("Loading ServiceNow voice gateways data...")
    servicenow_gateways = load_json_file(args.servicenow_gateways)
    if not servicenow_gateways:
        logger.warning("No ServiceNow voice gateways data found, will create new records")
    
    # Create matcher
    matcher = VoicePBXMatcher()
    
    # Match voice PBX assets
    logger.info("Matching voice PBX assets...")
    matches, quality_issues = matcher.match_voice_pbx_assets(itglue_assets, servicenow_gateways)
    
    # Print match results
    print_match_results(matches, quality_issues)
    
    # Generate match statistics
    match_stats = matcher.generate_matching_statistics(matches)
    
    # Save match results
    os.makedirs(args.output_dir, exist_ok=True)
    save_json_file(os.path.join(args.output_dir, 'voice_pbx_matches.json'), 
                  [match.__dict__ for match in matches])
    save_json_file(os.path.join(args.output_dir, 'voice_pbx_quality_issues.json'), 
                  [issue.__dict__ for issue in quality_issues])
    save_json_file(os.path.join(args.output_dir, 'voice_pbx_match_stats.json'), match_stats)
    
    # Perform migration if requested
    if args.migrate:
        logger.info("Migrating voice PBX assets...")
        
        # Create migrator
        migrator = VoicePBXMigrator(dry_run=args.dry_run)
        
        # Migrate voice PBX assets
        migration_results = migrator.migrate_voice_pbx_assets(itglue_assets, matches, servicenow_gateways)
        
        # Print migration results
        print_migration_results(migration_results)
        
        # Generate migration report
        migration_report = migrator.generate_migration_report(migration_results)
        
        # Save migration results
        save_json_file(os.path.join(args.output_dir, 'voice_pbx_migration_results.json'), 
                      [result.__dict__ for result in migration_results])
        save_json_file(os.path.join(args.output_dir, 'voice_pbx_migration_report.json'), 
                      migration_report)
    
    logger.info("Done")
    return 0


if __name__ == '__main__':
    sys.exit(main())