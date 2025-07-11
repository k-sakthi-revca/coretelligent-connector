"""
LoB applications matcher for the migration.
"""

import re
import logging
from difflib import SequenceMatcher
from dataclasses import dataclass
from typing import Dict, List, Any, Tuple, Optional

from config import config


@dataclass
class LoBApplicationMatch:
    """Result of matching an IT Glue LoB application asset to a ServiceNow application CI."""
    itglue_id: str
    itglue_name: str
    servicenow_id: Optional[str]
    servicenow_name: Optional[str]
    match_type: str  # 'Exact Name', 'Fuzzy Name', 'No Match'
    confidence: float  # 0.0 to 1.0
    recommended_action: str  # 'Use Existing', 'Review Match', 'Create New', 'Skip'
    data_quality: str  # '✅ Ready', '⚠️ Missing Data', '❌ Invalid Data'
    application_type: Optional[str] = None
    notes: str = ""


@dataclass
class DataQualityIssue:
    """Data quality issue for a LoB application asset."""
    asset_id: str
    asset_name: str
    issue_type: str  # 'Missing Required Field', 'Similar Name', 'Invalid Application Type'
    priority: str  # 'High', 'Medium', 'Low'
    description: str
    recommendation: str


class LoBApplicationsMatcher:
    """Matches IT Glue LoB application assets to ServiceNow application CIs."""
    
    def __init__(self):
        """Initialize LoB applications matcher."""
        self.logger = logging.getLogger(__name__)
        self.matching_settings = config.get("lob_applications_matching", {})
        
        # Extract matching settings or use defaults if not specified
        self.strategies = self.matching_settings.get("strategies", ["exact_name", "fuzzy_name"])
        self.fuzzy_threshold = self.matching_settings.get("fuzzy_matching", {}).get("threshold", 0.8)
        self.review_threshold = self.matching_settings.get("fuzzy_matching", {}).get("review_threshold", 0.95)
        self.normalization_patterns = self.matching_settings.get("normalization_patterns", [])
        
        # Valid application categories
        self.valid_categories = self.matching_settings.get("valid_categories", [
            "Analytics", "Automation", "Billing & Payments", "Compliance", "CRM", 
            "Database", "Development", "ERP", "Encryption", "File Sharing/Hosting", 
            "Finance", "Fleet Management", "HR/HRIS", "IT Tools", "Logistics / Shipping", 
            "Marketing/Media Creation", "Patient Information Management (PIMS)", "Payroll", 
            "Productivity", "Sales", "Security", "RMM", "Social Media", "Text Chat/IM", 
            "Voice/Video Conferencing", "Web Browser", "Other"
        ])
        
        self.logger.info(f"LoB Applications Matcher initialized with strategies: {', '.join(self.strategies)}")
    
    def match_lob_applications(self, 
                         itglue_assets: List[Dict], 
                         servicenow_applications: List[Dict]) -> Tuple[List[LoBApplicationMatch], List[DataQualityIssue]]:
        """
        Match IT Glue LoB application assets to ServiceNow application CIs.
        
        Args:
            itglue_assets: List of IT Glue LoB application asset data
            servicenow_applications: List of ServiceNow application CI data
            
        Returns:
            Tuple of (matches, data quality issues)
        """
        self.logger.info(f"Matching {len(itglue_assets)} IT Glue LoB application assets to {len(servicenow_applications)} ServiceNow application CIs")
        
        # Match each asset
        matches = []
        quality_issues = []
        
        for asset in itglue_assets:
            asset_id = asset.get("id")
            attributes = asset.get("attributes", {})
            asset_name = attributes.get("name", "Unknown")
            
            # Get traits
            traits = attributes.get("traits", {})
            category = traits.get("category", "Unknown")
            version = traits.get("version", "")
            
            # Match asset
            match_result = self.match_single_asset(
                asset_id, asset_name, category, version, servicenow_applications
            )
            
            # Assess data quality
            quality_label, quality_issue = self._assess_data_quality(
                asset_id, asset_name, category, traits, match_result
            )
            
            # Update match result with data quality
            match_result.data_quality = quality_label
            
            # Add to results
            matches.append(match_result)
            
            if quality_issue:
                quality_issues.append(quality_issue)
        
        self.logger.info(f"Matched {len(matches)} LoB application assets with {len(quality_issues)} data quality issues")
        return matches, quality_issues
    
    def match_single_asset(self, 
                         asset_id: str, 
                         asset_name: str, 
                         category: str,
                         version: str,
                         servicenow_applications: List[Dict]) -> LoBApplicationMatch:
        """
        Match a single IT Glue LoB application asset to a ServiceNow application CI.
        
        Args:
            asset_id: IT Glue asset ID
            asset_name: IT Glue asset name
            category: Application category
            version: Application version
            servicenow_applications: List of ServiceNow application CI data
            
        Returns:
            Match result
        """
        # Try each matching strategy in order
        for strategy in self.strategies:
            if strategy == "exact_name":
                # Try exact name matching
                match = self._match_by_exact_name(asset_id, asset_name, category, version, servicenow_applications)
                if match:
                    return match
            
            elif strategy == "fuzzy_name":
                # Try fuzzy name matching
                match = self._match_by_fuzzy_name(asset_id, asset_name, category, version, servicenow_applications)
                if match:
                    return match
        
        # No match found
        return self._create_no_match_result(asset_id, asset_name, category)
    
    def _match_by_exact_name(self, 
                           asset_id: str, 
                           asset_name: str,
                           category: str,
                           version: str,
                           servicenow_applications: List[Dict]) -> Optional[LoBApplicationMatch]:
        """
        Match by exact normalized name.
        
        Args:
            asset_id: IT Glue asset ID
            asset_name: IT Glue asset name
            category: Application category
            version: Application version
            servicenow_applications: List of ServiceNow application CI data
            
        Returns:
            Match result or None if no match
        """
        normalized_asset_name = self._normalize_application_name(asset_name)
        
        for application in servicenow_applications:
            application_name = application.get("name", "")
            application_version = application.get("version", "")
            normalized_application_name = self._normalize_application_name(application_name)
            
            if normalized_asset_name and normalized_application_name and normalized_asset_name == normalized_application_name:
                # Check version if available
                if version and application_version and version != application_version:
                    continue
                
                return LoBApplicationMatch(
                    itglue_id=asset_id,
                    itglue_name=asset_name,
                    servicenow_id=application.get("sys_id"),
                    servicenow_name=application_name,
                    match_type="Exact Name",
                    confidence=1.0,
                    recommended_action="Use Existing",
                    data_quality="✅ Ready",
                    application_type=category,
                    notes=f"Matched by exact normalized name: {normalized_asset_name}"
                )
        
        return None
    
    def _match_by_fuzzy_name(self, 
                           asset_id: str, 
                           asset_name: str,
                           category: str,
                           version: str,
                           servicenow_applications: List[Dict]) -> Optional[LoBApplicationMatch]:
        """
        Match by fuzzy name similarity.
        
        Args:
            asset_id: IT Glue asset ID
            asset_name: IT Glue asset name
            category: Application category
            version: Application version
            servicenow_applications: List of ServiceNow application CI data
            
        Returns:
            Match result or None if no match
        """
        normalized_asset_name = self._normalize_application_name(asset_name)
        
        best_match = None
        best_similarity = 0.0
        
        for application in servicenow_applications:
            application_name = application.get("name", "")
            application_version = application.get("version", "")
            normalized_application_name = self._normalize_application_name(application_name)
            
            if normalized_asset_name and normalized_application_name:
                similarity = SequenceMatcher(None, normalized_asset_name, normalized_application_name).ratio()
                
                if similarity > best_similarity and similarity >= self.fuzzy_threshold:
                    # Check version if available
                    if version and application_version and version != application_version:
                        continue
                    
                    best_similarity = similarity
                    best_match = application
        
        if best_match:
            # Determine recommended action based on confidence
            if best_similarity >= self.review_threshold:
                action = "Use Existing"
                notes = f"Matched by similar name with high confidence: {best_similarity:.1%}"
            else:
                action = "Review Match"
                notes = f"Matched by similar name with moderate confidence: {best_similarity:.1%}"
            
            return LoBApplicationMatch(
                itglue_id=asset_id,
                itglue_name=asset_name,
                servicenow_id=best_match.get("sys_id"),
                servicenow_name=best_match.get("name"),
                match_type="Fuzzy Name",
                confidence=best_similarity,
                recommended_action=action,
                data_quality="✅ Ready",
                application_type=category,
                notes=notes
            )
        
        return None
    
    def _create_no_match_result(self, 
                              asset_id: str, 
                              asset_name: str, 
                              category: str) -> LoBApplicationMatch:
        """
        Create a no-match result.
        
        Args:
            asset_id: IT Glue asset ID
            asset_name: IT Glue asset name
            category: Application category
            
        Returns:
            No-match result
        """
        return LoBApplicationMatch(
            itglue_id=asset_id,
            itglue_name=asset_name,
            servicenow_id=None,
            servicenow_name=None,
            match_type="No Match",
            confidence=0.0,
            recommended_action="Create New",
            data_quality="✅ Ready",
            application_type=category,
            notes="No matching application found in ServiceNow"
        )
    
    def _normalize_application_name(self, name: str) -> str:
        """
        Normalize application name for comparison.
        
        Args:
            name: Application name
            
        Returns:
            Normalized name
        """
        if not name:
            return ""
        
        # Convert to lowercase
        normalized = name.lower()
        
        # Apply normalization patterns
        for pattern in self.normalization_patterns:
            regex = pattern.get("pattern", "")
            replacement = pattern.get("replacement", "")
            
            if regex:
                normalized = re.sub(regex, replacement, normalized)
        
        # Remove common suffixes
        suffixes = [
            r" application$", r" app$", r" service$", r" server$",
            r" \d{4}$", r" \d{2}$", r" v\d+$", r" version \d+$"
        ]
        for suffix in suffixes:
            normalized = re.sub(suffix, "", normalized)
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _assess_data_quality(self, 
                           asset_id: str, 
                           asset_name: str, 
                           category: str,
                           traits: Dict[str, Any],
                           match_result: LoBApplicationMatch) -> Tuple[str, Optional[DataQualityIssue]]:
        """
        Assess data quality for a LoB application asset.
        
        Args:
            asset_id: IT Glue asset ID
            asset_name: IT Glue asset name
            category: Application category
            traits: Asset traits
            match_result: Match result
            
        Returns:
            Tuple of (quality label, quality issue or None)
        """
        # Check for invalid category
        if category and category not in self.valid_categories:
            return "⚠️ Invalid Category", DataQualityIssue(
                asset_id=asset_id,
                asset_name=asset_name,
                issue_type="Invalid Application Type",
                priority="Medium",
                description=f"Application category '{category}' is not in the list of valid categories",
                recommendation="Update application category to a valid value"
            )
        
        # Check for fuzzy matches with low confidence
        if match_result.match_type == "Fuzzy Name" and match_result.confidence < self.review_threshold:
            return "⚠️ Similar Name", DataQualityIssue(
                asset_id=asset_id,
                asset_name=asset_name,
                issue_type="Similar Name",
                priority="High",
                description=f"Asset matched by similar name with {match_result.confidence:.1%} confidence",
                recommendation="Review match and confirm or create new"
            )
        
        # Check for missing required fields
        required_fields = ["name", "application-manager"]
        missing_fields = []
        
        for field in required_fields:
            if field not in traits:
                missing_fields.append(field)
            elif not traits.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            return "❌ Missing Data", DataQualityIssue(
                asset_id=asset_id,
                asset_name=asset_name,
                issue_type="Missing Required Field",
                priority="High",
                description=f"Asset is missing required fields: {', '.join(missing_fields)}",
                recommendation="Complete asset data in IT Glue"
            )
        
        return "✅ Ready", None
    
    def generate_matching_statistics(self, matches: List[LoBApplicationMatch]) -> Dict[str, Any]:
        """
        Generate statistics from matching results.
        
        Args:
            matches: List of match results
            
        Returns:
            Statistics dictionary
        """
        total = len(matches)
        if total == 0:
            return {}
        
        # Count by match type
        match_types = {}
        for match in matches:
            match_type = match.match_type
            if match_type not in match_types:
                match_types[match_type] = {"count": 0, "percentage": 0.0}
            match_types[match_type]["count"] += 1
        
        # Calculate percentages
        for match_type in match_types:
            match_types[match_type]["percentage"] = match_types[match_type]["count"] / total * 100
        
        # Count by recommended action
        actions = {}
        for match in matches:
            action = match.recommended_action
            if action not in actions:
                actions[action] = {"count": 0, "percentage": 0.0}
            actions[action]["count"] += 1
        
        # Calculate percentages
        for action in actions:
            actions[action]["percentage"] = actions[action]["count"] / total * 100
        
        # Count by data quality
        quality = {}
        for match in matches:
            quality_label = match.data_quality
            if quality_label not in quality:
                quality[quality_label] = {"count": 0, "percentage": 0.0}
            quality[quality_label]["count"] += 1
        
        # Calculate percentages
        for quality_label in quality:
            quality[quality_label]["percentage"] = quality[quality_label]["count"] / total * 100
        
        # Count by application type
        application_types = {}
        for match in matches:
            application_type = match.application_type or "Unknown"
            if application_type not in application_types:
                application_types[application_type] = {"count": 0, "percentage": 0.0}
            application_types[application_type]["count"] += 1
        
        # Calculate percentages
        for application_type in application_types:
            application_types[application_type]["percentage"] = application_types[application_type]["count"] / total * 100
        
        return {
            "total": total,
            "by_match_type": match_types,
            "by_recommended_action": actions,
            "by_data_quality": quality,
            "by_application_type": application_types
        }