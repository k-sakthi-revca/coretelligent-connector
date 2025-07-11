"""
Demo script for the virtualization matcher.
"""

import json
import logging
import os
from typing import Dict, List, Any

from virtualization_matcher import VirtualizationMatcher


def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )


def load_json_file(file_path: str) -> Any:
    """
    Load JSON data from a file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Parsed JSON data
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load JSON file {file_path}: {e}")
        return None


def print_match_results(matches, quality_issues, stats):
    """
    Print match results in a readable format.
    
    Args:
        matches: List of match results
        quality_issues: List of data quality issues
        stats: Matching statistics
    """
    print("\n" + "=" * 80)
    print(f"VIRTUALIZATION ASSET MATCHING RESULTS ({stats['total']} assets)")
    print("=" * 80)
    
    # Print match type statistics
    print("\nMATCH TYPES:")
    for match_type, data in stats['by_match_type'].items():
        print(f"  {match_type}: {data['count']} ({data['percentage']:.1f}%)")
    
    # Print recommended action statistics
    print("\nRECOMMENDED ACTIONS:")
    for action, data in stats['by_recommended_action'].items():
        print(f"  {action}: {data['count']} ({data['percentage']:.1f}%)")
    
    # Print data quality statistics
    print("\nDATA QUALITY:")
    for quality, data in stats['by_data_quality'].items():
        print(f"  {quality}: {data['count']} ({data['percentage']:.1f}%)")
    
    # Print hypervisor statistics
    print("\nHYPERVISORS:")
    for hypervisor, data in stats['by_hypervisor'].items():
        print(f"  {hypervisor}: {data['count']} ({data['percentage']:.1f}%)")
    
    # Print match details
    print("\nMATCH DETAILS:")
    for i, match in enumerate(matches, 1):
        print(f"\n{i}. {match.itglue_name} ({match.hypervisor})")
        print(f"   Match Type: {match.match_type}")
        print(f"   Confidence: {match.confidence:.1%}")
        print(f"   Action: {match.recommended_action}")
        print(f"   Quality: {match.data_quality}")
        
        if match.servicenow_id:
            print(f"   ServiceNow: {match.servicenow_name} (ID: {match.servicenow_id})")
        
        if match.notes:
            print(f"   Notes: {match.notes}")
    
    # Print quality issues
    if quality_issues:
        print("\nDATA QUALITY ISSUES:")
        for i, issue in enumerate(quality_issues, 1):
            print(f"\n{i}. {issue.asset_name}")
            print(f"   Issue Type: {issue.issue_type}")
            print(f"   Priority: {issue.priority}")
            print(f"   Description: {issue.description}")
            print(f"   Recommendation: {issue.recommendation}")


def save_report_to_file(matches, quality_issues, stats, file_path="virtualization_migration_report.json"):
    """
    Save match results to a JSON file.
    
    Args:
        matches: List of match results
        quality_issues: List of data quality issues
        stats: Matching statistics
        file_path: Path to save the report
    """
    # Convert dataclass objects to dictionaries
    matches_dict = [
        {
            "itglue_id": match.itglue_id,
            "itglue_name": match.itglue_name,
            "servicenow_id": match.servicenow_id,
            "servicenow_name": match.servicenow_name,
            "match_type": match.match_type,
            "confidence": match.confidence,
            "recommended_action": match.recommended_action,
            "data_quality": match.data_quality,
            "hypervisor": match.hypervisor,
            "notes": match.notes
        }
        for match in matches
    ]
    
    issues_dict = [
        {
            "asset_id": issue.asset_id,
            "asset_name": issue.asset_name,
            "issue_type": issue.issue_type,
            "priority": issue.priority,
            "description": issue.description,
            "recommendation": issue.recommendation
        }
        for issue in quality_issues
    ]
    
    # Create report dictionary
    report = {
        "timestamp": logging.Formatter().converter(),
        "statistics": stats,
        "matches": matches_dict,
        "quality_issues": issues_dict
    }
    
    # Save to file
    try:
        with open(file_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        logging.info(f"Report saved to {file_path}")
    except Exception as e:
        logging.error(f"Failed to save report to {file_path}: {e}")


def main():
    """Main function."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Load virtualization data
    logger.info("Loading virtualization data...")
    virtualization_data_path = os.path.join("data", "virtualization", "virtualization_data.json")
    virtualization_data = load_json_file(virtualization_data_path)
    
    if not virtualization_data or "data" not in virtualization_data:
        logger.error("Failed to load virtualization data or invalid format")
        return
    
    # Load ServiceNow server data
    logger.info("Loading ServiceNow server data...")
    servicenow_servers_path = "mock_servicenow_servers.json"
    servicenow_servers = load_json_file(servicenow_servers_path)
    
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
    
    # Print results
    print_match_results(matches, quality_issues, stats)
    
    # Save report to file
    save_report_to_file(matches, quality_issues, stats, "virtualization_migration_report.json")
    
    logger.info("Virtualization matching demo completed")


if __name__ == "__main__":
    main()