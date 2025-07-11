"""
Email migrator for the migration demo.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict

from itglue_client import ITGlueClient
from servicenow_mock import ServiceNowMock
from email_matcher import EmailMatcher, EmailMatch, DataQualityIssue
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


class EmailMigrator:
    """Migrates email assets from IT Glue to ServiceNow."""
    
    def __init__(self, use_mock_data: bool = True):
        """
        Initialize email migrator.
        
        Args:
            use_mock_data: Whether to use mock data instead of making API calls
        """
        self.logger = logging.getLogger(__name__)
        self.use_mock_data = use_mock_data
        
        # Initialize clients
        self.itglue_client = ITGlueClient(use_mock_data=use_mock_data)
        self.servicenow_client = ServiceNowMock()
        
        # Initialize matcher and mapper
        self.matcher = EmailMatcher()
        self.field_mapper = FieldMapper()
        
        # Output settings
        self.output_settings = config.get("output", {})
        self.report_file = self.output_settings.get("email_report_file", "email_migration_report.json")
        self.console_output = self.output_settings.get("console_output", True)
        
        self.logger.info(f"Email Migrator initialized (use_mock_data={use_mock_data})")
    
    def migrate_emails(self) -> Tuple[List[MigrationResult], Dict[str, Any]]:
        """
        Migrate email assets from IT Glue to ServiceNow.
        
        Returns:
            Tuple of (migration results, statistics)
        """
        self.logger.info("Starting email migration")
        
        # Test connections
        if not self._test_connections():
            self.logger.error("Connection test failed")
            return [], {"total_emails": 0, "successful": 0, "failed": 0}
        
        # Fetch data
        itglue_emails = self.itglue_client.get_emails()
        servicenow_email_services = self.servicenow_client.get_email_services()
        
        # Match emails
        matches, quality_issues = self.matcher.match_email_assets(
            itglue_emails, servicenow_email_services
        )
        
        # If no emails were found, return empty results
        if not matches:
            self.logger.warning("No email assets found to migrate")
            empty_stats = {
                "total_emails": 0,
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
        
        # Migrate emails
        migration_results = []
        
        for i, (email, match) in enumerate(zip(itglue_emails, matches), 1):
            self.logger.info(f"Migrating email {i}/{len(itglue_emails)}: {match.itglue_name}")
            
            if self.console_output:
                self._print_migration_header(i, len(itglue_emails), email, match)
            
            # Migrate email
            result = self._migrate_single_email(email, match)
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
    
    def _migrate_single_email(self, email: Dict[str, Any], match: EmailMatch) -> MigrationResult:
        """
        Migrate a single email asset.
        
        Args:
            email: IT Glue email asset data
            match: Email match result
            
        Returns:
            Migration result
        """
        try:
            # Skip emails that should not be migrated
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
            
            # Map IT Glue email to ServiceNow email service
            email_service_data = self.field_mapper.map_email(email, match)
            
            # Create or update email service in ServiceNow
            if match.recommended_action == "Use Existing" or match.recommended_action == "Review Match":
                # Update existing email service
                updated_service = self.servicenow_client.update_email_service(
                    match.servicenow_id, email_service_data
                )
                
                if updated_service:
                    return MigrationResult(
                        itglue_id=match.itglue_id,
                        itglue_name=match.itglue_name,
                        servicenow_id=updated_service.get("sys_id"),
                        servicenow_name=updated_service.get("name"),
                        match_type=match.match_type,
                        confidence=match.confidence,
                        action="updated",
                        status="success",
                        notes=f"Updated existing email service: {match.notes}"
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
                        error_message="Failed to update email service",
                        notes=f"Failed to update email service: {match.notes}"
                    )
            else:
                # Create new email service
                created_service = self.servicenow_client.create_email_service(email_service_data)
                
                return MigrationResult(
                    itglue_id=match.itglue_id,
                    itglue_name=match.itglue_name,
                    servicenow_id=created_service.get("sys_id"),
                    servicenow_name=created_service.get("name"),
                    match_type=match.match_type,
                    confidence=match.confidence,
                    action="created",
                    status="success",
                    notes=f"Created new email service: {match.notes}"
                )
            
        except Exception as e:
            self.logger.exception(f"Failed to migrate email {match.itglue_name}: {e}")
            
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
                           matches: List[EmailMatch],
                           quality_issues: List[DataQualityIssue]) -> Dict[str, Any]:
        """
        Generate statistics from migration results.
        
        Args:
            results: Migration results
            matches: Email matches
            quality_issues: Data quality issues
            
        Returns:
            Statistics dictionary
        """
        total = len(results)
        
        # Basic statistics
        stats = {
            "total_emails": total,
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
            with open(self.report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            self.logger.info(f"Migration report saved to {self.report_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save migration report: {e}")
    
    def _print_migration_header(self, index: int, total: int, email: Dict[str, Any], match: EmailMatch) -> None:
        """
        Print migration header.
        
        Args:
            index: Current index
            total: Total number of emails
            email: IT Glue email asset data
            match: Email match result
        """
        email_name = match.itglue_name
        
        print("\n" + "=" * 80)
        print(f"Migrating email {index}/{total}: {email_name}")
        print("-" * 80)
        print(f"IT Glue ID: {match.itglue_id}")
        print(f"Email Type: {match.email_type or 'Unknown'}")
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
            print(f"ServiceNow Email Service: {result.servicenow_name} (ID: {result.servicenow_id})")
        
        if result.error_message:
            print(f"Error: {result.error_message}")
        
        print("=" * 80)
    
    def _print_migration_summary(self, statistics: Dict[str, Any]) -> None:
        """
        Print migration summary.
        
        Args:
            statistics: Migration statistics
        """
        total = statistics["total_emails"]
        successful = statistics["successful"]
        failed = statistics["failed"]
        created = statistics["created"]
        updated = statistics["updated"]
        skipped = statistics["skipped"]
        
        print("\n" + "=" * 80)
        print("Email Migration Summary")
        print("=" * 80)
        print(f"Total Email Assets: {total}")
        
        # Avoid division by zero
        if total > 0:
            print(f"Successful: {successful} ({successful/total*100:.1f}%)")
            print(f"Failed: {failed} ({failed/total*100:.1f}%)")
            print(f"Created: {created} ({created/total*100:.1f}%)")
            print(f"Updated: {updated} ({updated/total*100:.1f}%)")
            print(f"Skipped: {skipped} ({skipped/total*100:.1f}%)")
        else:
            print("No email assets found to migrate")
        
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
            
            # Email types
            email_types = matching_stats.get("by_email_type", {})
            if email_types:
                print("  Email Types:")
                for email_type, data in email_types.items():
                    count = data.get("count", 0)
                    percentage = data.get("percentage", 0)
                    print(f"    {email_type}: {count} ({percentage:.1f}%)")
        
        print("-" * 80)
        print(f"Report saved to: {self.report_file}")
        print("=" * 80)