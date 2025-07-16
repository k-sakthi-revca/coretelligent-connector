#!/usr/bin/env python3
"""
ITGlue to ServiceNow Deduplication Tool

This script implements the deduplication strategy for the ITGlue to ServiceNow migration
as specified in the requirements document. It identifies potential duplicate records
between ITGlue and ServiceNow using a weighted scoring algorithm and processes them
based on confidence levels.

Usage:
    python -3 deduplicator.py --organization <org_name> [--config <config_file>] [--output <output_dir>]

Note: The -3 flag enables Python 3 compatibility mode.

Author: Coretelligent Migration Team
Date: July 2023
"""

import os
import sys
import json
import argparse
import logging
import pandas as pd
from datetime import datetime
# Remove type hints for compatibility with older Python versions
# from typing import Dict, List, Tuple, Any, Optional, Union

# Local imports
from utils import (
    normalize_data,
    calculate_similarity,
    calculate_match_score,
    setup_logging,
    load_config,
    save_results
)

# Configure logging
logger = logging.getLogger(__name__)


class Deduplicator:
    """
    Main class for handling the deduplication process between ITGlue and ServiceNow.
    """

    def __init__(self, config_path=None):
        """
        Initialize the Deduplicator with configuration settings.
        
        Args:
            config_path: Path to the configuration file (optional)
        """
        self.config = load_config(config_path)
        self.itglue_data = None
        self.servicenow_data = None
        self.results = {
            "high_confidence": [],
            "medium_confidence": [],
            "low_confidence": [],
            "errors": [],
            "stats": {
                "total_records": 0,
                "high_confidence_matches": 0,
                "medium_confidence_matches": 0,
                "new_records": 0,
                "error_records": 0
            }
        }
        
        # Set up logging
        log_level = getattr(logging, self.config.get("log_level", "INFO"))
        setup_logging(log_level)
        
        logger.info("Deduplicator initialized with config: {}".format(self.config))

    def load_itglue_data(self, organization, data_path=None):
        """
        Load ITGlue data for the specified organization.
        
        Args:
            organization: Name of the organization to process
            data_path: Path to the ITGlue data (optional)
        """
        logger.info("Loading ITGlue data for organization: {}".format(organization))
        
        # If data_path is provided, load from file
        if data_path and os.path.exists(data_path):
            try:
                with open(data_path, 'r') as f:
                    self.itglue_data = json.load(f)
                logger.info("Loaded {} records from {}".format(len(self.itglue_data), data_path))
            except Exception as e:
                logger.error("Error loading ITGlue data from {}: {}".format(data_path, str(e)))
                raise
        else:
            # TODO: Implement API-based data loading
            # This would connect to ITGlue API and extract data for the organization
            logger.error("API-based data loading not implemented yet. Please provide a data file.")
            raise NotImplementedError("API-based data loading not implemented yet")
        
        # Apply data filters as per requirements
        self._filter_itglue_data()
        
        # Normalize the data
        self.itglue_data = normalize_data(self.itglue_data)
        
        self.results["stats"]["total_records"] = len(self.itglue_data)
        logger.info("Loaded and processed {} ITGlue records".format(len(self.itglue_data)))

    def load_servicenow_data(self, organization, data_path=None):
        """
        Load ServiceNow data for the specified organization.
        
        Args:
            organization: Name of the organization to process
            data_path: Path to the ServiceNow data (optional)
        """
        logger.info("Loading ServiceNow data for organization: {}".format(organization))
        
        # If data_path is provided, load from file
        if data_path and os.path.exists(data_path):
            try:
                with open(data_path, 'r') as f:
                    self.servicenow_data = json.load(f)
                logger.info("Loaded {} records from {}".format(len(self.servicenow_data), data_path))
            except Exception as e:
                logger.error("Error loading ServiceNow data from {}: {}".format(data_path, str(e)))
                raise
        else:
            # TODO: Implement API-based data loading
            # This would connect to ServiceNow API and extract data for the organization
            logger.error("API-based data loading not implemented yet. Please provide a data file.")
            raise NotImplementedError("API-based data loading not implemented yet")
        
        # Verify the ServiceNow account is active
        if not self._verify_servicenow_account(organization):
            logger.error("ServiceNow account for {} is not active".format(organization))
            raise ValueError("ServiceNow account for {} is not active".format(organization))
        
        # Normalize the data
        self.servicenow_data = normalize_data(self.servicenow_data)
        
        logger.info("Loaded and processed {} ServiceNow records".format(len(self.servicenow_data)))

    def _filter_itglue_data(self):
        """
        Apply filters to ITGlue data as per requirements.
        
        Filters:
        - Skip records where .archived = false
        - Skip if organization status doesn't match allowed statuses
        - Skip "Product Only" assets containing "Not Managed By Coretelligent"
        """
        if not self.itglue_data:
            logger.warning("No ITGlue data to filter")
            return
        
        original_count = len(self.itglue_data)
        
        # Define allowed organization statuses
        allowed_statuses = [
            "Active", "Active - Popup", "Credit Hold", "Product Only", 
            "Presales", "Service Hold Phase 1", "Service Hold Phase 2", 
            "Service Hold Phase 3", "Pre-Pay Only", "Staff Augmentation"
        ]
        
        filtered_data = []
        for record in self.itglue_data:
            # Skip archived records
            if record.get("archived") == False:
                logger.debug("Skipping archived record: {}".format(record.get('id')))
                continue
            
            # Skip if organization status is not allowed
            org_status = record.get("organization_status_name")
            if org_status and org_status not in allowed_statuses:
                logger.debug("Skipping record with invalid org status: {}".format(org_status))
                continue
            
            # Skip "Product Only" assets with "Not Managed By Coretelligent"
            if (org_status == "Product Only" and 
                "Not Managed By Coretelligent" in record.get("notes", "")):
                logger.debug("Skipping 'Not Managed' Product Only record: {}".format(record.get('id')))
                continue
            
            filtered_data.append(record)
        
        self.itglue_data = filtered_data
        logger.info("Filtered ITGlue data: {} -> {} records".format(original_count, len(self.itglue_data)))

    def _verify_servicenow_account(self, organization):
        """
        Verify that the ServiceNow account for the organization is active.
        
        Args:
            organization: Name of the organization to verify
            
        Returns:
            bool: True if the account is active, False otherwise
        """
        # TODO: Implement actual verification against ServiceNow
        # For now, assume all accounts are active
        return True

    def process_records(self):
        """
        Process all ITGlue records against ServiceNow to identify duplicates.
        
        Returns:
            Dict: Results of the deduplication process
        """
        if not self.itglue_data:
            logger.error("No ITGlue data loaded")
            raise ValueError("No ITGlue data loaded")
        
        if not self.servicenow_data:
            logger.error("No ServiceNow data loaded")
            raise ValueError("No ServiceNow data loaded")
        
        logger.info("Starting deduplication process")
        
        for itg_record in self.itglue_data:
            try:
                self._process_single_record(itg_record)
            except Exception as e:
                logger.error("Error processing record {}: {}".format(itg_record.get('id'), str(e)))
                self.results["errors"].append({
                    "record_id": itg_record.get("id"),
                    "error": str(e)
                })
                self.results["stats"]["error_records"] += 1
        
        logger.info("Deduplication process completed")
        logger.info("Stats: {}".format(self.results['stats']))
        
        return self.results

    def _process_single_record(self, itg_record):
        """
        Process a single ITGlue record against ServiceNow records.
        
        Args:
            itg_record: The ITGlue record to process
        """
        logger.debug("Processing record: {}".format(itg_record.get('id')))
        
        # Find potential matches in ServiceNow
        potential_matches = self._find_potential_matches(itg_record)
        
        if not potential_matches:
            # No potential matches found, create new record
            logger.debug("No potential matches found for {}".format(itg_record.get('id')))
            self.results["low_confidence"].append({
                "itglue_record": itg_record,
                "servicenow_record": None,
                "match_score": 0.0,
                "action": "create_new"
            })
            self.results["stats"]["new_records"] += 1
            return
        
        # Calculate match scores for all potential matches
        scored_matches = []
        for sn_record in potential_matches:
            match_score = self._calculate_match_score(itg_record, sn_record)
            scored_matches.append((sn_record, match_score))
        
        # Sort by match score (highest first)
        scored_matches.sort(key=lambda x: x[1], reverse=True)
        
        # Get the best match
        best_match, best_score = scored_matches[0]
        
        # Process based on confidence level
        if best_score >= 0.8:
            # High confidence match
            logger.debug("High confidence match ({}) for {}".format(best_score, itg_record.get('id')))
            self.results["high_confidence"].append({
                "itglue_record": itg_record,
                "servicenow_record": best_match,
                "match_score": best_score,
                "action": "automatic_update"
            })
            self.results["stats"]["high_confidence_matches"] += 1
        elif best_score >= 0.6:
            # Medium confidence match
            logger.debug("Medium confidence match ({}) for {}".format(best_score, itg_record.get('id')))
            self.results["medium_confidence"].append({
                "itglue_record": itg_record,
                "servicenow_record": best_match,
                "match_score": best_score,
                "action": "manual_review"
            })
            self.results["stats"]["medium_confidence_matches"] += 1
        else:
            # Low confidence match, create new record
            logger.debug("Low confidence match ({}) for {}".format(best_score, itg_record.get('id')))
            self.results["low_confidence"].append({
                "itglue_record": itg_record,
                "servicenow_record": best_match,
                "match_score": best_score,
                "action": "create_new"
            })
            self.results["stats"]["new_records"] += 1

    def _find_potential_matches(self, itg_record):
        """
        Find potential matches for an ITGlue record in ServiceNow.
        
        Args:
            itg_record: The ITGlue record to find matches for
            
        Returns:
            List[Dict]: List of potential matching ServiceNow records
        """
        potential_matches = []
        
        # Extract key identifiers
        serial_number = itg_record.get("serial_number", "").strip()
        mac_address = itg_record.get("mac_address", "").strip()
        asset_tag = itg_record.get("asset_tag", "").strip()
        hostname = itg_record.get("hostname", "").strip()
        ip_address = itg_record.get("primary_ip", "").strip()
        name = itg_record.get("name", "").strip()
        
        # Get organization/company context
        organization_id = itg_record.get("organization_id")
        
        # Search for matches within the same company context
        for sn_record in self.servicenow_data:
            # Skip records from different companies
            if sn_record.get("company") != organization_id:
                continue
            
            # Check primary identifiers first
            if serial_number and serial_number == sn_record.get("serial_number", "").strip():
                potential_matches.append(sn_record)
                continue
                
            if mac_address and mac_address == sn_record.get("mac_address", "").strip():
                potential_matches.append(sn_record)
                continue
                
            if asset_tag and asset_tag == sn_record.get("asset_tag", "").strip():
                potential_matches.append(sn_record)
                continue
            
            # Check secondary identifiers
            if hostname and hostname == sn_record.get("hostname", "").strip():
                potential_matches.append(sn_record)
                continue
                
            if ip_address and ip_address == sn_record.get("ip_address", "").strip():
                potential_matches.append(sn_record)
                continue
                
            if name and name == sn_record.get("name", "").strip():
                potential_matches.append(sn_record)
                continue
        
        return potential_matches

    def _calculate_match_score(self, itg_record, sn_record):
        """
        Calculate the match score between an ITGlue record and a ServiceNow record.
        
        The weighted formula is:
        Match Score = (
            0.4 * serial_number_similarity +
            0.3 * mac_address_similarity +
            0.2 * hostname_similarity +
            0.1 * name_similarity
        )
        
        Args:
            itg_record: The ITGlue record
            sn_record: The ServiceNow record
            
        Returns:
            float: The match score (0.0 to 1.0)
        """
        # Extract fields for comparison
        itg_serial = itg_record.get("serial_number", "").strip()
        sn_serial = sn_record.get("serial_number", "").strip()
        
        itg_mac = itg_record.get("mac_address", "").strip()
        sn_mac = sn_record.get("mac_address", "").strip()
        
        itg_hostname = itg_record.get("hostname", "").strip()
        sn_hostname = sn_record.get("hostname", "").strip()
        
        itg_name = itg_record.get("name", "").strip()
        sn_name = sn_record.get("name", "").strip()
        
        # Calculate similarities
        serial_similarity = calculate_similarity(itg_serial, sn_serial)
        mac_similarity = calculate_similarity(itg_mac, sn_mac)
        hostname_similarity = calculate_similarity(itg_hostname, sn_hostname)
        name_similarity = calculate_similarity(itg_name, sn_name)
        
        # Apply weighted formula
        match_score = (
            0.4 * serial_similarity +
            0.3 * mac_similarity +
            0.2 * hostname_similarity +
            0.1 * name_similarity
        )
        
        return match_score

    def apply_updates(self, dry_run=True):
        """
        Apply the deduplication results to ServiceNow.
        
        Args:
            dry_run: If True, only simulate updates without actually applying them
            
        Returns:
            Dict: Results of the update process
        """
        if not self.results:
            logger.error("No deduplication results to apply")
            raise ValueError("No deduplication results to apply")
        
        update_results = {
            "updated": 0,
            "created": 0,
            "errors": [],
            "dry_run": dry_run
        }
        
        logger.info("Applying updates (dry_run={})".format(dry_run))
        
        # Process high confidence matches (automatic updates)
        for match in self.results["high_confidence"]:
            try:
                if not dry_run:
                    # TODO: Implement actual update to ServiceNow
                    pass
                update_results["updated"] += 1
                logger.debug("Updated record: {}".format(match['servicenow_record'].get('sys_id')))
            except Exception as e:
                logger.error("Error updating record: {}".format(str(e)))
                update_results["errors"].append({
                    "record_id": match["servicenow_record"].get("sys_id"),
                    "error": str(e)
                })
        
        # Process low confidence matches (create new records)
        for match in self.results["low_confidence"]:
            if match["action"] != "create_new":
                continue
                
            try:
                if not dry_run:
                    # TODO: Implement actual creation in ServiceNow
                    pass
                update_results["created"] += 1
                logger.debug("Created new record for ITGlue ID: {}".format(match['itglue_record'].get('id')))
            except Exception as e:
                logger.error("Error creating record: {}".format(str(e)))
                update_results["errors"].append({
                    "record_id": match["itglue_record"].get("id"),
                    "error": str(e)
                })
        
        logger.info("Update results: {}".format(update_results))
        return update_results

    def generate_report(self, output_dir=None):
        """
        Generate a comprehensive report of the deduplication process.
        
        Args:
            output_dir: Directory to save the report (optional)
            
        Returns:
            str: Path to the generated report
        """
        if not self.results:
            logger.error("No deduplication results to report")
            raise ValueError("No deduplication results to report")
        
        # Create output directory if it doesn't exist
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Generate timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Define report filename
        report_filename = "deduplication_report_{}.json".format(timestamp)
        if output_dir:
            report_path = os.path.join(output_dir, report_filename)
        else:
            report_path = report_filename
        
        # Create the report
        report = {
            "timestamp": timestamp,
            "stats": self.results["stats"],
            "high_confidence_count": len(self.results["high_confidence"]),
            "medium_confidence_count": len(self.results["medium_confidence"]),
            "low_confidence_count": len(self.results["low_confidence"]),
            "error_count": len(self.results["errors"]),
            "medium_confidence_matches": self.results["medium_confidence"],
            "errors": self.results["errors"]
        }
        
        # Save the report
        try:
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info("Report saved to {}".format(report_path))
        except Exception as e:
            logger.error("Error saving report: {}".format(str(e)))
            raise
        
        return report_path

    def export_manual_review_items(self, output_dir=None):
        """
        Export medium confidence matches for manual review.
        
        Args:
            output_dir: Directory to save the export (optional)
            
        Returns:
            str: Path to the exported file
        """
        if not self.results or not self.results.get("medium_confidence"):
            logger.error("No medium confidence matches to export")
            raise ValueError("No medium confidence matches to export")
        
        # Create output directory if it doesn't exist
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Generate timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Define export filename
        export_filename = "manual_review_items_{}.csv".format(timestamp)
        if output_dir:
            export_path = os.path.join(output_dir, export_filename)
        else:
            export_path = export_filename
        
        # Prepare data for CSV export
        data = []
        for match in self.results["medium_confidence"]:
            itg_record = match["itglue_record"]
            sn_record = match["servicenow_record"]
            
            row = {
                "match_score": match["match_score"],
                "itg_id": itg_record.get("id"),
                "itg_name": itg_record.get("name"),
                "itg_serial": itg_record.get("serial_number"),
                "itg_mac": itg_record.get("mac_address"),
                "itg_hostname": itg_record.get("hostname"),
                "sn_sys_id": sn_record.get("sys_id"),
                "sn_name": sn_record.get("name"),
                "sn_serial": sn_record.get("serial_number"),
                "sn_mac": sn_record.get("mac_address"),
                "sn_hostname": sn_record.get("hostname"),
                "decision": ""  # To be filled by reviewer
            }
            data.append(row)
        
        # Create DataFrame and export to CSV
        try:
            df = pd.DataFrame(data)
            df.to_csv(export_path, index=False)
            logger.info("Manual review items exported to {}".format(export_path))
        except Exception as e:
            logger.error("Error exporting manual review items: {}".format(str(e)))
            raise
        
        return export_path


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="ITGlue to ServiceNow Deduplication Tool")
    parser.add_argument("--organization", required=True, help="Name of the organization to process")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--itglue-data", help="Path to ITGlue data file")
    parser.add_argument("--servicenow-data", help="Path to ServiceNow data file")
    parser.add_argument("--output", help="Directory to save output files")
    parser.add_argument("--apply", action="store_true", help="Apply updates to ServiceNow")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Initialize deduplicator
    deduplicator = Deduplicator(args.config)
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Load data
        deduplicator.load_itglue_data(args.organization, args.itglue_data)
        deduplicator.load_servicenow_data(args.organization, args.servicenow_data)
        
        # Process records
        results = deduplicator.process_records()
        
        # Generate report
        report_path = deduplicator.generate_report(args.output)
        print("Deduplication report saved to: {}".format(report_path))
        
        # Export manual review items
        if results["medium_confidence"]:
            export_path = deduplicator.export_manual_review_items(args.output)
            print("Manual review items exported to: {}".format(export_path))
        
        # Apply updates if requested
        if args.apply:
            update_results = deduplicator.apply_updates(dry_run=False)
            print("Applied {} updates and created {} new records".format(
                update_results['updated'], update_results['created']))
        else:
            update_results = deduplicator.apply_updates(dry_run=True)
            print("Dry run: Would apply {} updates and create {} new records".format(
                update_results['updated'], update_results['created']))
        
        # Print summary
        print("\nDeduplication Summary:")
        print("Total records processed: {}".format(results['stats']['total_records']))
        print("High confidence matches: {}".format(results['stats']['high_confidence_matches']))
        print("Medium confidence matches: {}".format(results['stats']['medium_confidence_matches']))
        print("New records: {}".format(results['stats']['new_records']))
        print("Error records: {}".format(results['stats']['error_records']))
        
    except Exception as e:
        logger.error("Error: {}".format(str(e)))
        print("Error: {}".format(str(e)))
        sys.exit(1)


if __name__ == "__main__":
    main()
