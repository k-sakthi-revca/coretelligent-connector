"""
Virtualization matcher for the migration demo.
"""

import re
import logging
from difflib import SequenceMatcher
from typing import Dict, List, Any, Tuple, Optional

from config import config
from models.match_models import VirtualizationMatch, DataQualityIssue


class VirtualizationMatcher:
    """Matches IT Glue virtualization assets to ServiceNow servers."""
    
    def __init__(self):
        """Initialize virtualization matcher."""
        self.logger = logging.getLogger(__name__)
        self.matching_settings = config.get("virtualization_matching", {})
        
        # Extract matching settings
        self.strategies = self.matching_settings.get("strategies", ["exact_name", "fuzzy_name"])
        self.fuzzy_threshold = self.matching_settings.get("fuzzy_matching", {}).get("threshold", 0.8)
        self.review_threshold = self.matching_settings.get("fuzzy_matching", {}).get("review_threshold", 0.95)
        self.normalization_patterns = self.matching_settings.get("normalization_patterns", [])
        
        # Valid hypervisors
        self.valid_hypervisors = self.matching_settings.get("valid_hypervisors", ["VMware", "Hyper-V", "Xen", "Nutanix", "Other"])
        
        self.logger.info(f"Virtualization Matcher initialized with strategies: {', '.join(self.strategies)}")
    
    def match_virtualization_assets(self, 
                                  itglue_assets: List[Dict], 
                                  servicenow_servers: List[Dict]) -> Tuple[List[VirtualizationMatch], List[DataQualityIssue]]:
        """
        Match IT Glue virtualization assets to ServiceNow servers.
        
        Args:
            itglue_assets: List of IT Glue virtualization asset data
            servicenow_servers: List of ServiceNow server data
            
        Returns:
            Tuple of (matches, data quality issues)
        """
        self.logger.info(f"Matching {len(itglue_assets)} IT Glue virtualization assets to {len(servicenow_servers)} ServiceNow servers")
        
        # Match each asset
        matches = []
        quality_issues = []
        
        for asset in itglue_assets:
            asset_id = asset.get("id")
            attributes = asset.get("attributes", {})
            asset_name = attributes.get("name", "Unknown")
            
            # Get traits
            traits = attributes.get("traits", {})
            hypervisor = traits.get("hypervisor", "Unknown")
            
            # Match asset
            match_result = self.match_single_asset(
                asset_id, asset_name, hypervisor, servicenow_servers
            )
            
            # Assess data quality
            quality_label, quality_issue = self._assess_data_quality(
                asset_id, asset_name, hypervisor, traits, match_result
            )
            
            # Update match result with data quality
            match_result.data_quality = quality_label
            
            # Add to results
            matches.append(match_result)
            
            if quality_issue:
                quality_issues.append(quality_issue)
        
        self.logger.info(f"Matched {len(matches)} virtualization assets with {len(quality_issues)} data quality issues")
        return matches, quality_issues
    
    def match_single_asset(self, 
                         asset_id: str, 
                         asset_name: str, 
                         hypervisor: str,
                         servicenow_servers: List[Dict]) -> VirtualizationMatch:
        """
        Match a single IT Glue virtualization asset to a ServiceNow server.
        
        Args:
            asset_id: IT Glue asset ID
            asset_name: IT Glue asset name
            hypervisor: Hypervisor type
            servicenow_servers: List of ServiceNow server data
            
        Returns:
            Match result
        """
        # Try each matching strategy in order
        for strategy in self.strategies:
            if strategy == "exact_name":
                # Try exact name matching
                match = self._match_by_exact_name(asset_id, asset_name, hypervisor, servicenow_servers)
                if match:
                    return match
            
            elif strategy == "fuzzy_name":
                # Try fuzzy name matching
                match = self._match_by_fuzzy_name(asset_id, asset_name, hypervisor, servicenow_servers)
                if match:
                    return match
        
        # No match found
        return self._create_no_match_result(asset_id, asset_name, hypervisor)
    
    def _match_by_exact_name(self, 
                           asset_id: str, 
                           asset_name: str,
                           hypervisor: str,
                           servicenow_servers: List[Dict]) -> Optional[VirtualizationMatch]:
        """
        Match by exact normalized name.
        
        Args:
            asset_id: IT Glue asset ID
            asset_name: IT Glue asset name
            hypervisor: Hypervisor type
            servicenow_servers: List of ServiceNow server data
            
        Returns:
            Match result or None if no match
        """
        normalized_asset_name = self._normalize_server_name(asset_name)
        
        for server in servicenow_servers:
            server_name = server.get("name", "")
            normalized_server_name = self._normalize_server_name(server_name)
            
            if normalized_asset_name and normalized_server_name and normalized_asset_name == normalized_server_name:
                return VirtualizationMatch(
                    itglue_id=asset_id,
                    itglue_name=asset_name,
                    servicenow_id=server.get("sys_id"),
                    servicenow_name=server_name,
                    match_type="Exact Name",
                    confidence=1.0,
                    recommended_action="Use Existing",
                    data_quality="✅ Ready",
                    hypervisor=hypervisor,
                    notes=f"Matched by exact normalized name: {normalized_asset_name}"
                )
        
        return None
    
    def _match_by_fuzzy_name(self, 
                           asset_id: str, 
                           asset_name: str,
                           hypervisor: str,
                           servicenow_servers: List[Dict]) -> Optional[VirtualizationMatch]:
        """
        Match by fuzzy name similarity.
        
        Args:
            asset_id: IT Glue asset ID
            asset_name: IT Glue asset name
            hypervisor: Hypervisor type
            servicenow_servers: List of ServiceNow server data
            
        Returns:
            Match result or None if no match
        """
        normalized_asset_name = self._normalize_server_name(asset_name)
        
        best_match = None
        best_similarity = 0.0
        
        for server in servicenow_servers:
            server_name = server.get("name", "")
            normalized_server_name = self._normalize_server_name(server_name)
            
            if normalized_asset_name and normalized_server_name:
                similarity = SequenceMatcher(None, normalized_asset_name, normalized_server_name).ratio()
                
                if similarity > best_similarity and similarity >= self.fuzzy_threshold:
                    best_similarity = similarity
                    best_match = server
        
        if best_match:
            # Determine recommended action based on confidence
            if best_similarity >= self.review_threshold:
                action = "Use Existing"
                notes = f"Matched by similar name with high confidence: {best_similarity:.1%}"
            else:
                action = "Review Match"
                notes = f"Matched by similar name with moderate confidence: {best_similarity:.1%}"
            
            return VirtualizationMatch(
                itglue_id=asset_id,
                itglue_name=asset_name,
                servicenow_id=best_match.get("sys_id"),
                servicenow_name=best_match.get("name"),
                match_type="Fuzzy Name",
                confidence=best_similarity,
                recommended_action=action,
                data_quality="✅ Ready",
                hypervisor=hypervisor,
                notes=notes
            )
        
        return None
    
    def _create_no_match_result(self, 
                              asset_id: str, 
                              asset_name: str, 
                              hypervisor: str) -> VirtualizationMatch:
        """
        Create a no-match result.
        
        Args:
            asset_id: IT Glue asset ID
            asset_name: IT Glue asset name
            hypervisor: Hypervisor type
            
        Returns:
            No-match result
        """
        return VirtualizationMatch(
            itglue_id=asset_id,
            itglue_name=asset_name,
            servicenow_id=None,
            servicenow_name=None,
            match_type="No Match",
            confidence=0.0,
            recommended_action="Create New",
            data_quality="✅ Ready",
            hypervisor=hypervisor,
            notes="No matching server found in ServiceNow"
        )
    
    def _normalize_server_name(self, name: str) -> str:
        """
        Normalize server name for comparison.
        
        Args:
            name: Server name
            
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
                           hypervisor: str,
                           traits: Dict[str, Any],
                           match_result: VirtualizationMatch) -> Tuple[str, Optional[DataQualityIssue]]:
        """
        Assess data quality for a virtualization asset.
        
        Args:
            asset_id: IT Glue asset ID
            asset_name: IT Glue asset name
            hypervisor: Hypervisor type
            traits: Asset traits
            match_result: Match result
            
        Returns:
            Tuple of (quality label, quality issue or None)
        """
        # Check for invalid hypervisor
        if hypervisor not in self.valid_hypervisors:
            return "⚠️ Invalid Hypervisor", DataQualityIssue(
                asset_id=asset_id,
                asset_name=asset_name,
                issue_type="Invalid Hypervisor",
                priority="Medium",
                description=f"Hypervisor '{hypervisor}' is not in the list of valid hypervisors",
                recommendation="Update hypervisor to a valid value"
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
        required_fields = ["friendly-name", "hypervisor"]
        missing_fields = [field for field in required_fields if field not in traits or not traits.get(field)]
        
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
    
    def generate_matching_statistics(self, matches: List[VirtualizationMatch]) -> Dict[str, Any]:
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
        
        # Count by hypervisor
        hypervisors = {}
        for match in matches:
            hypervisor = match.hypervisor or "Unknown"
            if hypervisor not in hypervisors:
                hypervisors[hypervisor] = {"count": 0, "percentage": 0.0}
            hypervisors[hypervisor]["count"] += 1
        
        # Calculate percentages
        for hypervisor in hypervisors:
            hypervisors[hypervisor]["percentage"] = hypervisors[hypervisor]["count"] / total * 100
        
        return {
            "total": total,
            "by_match_type": match_types,
            "by_recommended_action": actions,
            "by_data_quality": quality,
            "by_hypervisor": hypervisors
        }