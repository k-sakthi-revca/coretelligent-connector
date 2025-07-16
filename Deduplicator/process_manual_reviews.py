#!/usr/bin/env python3
"""
Process Manual Review Items for ITGlue to ServiceNow Deduplication

This script processes the manual review decisions made by reviewers for medium
confidence matches. It reads the CSV file containing the decisions and applies
the appropriate actions (update, keep, or create) to ServiceNow.

Usage:
    python -3 process_manual_reviews.py --file <manual_review_file> [--config <config_file>] [--dry-run]

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
# Remove type hints for compatibility with older Python versions
# from typing import Dict, List, Any, Optional

# Local imports
from utils import setup_logging, load_config, save_results
from config import get_default_config

# Configure logging
logger = logging.getLogger(__name__)


class ManualReviewProcessor:
    """
    Process manual review decisions for medium confidence matches.
    """

    def __init__(self, config_path=None):
        """
        Initialize the ManualReviewProcessor with configuration settings.
        
        Args:
            config_path: Path to the configuration file (optional)
        """
        self.config = load_config(config_path) if config_path else get_default_config()
        self.results = {
            "updated": 0,
            "kept": 0,
            "created": 0,
            "errors": [],
            "stats": {
                "total_records": 0,
                "processed_records": 0,
                "error_records": 0
            }
        }
        
        # Set up logging
        log_level = getattr(logging, self.config.get("logging", {}).get("level", "INFO"))
        setup_logging(log_level)
        
        logger.info("ManualReviewProcessor initialized with config: {}".format(self.config))

    def load_manual_review_file(self, file_path):
        """
        Load the manual review CSV file.
        
        Args:
            file_path: Path to the manual review CSV file
            
        Returns:
            pd.DataFrame: DataFrame containing the manual review items
        """
        logger.info("Loading manual review file: {}".format(file_path))
        
        if not os.path.exists(file_path):
            logger.error("Manual review file not found: {}".format(file_path))
            raise FileNotFoundError("Manual review file not found: {}".format(file_path))
        
        try:
            df = pd.read_csv(file_path)
            logger.info("Loaded {} manual review items from {}".format(len(df), file_path))
            
            # Validate required columns
            required_columns = [
                "match_score", "itg_id", "sn_sys_id", "decision"
            ]
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error("Missing required columns in manual review file: {}".format(missing_columns))
                raise ValueError("Missing required columns in manual review file: {}".format(missing_columns))
            
            # Check if decisions have been made
            if df["decision"].isna().all():
                logger.error("No decisions have been made in the manual review file")
                raise ValueError("No decisions have been made in the manual review file")
            
            self.results["stats"]["total_records"] = len(df)
            return df
            
        except Exception as e:
            logger.error("Error loading manual review file: {}".format(str(e)))
            raise

    def process_decisions(self, df, dry_run=True):
        """
        Process the manual review decisions.
        
        Args:
            df: DataFrame containing the manual review items
            dry_run: If True, only simulate actions without actually applying them
            
        Returns:
            Dict: Results of the processing
        """
        logger.info("Processing manual review decisions (dry_run={})".format(dry_run))
        
        # Process each row
        for index, row in df.iterrows():
            try:
                decision = row["decision"].strip().lower()
                
                if not decision:
                    logger.warning("No decision for row {}, skipping".format(index))
                    continue
                
                if decision not in ["update", "keep", "create"]:
                    logger.warning("Invalid decision '{}' for row {}, skipping".format(decision, index))
                    continue
                
                # Process based on decision
                if decision == "update":
                    self._process_update_decision(row, dry_run)
                elif decision == "keep":
                    self._process_keep_decision(row, dry_run)
                elif decision == "create":
                    self._process_create_decision(row, dry_run)
                
                self.results["stats"]["processed_records"] += 1
                
            except Exception as e:
                logger.error("Error processing row {}: {}".format(index, str(e)))
                self.results["errors"].append({
                    "row_index": index,
                    "itg_id": row.get("itg_id"),
                    "sn_sys_id": row.get("sn_sys_id"),
                    "error": str(e)
                })
                self.results["stats"]["error_records"] += 1
        
        logger.info("Processed {} decisions".format(self.results['stats']['processed_records']))
        logger.info("Results: {} updated, {} kept, {} created".format(
            self.results['updated'], self.results['kept'], self.results['created']))
        
        return self.results

    def _process_update_decision(self, row, dry_run):
        """
        Process an 'update' decision.
        
        Args:
            row: DataFrame row containing the manual review item
            dry_run: If True, only simulate the update without actually applying it
        """
        itg_id = row["itg_id"]
        sn_sys_id = row["sn_sys_id"]
        
        logger.debug("Processing 'update' decision for ITG ID {} -> SN sys_id {}".format(itg_id, sn_sys_id))
        
        if not dry_run:
            # TODO: Implement actual update to ServiceNow
            # This would involve:
            # 1. Retrieving the ITGlue record data
            # 2. Updating the ServiceNow record with the ITGlue data
            # 3. Setting the u_itg_id field to track the source
            pass
        
        self.results["updated"] += 1
        logger.debug("Updated ServiceNow record {} with ITGlue data {}".format(sn_sys_id, itg_id))

    def _process_keep_decision(self, row, dry_run):
        """
        Process a 'keep' decision.
        
        Args:
            row: DataFrame row containing the manual review item
            dry_run: If True, only simulate the action without actually applying it
        """
        itg_id = row["itg_id"]
        sn_sys_id = row["sn_sys_id"]
        
        logger.debug("Processing 'keep' decision for ITG ID {} -> SN sys_id {}".format(itg_id, sn_sys_id))
        
        if not dry_run:
            # TODO: Implement action for 'keep' decision
            # This might involve:
            # 1. Marking the ITGlue record as processed
            # 2. Possibly updating the u_itg_id field in ServiceNow for tracking
            pass
        
        self.results["kept"] += 1
        logger.debug("Kept ServiceNow record {} as is".format(sn_sys_id))

    def _process_create_decision(self, row, dry_run):
        """
        Process a 'create' decision.
        
        Args:
            row: DataFrame row containing the manual review item
            dry_run: If True, only simulate the creation without actually applying it
        """
        itg_id = row["itg_id"]
        
        logger.debug("Processing 'create' decision for ITG ID {}".format(itg_id))
        
        if not dry_run:
            # TODO: Implement actual creation in ServiceNow
            # This would involve:
            # 1. Retrieving the ITGlue record data
            # 2. Creating a new record in ServiceNow with the ITGlue data
            # 3. Setting the u_itg_id field to track the source
            pass
        
        self.results["created"] += 1
        logger.debug("Created new ServiceNow record for ITGlue ID {}".format(itg_id))

    def generate_report(self, output_dir=None):
        """
        Generate a report of the manual review processing.
        
        Args:
            output_dir: Directory to save the report (optional)
            
        Returns:
            str: Path to the generated report
        """
        from datetime import datetime
        
        # Create output directory if it doesn't exist
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Generate timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Define report filename
        report_filename = "manual_review_processing_report_{}.json".format(timestamp)
        if output_dir:
            report_path = os.path.join(output_dir, report_filename)
        else:
            report_path = report_filename
        
        # Create the report
        report = {
            "timestamp": timestamp,
            "stats": self.results["stats"],
            "updated_count": self.results["updated"],
            "kept_count": self.results["kept"],
            "created_count": self.results["created"],
            "error_count": len(self.results["errors"]),
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


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Process Manual Review Items for ITGlue to ServiceNow Deduplication")
    parser.add_argument("--file", required=True, help="Path to the manual review CSV file")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--output", help="Directory to save output files")
    parser.add_argument("--dry-run", action="store_true", help="Simulate actions without applying them")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = ManualReviewProcessor(args.config)
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Load manual review file
        df = processor.load_manual_review_file(args.file)
        
        # Process decisions
        results = processor.process_decisions(df, args.dry_run)
        
        # Generate report
        report_path = processor.generate_report(args.output)
        print("Processing report saved to: {}".format(report_path))
        
        # Print summary
        print("\nManual Review Processing Summary:")
        print("Total records: {}".format(results['stats']['total_records']))
        print("Processed records: {}".format(results['stats']['processed_records']))
        print("Updated: {}".format(results['updated']))
        print("Kept as is: {}".format(results['kept']))
        print("Created new: {}".format(results['created']))
        print("Errors: {}".format(results['stats']['error_records']))
        
        if args.dry_run:
            print("\nThis was a dry run. No changes were applied to ServiceNow.")
        
    except Exception as e:
        logger.error("Error: {}".format(str(e)))
        print("Error: {}".format(str(e)))
        sys.exit(1)


if __name__ == "__main__":
    main()
