"""
Email matcher for the migration demo.
"""

import re
import logging
from difflib import SequenceMatcher
from dataclasses import dataclass
from typing import Dict, List, Any, Tuple, Optional

from config import config


@dataclass
class EmailMatch:
    """Result of matching an IT Glue email asset to a ServiceNow email service."""
    itglue_id: str
    itglue_name: str
    servicenow_id: Optional[str]
    servicenow_name: Optional[str]
    match_type: str  # 'Exact Name', 'Fuzzy Name', 'No Match'
    confidence: float  # 0.0 to 1.0
    recommended_action: str  # 'Use Existing', 'Review Match', 'Create New', 'Skip'
    data_quality: str  # '✅ Ready', '⚠️ Missing Data', '❌ Invalid Data'
    email_type: Optional[str] = None
    notes: str = ""


@dataclass
class DataQualityIssue:
    """Data quality issue for an email asset."""
    asset_id: str
    asset_name: str
    issue_type: str  # 'Missing Required Field', 'Similar Name', 'Invalid Email Type'
    priority: str  # 'High', 'Medium', 'Low'
    description: str
    recommendation: str


class EmailMatcher:
    """Matches IT Glue email assets to ServiceNow email services."""
    
    def __init__(self):
        """Initialize email matcher."""
        self.logger = logging.getLogger(__name__)
        self.matching_settings = config.get("email_matching", {})
        
        # Extract matching settings or use defaults if not specified
        self.strategies = self.matching_settings.get("strategies", ["exact_name", "fuzzy_name"])
        self.fuzzy_threshold = self.matching_settings.get("fuzzy_matching", {}).get("threshold", 0.8)
        self.review_threshold = self.matching_settings.get("fuzzy_matching", {}).get("review_threshold", 0.95)
        self.normalization_patterns = self.matching_settings.get("normalization_patterns", [])
        
        # Valid email types
        self.valid_email_types = self.matching_settings.get("valid_email_types", [
            "Microsoft 365", "Google Apps", "Exchange 2019", "Exchange 2016", 
            "Exchange 2013", "Office 365", "Other"
        ])
        
        self.logger.info(f"Email Matcher initialized with strategies: {', '.join(self.strategies)}")
    
    def match_email_assets(self, 
                         itglue_assets: List[Dict], 
                         servicenow_email_services: List[Dict]) -> Tuple[List[EmailMatch], List[DataQualityIssue]]:
        """
        Match IT Glue email assets to ServiceNow email services.
        
        Args:
            itglue_assets: List of IT Glue email asset data
            servicenow_email_services: List of ServiceNow email service data
            
        Returns:
            Tuple of (matches, data quality issues)
        """
        self.logger.info(f"Matching {len(itglue_assets)} IT Glue email assets to {len(servicenow_email_services)} ServiceNow email services")
        
        # Match each asset
        matches = []
        quality_issues = []
        
        for asset in itglue_assets:
            asset_id = asset.get("id")
            attributes = asset.get("attributes", {})
            asset_name = attributes.get("name", "Unknown")
            
            # Get traits
            traits = attributes.get("traits", {})
            email_type = traits.get("type", "Unknown")
            
            # Match asset
            match_result = self.match_single_asset(
                asset_id, asset_name, email_type, servicenow_email_services
            )
            
            # Assess data quality
            quality_label, quality_issue = self._assess_data_quality(
                asset_id, asset_name, email_type, traits, match_result
            )
            
            # Update match result with data quality
            match_result.data_quality = quality_label
            
            # Add to results
            matches.append(match_result)
            
            if quality_issue:
                quality_issues.append(quality_issue)
        
        self.logger.info(f"Matched {len(matches)} email assets with {len(quality_issues)} data quality issues")
        return matches, quality_issues
    
    def match_single_asset(self, 
                         asset_id: str, 
                         asset_name: str, 
                         email_type: str,
                         servicenow_email_services: List[Dict]) -> EmailMatch:
        """
        Match a single IT Glue email asset to a ServiceNow email service.
        
        Args:
            asset_id: IT Glue asset ID
            asset_name: IT Glue asset name
            email_type: Email type
            servicenow_email_services: List of ServiceNow email service data
            
        Returns:
            Match result
        """
        # Try each matching strategy in order
        for strategy in self.strategies:
            if strategy == "exact_name":
                # Try exact name matching
                match = self._match_by_exact_name(asset_id, asset_name, email_type, servicenow_email_services)
                if match:
                    return match
            
            elif strategy == "fuzzy_name":
                # Try fuzzy name matching
                match = self._match_by_fuzzy_name(asset_id, asset_name, email_type, servicenow_email_services)
                if match:
                    return match
        
        # No match found
        return self._create_no_match_result(asset_id, asset_name, email_type)
    
    def _match_by_exact_name(self, 
                           asset_id: str, 
                           asset_name: str,
                           email_type: str,
                           servicenow_email_services: List[Dict]) -> Optional[EmailMatch]:
        """
        Match by exact normalized name.
        
        Args:
            asset_id: IT Glue asset ID
            asset_name: IT Glue asset name
            email_type: Email type
            servicenow_email_services: List of ServiceNow email service data
            
        Returns:
            Match result or None if no match
        """
        normalized_asset_name = self._normalize_email_name(asset_name)
        
        for service in servicenow_email_services:
            service_name = service.get("name", "")
            normalized_service_name = self._normalize_email_name(service_name)
            
            if normalized_asset_name and normalized_service_name and normalized_asset_name == normalized_service_name:
                return EmailMatch(
                    itglue_id=asset_id,
                    itglue_name=asset_name,
                    servicenow_id=service.get("sys_id"),
                    servicenow_name=service_name,
                    match_type="Exact Name",
                    confidence=1.0,
                    recommended_action="Use Existing",
                    data_quality="✅ Ready",
                    email_type=email_type,
                    notes=f"Matched by exact normalized name: {normalized_asset_name}"
                )
        
        return None
    
    def _match_by_fuzzy_name(self, 
                           asset_id: str, 
                           asset_name: str,
                           email_type: str,
                           servicenow_email_services: List[Dict]) -> Optional[EmailMatch]:
        """
        Match by fuzzy name similarity.
        
        Args:
            asset_id: IT Glue asset ID
            asset_name: IT Glue asset name
            email_type: Email type
            servicenow_email_services: List of ServiceNow email service data
            
        Returns:
            Match result or None if no match
        """
        normalized_asset_name = self._normalize_email_name(asset_name)
        
        best_match = None
        best_similarity = 0.0
        
        for service in servicenow_email_services:
            service_name = service.get("name", "")
            normalized_service_name = self._normalize_email_name(service_name)
            
            if normalized_asset_name and normalized_service_name:
                similarity = SequenceMatcher(None, normalized_asset_name, normalized_service_name).ratio()
                
                if similarity > best_similarity and similarity >= self.fuzzy_threshold:
                    best_similarity = similarity
                    best_match = service
        
        if best_match:
            # Determine recommended action based on confidence
            if best_similarity >= self.review_threshold:
                action = "Use Existing"
                notes = f"Matched by similar name with high confidence: {best_similarity:.1%}"
            else:
                action = "Review Match"
                notes = f"Matched by similar name with moderate confidence: {best_similarity:.1%}"
            
            return EmailMatch(
                itglue_id=asset_id,
                itglue_name=asset_name,
                servicenow_id=best_match.get("sys_id"),
                servicenow_name=best_match.get("name"),
                match_type="Fuzzy Name",
                confidence=best_similarity,
                recommended_action=action,
                data_quality="✅ Ready",
                email_type=email_type,
                notes=notes
            )
        
        return None
    
    def _create_no_match_result(self, 
                              asset_id: str, 
                              asset_name: str, 
                              email_type: str) -> EmailMatch:
        """
        Create a no-match result.
        
        Args:
            asset_id: IT Glue asset ID
            asset_name: IT Glue asset name
            email_type: Email type
            
        Returns:
            No-match result
        """
        return EmailMatch(
            itglue_id=asset_id,
            itglue_name=asset_name,
            servicenow_id=None,
            servicenow_name=None,
            match_type="No Match",
            confidence=0.0,
            recommended_action="Create New",
            data_quality="✅ Ready",
            email_type=email_type,
            notes="No matching email service found in ServiceNow"
        )
    
    def _normalize_email_name(self, name: str) -> str:
        """
        Normalize email service name for comparison.
        
        Args:
            name: Email service name
            
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
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _assess_data_quality(self, 
                           asset_id: str, 
                           asset_name: str, 
                           email_type: str,
                           traits: Dict[str, Any],
                           match_result: EmailMatch) -> Tuple[str, Optional[DataQualityIssue]]:
        """
        Assess data quality for an email asset.
        
        Args:
            asset_id: IT Glue asset ID
            asset_name: IT Glue asset name
            email_type: Email type
            traits: Asset traits
            match_result: Match result
            
        Returns:
            Tuple of (quality label, quality issue or None)
        """
        # Check for invalid email type
        if email_type not in self.valid_email_types:
            return "⚠️ Invalid Email Type", DataQualityIssue(
                asset_id=asset_id,
                asset_name=asset_name,
                issue_type="Invalid Email Type",
                priority="Medium",
                description=f"Email type '{email_type}' is not in the list of valid email types",
                recommendation="Update email type to a valid value"
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
        required_fields = ["type", "domain-s", "webmail-url"]
        missing_fields = []
        
        for field in required_fields:
            if field not in traits:
                missing_fields.append(field)
            elif field == "domain-s" and not traits.get(field, {}).get("values", []):
                missing_fields.append(field)
            elif field != "domain-s" and not traits.get(field):
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
    
    def generate_matching_statistics(self, matches: List[EmailMatch]) -> Dict[str, Any]:
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
        
        # Count by email type
        email_types = {}
        for match in matches:
            email_type = match.email_type or "Unknown"
            if email_type not in email_types:
                email_types[email_type] = {"count": 0, "percentage": 0.0}
            email_types[email_type]["count"] += 1
        
        # Calculate percentages
        for email_type in email_types:
            email_types[email_type]["percentage"] = email_types[email_type]["count"] / total * 100
        
        return {
            "total": total,
            "by_match_type": match_types,
            "by_recommended_action": actions,
            "by_data_quality": quality,
            "by_email_type": email_types
        }