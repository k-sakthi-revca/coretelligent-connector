"""
Report generator for the migration demo.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from models.match_models import OrganizationMatch, VirtualizationMatch, DataQualityIssue
from utils.file_utils import save_json_file


class ReportGenerator:
    """Generates reports for migration results."""
    
    def __init__(self, output_dir: str = "reports"):
        """
        Initialize report generator.
        
        Args:
            output_dir: Directory to save reports
        """
        self.logger = logging.getLogger(__name__)
        self.output_dir = output_dir
    
    def generate_organization_report(self, 
                                   matches: List[OrganizationMatch], 
                                   quality_issues: List[DataQualityIssue],
                                   stats: Dict[str, Any],
                                   file_name: Optional[str] = None) -> str:
        """
        Generate organization matching report.
        
        Args:
            matches: List of organization match results
            quality_issues: List of data quality issues
            stats: Matching statistics
            file_name: Output file name (optional)
            
        Returns:
            Path to the generated report
        """
        self.logger.info("Generating organization matching report...")
        
        # Create report data
        report_data = self._create_organization_report_data(matches, quality_issues, stats)
        
        # Generate file name if not provided
        if not file_name:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_name = f"organization_migration_report_{timestamp}.json"
        
        # Save report
        file_path = f"{self.output_dir}/{file_name}"
        save_json_file(report_data, file_path)
        
        self.logger.info(f"Organization report saved to {file_path}")
        return file_path
    
    def generate_virtualization_report(self, 
                                     matches: List[VirtualizationMatch], 
                                     quality_issues: List[DataQualityIssue],
                                     stats: Dict[str, Any],
                                     file_name: Optional[str] = None) -> str:
        """
        Generate virtualization matching report.
        
        Args:
            matches: List of virtualization match results
            quality_issues: List of data quality issues
            stats: Matching statistics
            file_name: Output file name (optional)
            
        Returns:
            Path to the generated report
        """
        self.logger.info("Generating virtualization matching report...")
        
        # Create report data
        report_data = self._create_virtualization_report_data(matches, quality_issues, stats)
        
        # Generate file name if not provided
        if not file_name:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_name = f"virtualization_migration_report_{timestamp}.json"
        
        # Save report
        file_path = f"{self.output_dir}/{file_name}"
        save_json_file(report_data, file_path)
        
        self.logger.info(f"Virtualization report saved to {file_path}")
        return file_path
    
    def _create_organization_report_data(self, 
                                       matches: List[OrganizationMatch], 
                                       quality_issues: List[DataQualityIssue],
                                       stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create organization report data.
        
        Args:
            matches: List of organization match results
            quality_issues: List of data quality issues
            stats: Matching statistics
            
        Returns:
            Report data dictionary
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
                "coreid": match.coreid,
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
        return {
            "report_type": "organization_matching",
            "timestamp": datetime.now().isoformat(),
            "statistics": stats,
            "matches": matches_dict,
            "quality_issues": issues_dict
        }
    
    def _create_virtualization_report_data(self, 
                                         matches: List[VirtualizationMatch], 
                                         quality_issues: List[DataQualityIssue],
                                         stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create virtualization report data.
        
        Args:
            matches: List of virtualization match results
            quality_issues: List of data quality issues
            stats: Matching statistics
            
        Returns:
            Report data dictionary
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
        return {
            "report_type": "virtualization_matching",
            "timestamp": datetime.now().isoformat(),
            "statistics": stats,
            "matches": matches_dict,
            "quality_issues": issues_dict
        }
    
    def print_organization_report_summary(self, 
                                        matches: List[OrganizationMatch], 
                                        quality_issues: List[DataQualityIssue],
                                        stats: Dict[str, Any]) -> None:
        """
        Print organization report summary to console.
        
        Args:
            matches: List of organization match results
            quality_issues: List of data quality issues
            stats: Matching statistics
        """
        print("\n" + "=" * 80)
        print(f"ORGANIZATION MATCHING RESULTS ({stats['total']} organizations)")
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
        
        # Print match details
        print("\nMATCH DETAILS:")
        for i, match in enumerate(matches, 1):
            print(f"\n{i}. {match.itglue_name}")
            print(f"   Match Type: {match.match_type}")
            print(f"   Confidence: {match.confidence:.1%}")
            print(f"   Action: {match.recommended_action}")
            print(f"   Quality: {match.data_quality}")
            
            if match.servicenow_id:
                print(f"   ServiceNow: {match.servicenow_name} (ID: {match.servicenow_id})")
            
            if match.coreid:
                print(f"   CoreID: {match.coreid}")
            
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
    
    def print_virtualization_report_summary(self, 
                                          matches: List[VirtualizationMatch], 
                                          quality_issues: List[DataQualityIssue],
                                          stats: Dict[str, Any]) -> None:
        """
        Print virtualization report summary to console.
        
        Args:
            matches: List of virtualization match results
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