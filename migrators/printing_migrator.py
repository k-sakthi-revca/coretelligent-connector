"""
Printing migrator for the migration.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict

from itglue_client import ITGlueClient
from servicenow_mock import ServiceNowMock
from matchers.printing_matcher import PrintingMatcher, PrintingMatch, DataQualityIssue
from field_mapper import FieldMapper
from config import config


@dataclass
class MigrationResult:
    """Result of a migration operation."""
    itglue_id: str
    itglue_name: str
    servicenow_id: Optional[str]
    servicenow_name: Optional[str]
    match_type: str
    confidence: float
    action: str  # 'created', 'updated', 'skipped', 'failed'
    status: str  # 'success', 'failure'
    error_message: Optional[str] = None
    notes: str = ""


class PrintingMigrator:
    """Migrates printing assets from IT Glue to ServiceNow."""
    
    def __init__(self, use_mock_data: bool = True):
        """
        Initialize printing migrator.
        
        Args:
            use_mock_data: Whether to use mock data instead of making API calls
        """
        self.logger = logging.getLogger(__name__)
        self.use_mock_data = use_mock_data
        
        # Initialize clients
        self.itglue_client = ITGlueClient(use_mock_data=use_mock_data)
        self.servicenow_client = ServiceNowMock()
        
        # Initialize matcher and mapper
        self.matcher = PrintingMatcher()
        self.field_mapper = FieldMapper()
        
        # Output settings
        self.output_settings = config.get("output", {})
        self.report_file = self.output_settings.get("printing_report_file", "reports/printing_migration_report.json")
        self.console_output = self.output_settings.get("console_output", True)
        
        self.logger.info(f"Printing Migrator initialized (use_mock_data={use_mock_data})")
    
    def migrate_printing_assets(self) -> Tuple[List[MigrationResult], Dict[str, Any]]:
        """
        Migrate printing assets from IT Glue to ServiceNow.
        
        Returns:
            Tuple of (migration results, statistics)
        """
        self.logger.info("Starting printing migration")
        
        # Test connections
        if not self._test_connections():
            self.logger.error("Connection test failed")
            return [], {"total_printers": 0, "successful": 0, "failed": 0}
        
        # Fetch data
        itglue_printing_assets = self.itglue_client.get_printing_assets()
        servicenow_printers = self.servicenow_client.get_printers()
        
        # Match printing assets
        matches, quality_issues = self.matcher.match_printing_assets(
            itglue_printing_assets, servicenow_printers
        )
        
        # If no printing assets were found, return empty results
        if not matches:
            self.logger.warning("No printing assets found to migrate")
            empty_stats = {
                "total_printers": 0,
                "successful": 0,
                "failed": 0,
                "created": 0,
                "updated": 0,
                "skipped": 0,
                "timestamp": datetime.now().isoformat(),
                "matching": {
                    "total": 0,
                    "by_match_type": {},
                    "by_recommended_action": {},
                    "by_data_quality": {}
                },
                "data_quality": {
                    "total_issues": 0,
                    "by_issue_type": {},
                    "by_priority": {}
                },
                "field_mappings": self.field_mapper.get_field_mapping_details()
            }
            
            # Save empty report
            self._save_report([], empty_stats)
            
            return [], empty_stats
        
        # Migrate printing assets
        migration_results = []
        
        for i, (printing_asset, match) in enumerate(zip(itglue_printing_assets, matches), 1):
            self.logger.info(f"Migrating printing asset {i}/{len(itglue_printing_assets)}: {match.itglue_name}")
            
            if self.console_output:
                self._print_migration_header(i, len(itglue_printing_assets), printing_asset, match)
            
            # Migrate printing asset
            result = self._migrate_single_printing_asset(printing_asset, match)
            migration_results.append(result)
            
            if self.console_output:
                self._print_migration_result(result)
        
        # Generate statistics
        statistics = self._generate_statistics(migration_results, matches, quality_issues)
        
        # Save report
        self._save_report(migration_results, statistics)
        
        # Print summary
        if self.console_output:
            self._print_migration_summary(statistics)
        
        return migration_results, statistics
    
    def _test_connections(self) -> bool:
        """
        Test connections to IT Glue and ServiceNow.
        
        Returns:
            True if connections are successful, False otherwise
        """
        # Test IT Glue connection
        if not self.itglue_client.test_connection():
            self.logger.error("IT Glue connection test failed")
            return False
        
        # Test ServiceNow connection
        if not self.servicenow_client.test_connection():
            self.logger.error("ServiceNow connection test failed")
            return False
        
        self.logger.info("Connection tests successful")
        return True
    
    def _migrate_single_printing_asset(self, printing_asset: Dict[str, Any], match: PrintingMatch) -> MigrationResult:
        """
        Migrate a single printing asset.
        
        Args:
            printing_asset: IT Glue printing asset data
            match: Printing match result
            
        Returns:
            Migration result
        """
        try:
            # Skip printing assets that should not be migrated
            if match.recommended_action == "Skip":
                return MigrationResult(
                    itglue_id=match.itglue_id,
                    itglue_name=match.itglue_name,
                    servicenow_id=None,
                    servicenow_name=None,
                    match_type=match.match_type,
                    confidence=match.confidence,
                    action="skipped",
                    status="success",
                    notes=f"Skipped: {match.notes}"
                )
            
            # Map IT Glue printing asset to ServiceNow printer CI
            printer_data = self.field_mapper.map_printing(printing_asset, match)
            
            # Create or update printer CI in ServiceNow
            if match.recommended_action == "Use Existing" or match.recommended_action == "Review Match":
                # Update existing printer CI
                updated_printer = self.servicenow_client.update_printer(
                    match.servicenow_id, printer_data
                )
                
                if updated_printer:
                    return MigrationResult(
                        itglue_id=match.itglue_id,
                        itglue_name=match.itglue_name,
                        servicenow_id=updated_printer.get("sys_id"),
                        servicenow_name=updated_printer.get("name"),
                        match_type=match.match_type,
                        confidence=match.confidence,
                        action="updated",
                        status="success",
                        notes=f"Updated existing printer CI: {match.notes}"
                    )
                else:
                    return MigrationResult(
                        itglue_id=match.itglue_id,
                        itglue_name=match.itglue_name,
                        servicenow_id=match.servicenow_id,
                        servicenow_name=match.servicenow_name,
                        match_type=match.match_type,
                        confidence=match.confidence,
                        action="failed",
                        status="failure",
                        error_message="Failed to update printer CI",
                        notes=f"Failed to update printer CI: {match.notes}"
                    )
            else:
                # Create new printer CI
                created_printer = self.servicenow_client.create_printer(printer_data)
                
                return MigrationResult(
                    itglue_id=match.itglue_id,
                    itglue_name=match.itglue_name,
                    servicenow_id=created_printer.get("sys_id"),
                    servicenow_name=created_printer.get("name"),
                    match_type=match.match_type,
                    confidence=match.confidence,
                    action="created",
                    status="success",
                    notes=f"Created new printer CI: {match.notes}"
                )
            
        except Exception as e:
            self.logger.exception(f"Failed to migrate printing asset {match.itglue_name}: {e}")
            
            return MigrationResult(
                itglue_id=match.itglue_id,
                itglue_name=match.itglue_name,
                servicenow_id=match.servicenow_id,
                servicenow_name=match.servicenow_name,
                match_type=match.match_type,
                confidence=match.confidence,
                action="failed",
                status="failure",
                error_message=str(e),
                notes=f"Migration failed: {e}"
            )
    
    def _generate_statistics(self, results: List[MigrationResult], 
                           matches: List[PrintingMatch],
                           quality_issues: List[DataQualityIssue]) -> Dict[str, Any]:
        """
        Generate statistics from migration results.
        
        Args:
            results: Migration results
            matches: Printing matches
            quality_issues: Data quality issues
            
        Returns:
            Statistics dictionary
        """
        total = len(results)
        
        # Basic statistics
        stats = {
            "total_printers": total,
            "successful": len([r for r in results if r.status == "success"]),
            "failed": len([r for r in results if r.status == "failure"]),
            "created": len([r for r in results if r.action == "created"]),
            "updated": len([r for r in results if r.action == "updated"]),
            "skipped": len([r for r in results if r.action == "skipped"]),
            "timestamp": datetime.now().isoformat(),
        }
        
        # Add matching statistics
        stats["matching"] = self.matcher.generate_matching_statistics(matches)
        
        # Add data quality statistics
        quality_stats = {
            "total_issues": len(quality_issues),
            "by_issue_type": {},
            "by_priority": {}
        }
        
        for issue in quality_issues:
            # Count by issue type
            issue_type = issue.issue_type
            quality_stats["by_issue_type"][issue_type] = quality_stats["by_issue_type"].get(issue_type, 0) + 1
            
            # Count by priority
            priority = issue.priority
            quality_stats["by_priority"][priority] = quality_stats["by_priority"].get(priority, 0) + 1
        
        stats["data_quality"] = quality_stats
        
        # Add field mapping details
        stats["field_mappings"] = self.field_mapper.get_field_mapping_details()
        
        return stats
    
    def _save_report(self, results: List[MigrationResult], statistics: Dict[str, Any]) -> None:
        """
        Save migration report to file.
        
        Args:
            results: Migration results
            statistics: Migration statistics
        """
        report = {
            "statistics": statistics,
            "results": [asdict(result) for result in results]
        }
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.report_file), exist_ok=True)
            
            with open(self.report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            self.logger.info(f"Migration report saved to {self.report_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save migration report: {e}")
    
    def _print_migration_header(self, index: int, total: int, printing_asset: Dict[str, Any], match: PrintingMatch) -> None:
        """
        Print migration header.
        
        Args:
            index: Current index
            total: Total number of printing assets
            printing_asset: IT Glue printing asset data
            match: Printing match result
        """
        printing_name = match.itglue_name
        
        print("\n" + "=" * 80)
        print(f"Migrating printing asset {index}/{total}: {printing_name}")
        print("-" * 80)
        print(f"IT Glue ID: {match.itglue_id}")
        print(f"Printer Type: {match.printer_type or 'Unknown'}")
        print(f"Match Type: {match.match_type} (Confidence: {match.confidence:.1%})")
        print(f"Recommended Action: {match.recommended_action}")
        print(f"Data Quality: {match.data_quality}")
        
        if match.notes:
            print(f"Notes: {match.notes}")
        
        print("-" * 80)
    
    def _print_migration_result(self, result: MigrationResult) -> None:
        """
        Print migration result.
        
        Args:
            result: Migration result
        """
        if result.status == "success":
            status_str = "✅ Success"
        else:
            status_str = "❌ Failure"
        
        print(f"Result: {status_str} - {result.action.capitalize()}")
        
        if result.servicenow_id:
            print(f"ServiceNow Printer CI: {result.servicenow_name} (ID: {result.servicenow_id})")
        
        if result.error_message:
            print(f"Error: {result.error_message}")
        
        print("=" * 80)
    
    def _print_migration_summary(self, statistics: Dict[str, Any]) -> None:
        """
        Print migration summary.
        
        Args:
            statistics: Migration statistics
        """
        total = statistics["total_printers"]
        successful = statistics["successful"]
        failed = statistics["failed"]
        created = statistics["created"]
        updated = statistics["updated"]
        skipped = statistics["skipped"]
        
        print("\n" + "=" * 80)
        print("Printing Migration Summary")
        print("=" * 80)
        print(f"Total Printing Assets: {total}")
        
        # Avoid division by zero
        if total > 0:
            print(f"Successful: {successful} ({successful/total*100:.1f}%)")
            print(f"Failed: {failed} ({failed/total*100:.1f}%)")
            print(f"Created: {created} ({created/total*100:.1f}%)")
            print(f"Updated: {updated} ({updated/total*100:.1f}%)")
            print(f"Skipped: {skipped} ({skipped/total*100:.1f}%)")
        else:
            print("No printing assets found to migrate")
        
        print("-" * 80)
        
        # Print matching statistics
        matching_stats = statistics.get("matching", {})
        if matching_stats and total > 0:
            print("Matching Statistics:")
            
            # Match types
            match_types = matching_stats.get("by_match_type", {})
            if match_types:
                print("  Match Types:")
                for match_type, data in match_types.items():
                    count = data.get("count", 0)
                    percentage = data.get("percentage", 0)
                    print(f"    {match_type}: {count} ({percentage:.1f}%)")
            
            # Recommended actions
            actions = matching_stats.get("by_recommended_action", {})
            if actions:
                print("  Recommended Actions:")
                for action, data in actions.items():
                    count = data.get("count", 0)
                    percentage = data.get("percentage", 0)
                    print(f"    {action}: {count} ({percentage:.1f}%)")
            
            # Data quality
            quality = matching_stats.get("by_data_quality", {})
            if quality:
                print("  Data Quality:")
                for quality_type, data in quality.items():
                    count = data.get("count", 0)
                    percentage = data.get("percentage", 0)
                    print(f"    {quality_type}: {count} ({percentage:.1f}%)")
            
            # Printer types
            printer_types = matching_stats.get("by_printer_type", {})
            if printer_types:
                print("  Printer Types:")
                for printer_type, data in printer_types.items():
                    count = data.get("count", 0)
                    percentage = data.get("percentage", 0)
                    print(f"    {printer_type}: {count} ({percentage:.1f}%)")
        
        print("-" * 80)
        print(f"Report saved to: {self.report_file}")
        print("=" * 80)