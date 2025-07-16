#!/usr/bin/env python3
"""
Example Usage of the ITGlue to ServiceNow Deduplication Tool

This script demonstrates how to use the deduplication tool with sample data.
It provides examples of loading data, running the deduplication process,
and processing manual review decisions.

Usage:
    python -3 example.py

Note: The -3 flag enables Python 3 compatibility mode.

Author: Coretelligent Migration Team
Date: July 2023
"""

import os
import json
import logging
import pandas as pd
from datetime import datetime

# Import the deduplication tool
from deduplicator import Deduplicator
from process_manual_reviews import ManualReviewProcessor
from utils import setup_logging

# Set up logging
setup_logging(logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_data():
    """
    Create sample data for demonstration purposes.
    
    Returns:
        tuple: Paths to the sample ITGlue and ServiceNow data files
    """
    # Create output directory if it doesn't exist
    if not os.path.exists("sample_data"):
        os.makedirs("sample_data")
    
    # Create sample ITGlue data
    itglue_data = [
        {
            "id": "itg-001",
            "name": "ACME-SRV01",
            "hostname": "acme-srv01.local",
            "serial_number": "ABC123456",
            "mac_address": "00:11:22:33:44:55",
            "primary_ip": "192.168.1.10",
            "organization_id": "org-001",
            "organization_status_name": "Active",
            "notes": "Primary file server",
            "archived": True
        },
        {
            "id": "itg-002",
            "name": "ACME-SRV02",
            "hostname": "acme-srv02.local",
            "serial_number": "DEF789012",
            "mac_address": "00:11:22:33:44:66",
            "primary_ip": "192.168.1.11",
            "organization_id": "org-001",
            "organization_status_name": "Active",
            "notes": "Database server",
            "archived": True
        },
        {
            "id": "itg-003",
            "name": "ACME-WKS01",
            "hostname": "acme-wks01.local",
            "serial_number": "GHI345678",
            "mac_address": "00:11:22:33:44:77",
            "primary_ip": "192.168.1.100",
            "organization_id": "org-001",
            "organization_status_name": "Active",
            "notes": "CEO workstation",
            "archived": True
        },
        {
            "id": "itg-004",
            "name": "ACME-RTR01",
            "hostname": "acme-rtr01.local",
            "serial_number": "JKL901234",
            "mac_address": "00:11:22:33:44:88",
            "primary_ip": "192.168.1.1",
            "organization_id": "org-001",
            "organization_status_name": "Active",
            "notes": "Main router",
            "archived": True
        }
    ]
    
    # Create sample ServiceNow data
    servicenow_data = [
        {
            "sys_id": "sn-001",
            "name": "ACME-SRV01",
            "hostname": "acme-srv01.local",
            "serial_number": "ABC123456",
            "mac_address": "00:11:22:33:44:55",
            "ip_address": "192.168.1.10",
            "company": "org-001",
            "u_itg_id": ""
        },
        {
            "sys_id": "sn-002",
            "name": "ACME-SRV02-OLD",  # Slightly different name
            "hostname": "acme-srv02.local",
            "serial_number": "DEF789012",
            "mac_address": "AA:BB:CC:DD:EE:FF",  # Different MAC
            "ip_address": "192.168.1.11",
            "company": "org-001",
            "u_itg_id": ""
        },
        {
            "sys_id": "sn-003",
            "name": "ACME-WKS99",  # Different name
            "hostname": "acme-wks99.local",  # Different hostname
            "serial_number": "GHI345678",  # Same serial
            "mac_address": "00:11:22:33:44:77",
            "ip_address": "192.168.1.199",  # Different IP
            "company": "org-001",
            "u_itg_id": ""
        }
        # Note: No match for ACME-RTR01 in ServiceNow
    ]
    
    # Save sample data to files
    itglue_data_path = os.path.join("sample_data", "itglue_sample.json")
    servicenow_data_path = os.path.join("sample_data", "servicenow_sample.json")
    
    with open(itglue_data_path, 'w') as f:
        json.dump(itglue_data, f, indent=2)
    
    with open(servicenow_data_path, 'w') as f:
        json.dump(servicenow_data, f, indent=2)
    
    logger.info("Created sample ITGlue data: {}".format(itglue_data_path))
    logger.info("Created sample ServiceNow data: {}".format(servicenow_data_path))
    
    return itglue_data_path, servicenow_data_path


def run_deduplication_example():
    """
    Run the deduplication process with sample data.
    
    Returns:
        Path to the manual review items file
    """
    # Create sample data
    itglue_data_path, servicenow_data_path = create_sample_data()
    
    # Create output directory if it doesn't exist
    output_dir = os.path.join("sample_data", "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Initialize deduplicator
    deduplicator = Deduplicator()
    
    # Load data
    deduplicator.load_itglue_data("Acme Corporation", itglue_data_path)
    deduplicator.load_servicenow_data("Acme Corporation", servicenow_data_path)
    
    # Process records
    results = deduplicator.process_records()
    
    # Generate report
    report_path = deduplicator.generate_report(output_dir)
    logger.info("Deduplication report saved to: {}".format(report_path))
    
    # Export manual review items
    if results["medium_confidence"]:
        manual_review_path = deduplicator.export_manual_review_items(output_dir)
        logger.info("Manual review items exported to: {}".format(manual_review_path))
    else:
        manual_review_path = None
        logger.info("No medium confidence matches to export")
    
    # Apply updates (dry run)
    update_results = deduplicator.apply_updates(dry_run=True)
    logger.info("Dry run: Would apply {} updates and create {} new records".format(
        update_results['updated'], update_results['created']))
    
    # Print summary
    print("\nDeduplication Summary:")
    print("Total records processed: {}".format(results['stats']['total_records']))
    print("High confidence matches: {}".format(results['stats']['high_confidence_matches']))
    print("Medium confidence matches: {}".format(results['stats']['medium_confidence_matches']))
    print("New records: {}".format(results['stats']['new_records']))
    print("Error records: {}".format(results['stats']['error_records']))
    
    return manual_review_path


def simulate_manual_review(manual_review_path):
    """
    Simulate the manual review process.
    
    Args:
        manual_review_path: Path to the manual review items file
    """
    if not manual_review_path or not os.path.exists(manual_review_path):
        logger.error("Manual review file not found")
        return
    
    # Load the manual review file
    df = pd.read_csv(manual_review_path)
    
    # Simulate making decisions
    for index, row in df.iterrows():
        # Make decisions based on match score
        if row["match_score"] >= 0.7:
            decision = "update"
        elif row["match_score"] >= 0.65:
            decision = "keep"
        else:
            decision = "create"
        
        # Update the decision column
        df.at[index, "decision"] = decision
    
    # Save the updated file
    decision_path = manual_review_path.replace(".csv", "_with_decisions.csv")
    df.to_csv(decision_path, index=False)
    logger.info("Saved manual review decisions to: {}".format(decision_path))
    
    return decision_path


def process_manual_review_example(decision_path):
    """
    Process the manual review decisions.
    
    Args:
        decision_path: Path to the manual review decisions file
    """
    if not decision_path or not os.path.exists(decision_path):
        logger.error("Decision file not found")
        return
    
    # Create output directory if it doesn't exist
    output_dir = os.path.join("sample_data", "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Initialize processor
    processor = ManualReviewProcessor()
    
    # Load manual review file
    df = processor.load_manual_review_file(decision_path)
    
    # Process decisions (dry run)
    results = processor.process_decisions(df, dry_run=True)
    
    # Generate report
    report_path = processor.generate_report(output_dir)
    logger.info("Processing report saved to: {}".format(report_path))
    
    # Print summary
    print("\nManual Review Processing Summary:")
    print("Total records: {}".format(results['stats']['total_records']))
    print("Processed records: {}".format(results['stats']['processed_records']))
    print("Updated: {}".format(results['updated']))
    print("Kept as is: {}".format(results['kept']))
    print("Created new: {}".format(results['created']))
    print("Errors: {}".format(results['stats']['error_records']))


def main():
    """Main entry point for the example script."""
    print("=== ITGlue to ServiceNow Deduplication Tool Example ===")
    
    # Run deduplication example
    print("\n1. Running deduplication process...")
    manual_review_path = run_deduplication_example()
    
    # Simulate manual review
    if manual_review_path:
        print("\n2. Simulating manual review process...")
        decision_path = simulate_manual_review(manual_review_path)
        
        # Process manual review decisions
        if decision_path:
            print("\n3. Processing manual review decisions...")
            process_manual_review_example(decision_path)
    
    print("\nExample completed successfully!")


if __name__ == "__main__":
    main()
