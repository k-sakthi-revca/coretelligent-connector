"""
LoB applications migrator for the migration.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict

from itglue_client import ITGlueClient
from servicenow_mock import ServiceNowMock
from matchers.lob_applications_matcher import LoBApplicationsMatcher, LoBApplicationMatch, DataQualityIssue
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


class LoBApplicationsMigrator:
    """Migrates LoB application assets from IT Glue to ServiceNow."""
    
    def __init__(self, use_mock_data: bool = True):
        """
        Initialize LoB applications migrator.
        
        Args:
            use_mock_data: Whether to use mock data instead of making API calls
        """
        self.logger = logging.getLogger(__name__)
        self.use_mock_data = use_mock_data
        
        # Initialize clients
        self.itglue_client = ITGlueClient(use_mock_data=use_mock_data)
        self.servicenow_client = ServiceNowMock()
        
        # Initialize matcher and mapper
        self.matcher = LoBApplicationsMatcher()
        self.field_mapper = FieldMapper()
        
        # Output settings
        self.output_settings = config.get("output", {})
        self.report_file = self.output_settings.get("lob_applications_report_file", "reports/lob_applications_migration_report.json")
        self.console_output = self.output_settings.get("console_output", True)
        
        self.logger.info(f"LoB Applications Migrator initialized (use_mock_data={use_mock_data})")
    
    def migrate_lob_applications(self) -> Tuple[List[MigrationResult], Dict[str, Any]]:
        """
        Migrate LoB application assets from IT Glue to ServiceNow.
        
        Returns:
            Tuple of (migration results, statistics)
        """
        self.logger.info("Starting LoB applications migration")
        
        # Test connections
        if not self._test_connections():
            self.logger.error("Connection test failed")
            return [], {"total_applications": 0, "successful": 0, "failed": 0}
        
        # Fetch data
        itglue_applications = self.itglue_client.get_lob_applications()
        servicenow_applications = self.servicenow_client.get_applications()
        
        # Match applications
        matches, quality_issues = self.matcher.match_lob_applications(
            itglue_applications, servicenow_applications
        )
        
        # If no applications were found, return empty results
        if not matches:
            self.logger.warning("No LoB application assets found to migrate")
            empty_stats = {
                "total_applications": 0,
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
        
        # Migrate applications
        migration_results = []
        
        for i, (application, match) in enumerate(zip(itglue_applications, matches), 1):
            self.logger.info(f"Migrating application {i}/{len(itglue_applications)}: {match.itglue_name}")
            
            if self.console_output:
                self._print_migration_header(i, len(itglue_applications), application, match)
            
            # Migrate application
            result = self._migrate_single_application(application, match)
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
    
    def _migrate_single_application(self, application: Dict[str, Any], match: LoBApplicationMatch) -> MigrationResult:
        """
        Migrate a single LoB application asset.
        
        Args:
            application: IT Glue LoB application asset data
            match: LoB application match result
            
        Returns:
            Migration result
        """
        try:
            # Skip applications that should not be migrated
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
            
            # Map IT Glue application to ServiceNow application CI
            application_data = self.field_mapper.map_lob_application(application, match)
            
            # Create or update application CI in ServiceNow
            if match.recommended_action == "Use Existing" or match.recommended_action == "Review Match":
                # Update existing application CI
                updated_application = self.servicenow_client.update_application(
                    match.servicenow_id, application_data
                )
                
                if updated_application:
                    return MigrationResult(
                        itglue_id=match.itglue_id,
                        itglue_name=match.itglue_name,
                        servicenow_id=updated_application.get("sys_id"),
                        servicenow_name=updated_application.get("name"),
                        match_type=match.match_type,
                        confidence=match.confidence,
                        action="updated",
                        status="success",
                        notes=f"Updated existing application CI: {match.notes}"
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
                        error_message="Failed to update application CI",
                        notes=f"Failed to update application CI: {match.notes}"
                    )
            else:
                # Create new application CI
                created_application = self.servicenow_client.create_application(application_data)
                
                return MigrationResult(
                    itglue_id=match.itglue_id,
                    itglue_name=match.itglue_name,
                    servicenow_id=created_application.get("sys_id"),
                    servicenow_name=created_application.get("name"),
                    match_type=match.match_type,
                    confidence=match.confidence,
                    action="created",
                    status="success",
                    notes=f"Created new application CI: {match.notes}"
                )
            
        except Exception as e:
            self.logger.exception(f"Failed to migrate application {match.itglue_name}: {e}")
            
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
                           matches: List[LoBApplicationMatch],
                           quality_issues: List[DataQualityIssue]) -> Dict[str, Any]:
        """
        Generate statistics from migration results.
        
        Args:
            results: Migration results
            matches: LoB application matches
            quality_issues: Data quality issues
            
        Returns:
            Statistics dictionary
        """
        total = len(results)
        
        # Basic statistics
        stats = {
            "total_applications": total,
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
    
    def _print_migration_header(self, index: int, total: int, application: Dict[str, Any], match: LoBApplicationMatch) -> None:
        """
        Print migration header.
        
        Args:
            index: Current index
            total: Total number of applications
            application: IT Glue LoB application asset data
            match: LoB application match result
        """
        application_name = match.itglue_name
        
        print("\n" + "=" * 80)
        print(f"Migrating application {index}/{total}: {application_name}")
        print("-" * 80)
        print(f"IT Glue ID: {match.itglue_id}")
        print(f"Application Type: {match.application_type or 'Unknown'}")
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
            print(f"ServiceNow Application CI: {result.servicenow_name} (ID: {result.servicenow_id})")
        
        if result.error_message:
            print(f"Error: {result.error_message}")
        
        print("=" * 80)
    
    def _print_migration_summary(self, statistics: Dict[str, Any]) -> None:
        """
        Print migration summary.
        
        Args:
            statistics: Migration statistics
        """
        total = statistics["total_applications"]
        successful = statistics["successful"]
        failed = statistics["failed"]
        created = statistics["created"]
        updated = statistics["updated"]
        skipped = statistics["skipped"]
        
        print("\n" + "=" * 80)
        print("LoB Applications Migration Summary")
        print("=" * 80)
        print(f"Total LoB Application Assets: {total}")
        
        # Avoid division by zero
        if total > 0:
            print(f"Successful: {successful} ({successful/total*100:.1f}%)")
            print(f"Failed: {failed} ({failed/total*100:.1f}%)")
            print(f"Created: {created} ({created/total*100:.1f}%)")
            print(f"Updated: {updated} ({updated/total*100:.1f}%)")
            print(f"Skipped: {skipped} ({skipped/total*100:.1f}%)")
        else:
            print("No LoB application assets found to migrate")
        
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
            
            # Application types
            application_types = matching_stats.get("by_application_type", {})
            if application_types:
                print("  Application Types:")
                for application_type, data in application_types.items():
                    count = data.get("count", 0)
                    percentage = data.get("percentage", 0)
                    print(f"    {application_type}: {count} ({percentage:.1f}%)")
        
        print("-" * 80)
        print(f"Report saved to: {self.report_file}")
        print("=" * 80)