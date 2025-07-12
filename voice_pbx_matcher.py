"""
Voice PBX matcher for the migration demo.
"""

import logging
from difflib import SequenceMatcher
from dataclasses import dataclass
from typing import Dict, List, Any, Tuple, Optional

from config import config


@dataclass
class VoicePBXMatch:
    """Result of matching an IT Glue Voice/PBX asset to a ServiceNow voice gateway CI."""
    itglue_id: str
    itglue_name: str
    servicenow_id: Optional[str]
    servicenow_name: Optional[str]
    match_type: str  # 'Exact Serial', 'Exact Name', 'Fuzzy Name', 'No Match'
    confidence: float  # 0.0 to 1.0
    recommended_action: str  # 'Use Existing', 'Review Match', 'Create New', 'Skip'
    data_quality: str  # '✅ Ready', '⚠️ No Serial', '❌ Missing Data'
    serial_number: Optional[str] = None
    notes: str = ""


@dataclass
class DataQualityIssue:
    """Data quality issue for a voice PBX asset."""
    asset_id: str
    asset_name: str
    organization_name: str
    issue_type: str  # 'Missing Serial', 'Missing Required Field', 'Similar Name'
    priority: str  # 'High', 'Medium', 'Low'
    description: str
    recommendation: str


class VoicePBXMatcher:
    """Matches IT Glue Voice/PBX assets to ServiceNow voice gateway CIs."""
    
    def __init__(self):
        """Initialize voice PBX matcher."""
        self.logger = logging.getLogger(__name__)
        self.matching_settings = config.get_matching_settings()
        
        # Extract matching settings
        self.strategies = self.matching_settings.get("strategies", ["serial", "exact_name", "fuzzy_name"])
        self.fuzzy_threshold = self.matching_settings.get("fuzzy_matching", {}).get("threshold", 0.8)
        self.review_threshold = self.matching_settings.get("fuzzy_matching", {}).get("review_threshold", 0.95)
        
        self.logger.info(f"Voice PBX Matcher initialized with strategies: {', '.join(self.strategies)}")
    
    def match_voice_pbx_assets(self, 
                             itglue_assets: List[Dict], 
                             servicenow_gateways: List[Dict]) -> Tuple[List[VoicePBXMatch], List[DataQualityIssue]]:
        """
        Match IT Glue Voice/PBX assets to ServiceNow voice gateway CIs.
        
        Args:
            itglue_assets: List of IT Glue Voice/PBX data
            servicenow_gateways: List of ServiceNow voice gateway CI data
            
        Returns:
            Tuple of (matches, data quality issues)
        """
        self.logger.info(f"Matching {len(itglue_assets)} IT Glue Voice/PBX assets to {len(servicenow_gateways)} ServiceNow voice gateways")
        
        # Match each voice PBX asset
        matches = []
        quality_issues = []
        
        for asset in itglue_assets:
            asset_id = asset.get("id")
            attributes = asset.get("attributes", {})
            asset_name = attributes.get("name", "Unknown")
            org_name = attributes.get("organization-name", "Unknown")
            
            # Get serial number for this asset
            serial_number = self._extract_serial_number_from_asset(asset)
            
            # Match voice PBX asset
            match_result = self.match_single_voice_pbx_asset(
                asset_id, asset_name, org_name, serial_number, servicenow_gateways
            )
            
            # Assess data quality
            quality_label, quality_issue = self._assess_data_quality(
                asset_id, asset_name, org_name, serial_number, attributes, match_result
            )
            
            # Update match result with data quality
            match_result.data_quality = quality_label
            
            # Add to results
            matches.append(match_result)
            
            if quality_issue:
                quality_issues.append(quality_issue)
        
        self.logger.info(f"Matched {len(matches)} voice PBX assets with {len(quality_issues)} data quality issues")
        return matches, quality_issues
    
    def match_single_voice_pbx_asset(self, 
                                   asset_id: str, 
                                   asset_name: str,
                                   org_name: str,
                                   serial_number: Optional[str],
                                   servicenow_gateways: List[Dict]) -> VoicePBXMatch:
        """
        Match a single IT Glue Voice/PBX asset to a ServiceNow voice gateway CI.
        
        Args:
            asset_id: IT Glue Voice/PBX asset ID
            asset_name: IT Glue Voice/PBX asset name
            org_name: IT Glue organization name
            serial_number: Serial number from Voice/PBX asset (if available)
            servicenow_gateways: List of ServiceNow voice gateway CI data
            
        Returns:
            Match result
        """
        # Try each matching strategy in order
        for strategy in self.strategies:
            if strategy == "serial" and serial_number:
                # Try serial number matching
                match = self._match_by_serial_number(asset_id, asset_name, org_name, serial_number, servicenow_gateways)
                if match:
                    return match
            
            elif strategy == "exact_name":
                # Try exact name matching
                match = self._match_by_exact_name(asset_id, asset_name, org_name, servicenow_gateways)
                if match:
                    return match
            
            elif strategy == "fuzzy_name":
                # Try fuzzy name matching
                match = self._match_by_fuzzy_name(asset_id, asset_name, org_name, servicenow_gateways)
                if match:
                    return match
        
        # No match found
        return self._create_no_match_result(asset_id, asset_name, org_name, serial_number)
    
    def _match_by_serial_number(self, 
                              asset_id: str, 
                              asset_name: str,
                              org_name: str,
                              serial_number: str,
                              servicenow_gateways: List[Dict]) -> Optional[VoicePBXMatch]:
        """
        Match by serial number.
        
        Args:
            asset_id: IT Glue Voice/PBX asset ID
            asset_name: IT Glue Voice/PBX asset name
            org_name: IT Glue organization name
            serial_number: Serial number from Voice/PBX asset
            servicenow_gateways: List of ServiceNow voice gateway CI data
            
        Returns:
            Match result or None if no match
        """
        for gateway in servicenow_gateways:
            gateway_serial = gateway.get("serial_number", "")
            
            if gateway_serial and gateway_serial == serial_number:
                return VoicePBXMatch(
                    itglue_id=asset_id,
                    itglue_name=asset_name,
                    servicenow_id=gateway.get("sys_id"),
                    servicenow_name=gateway.get("name"),
                    match_type="Exact Serial",
                    confidence=1.0,
                    recommended_action="Use Existing",
                    data_quality="✅ Ready",
                    serial_number=serial_number,
                    notes=f"Matched by serial number: {serial_number}"
                )
        
        return None
    
    def _match_by_exact_name(self, 
                           asset_id: str, 
                           asset_name: str,
                           org_name: str,
                           servicenow_gateways: List[Dict]) -> Optional[VoicePBXMatch]:
        """
        Match by exact name and company.
        
        Args:
            asset_id: IT Glue Voice/PBX asset ID
            asset_name: IT Glue Voice/PBX asset name
            org_name: IT Glue organization name
            servicenow_gateways: List of ServiceNow voice gateway CI data
            
        Returns:
            Match result or None if no match
        """
        for gateway in servicenow_gateways:
            gateway_name = gateway.get("name", "")
            company_name = gateway.get("company", {}).get("display_value", "")
            
            if gateway_name.lower() == asset_name.lower() and company_name.lower() == org_name.lower():
                return VoicePBXMatch(
                    itglue_id=asset_id,
                    itglue_name=asset_name,
                    servicenow_id=gateway.get("sys_id"),
                    servicenow_name=gateway_name,
                    match_type="Exact Name",
                    confidence=1.0,
                    recommended_action="Use Existing",
                    data_quality="✅ Ready",
                    serial_number=gateway.get("serial_number"),
                    notes=f"Matched by exact name and company: {asset_name} / {org_name}"
                )
        
        return None
    
    def _match_by_fuzzy_name(self, 
                           asset_id: str, 
                           asset_name: str,
                           org_name: str,
                           servicenow_gateways: List[Dict]) -> Optional[VoicePBXMatch]:
        """
        Match by fuzzy name similarity.
        
        Args:
            asset_id: IT Glue Voice/PBX asset ID
            asset_name: IT Glue Voice/PBX asset name
            org_name: IT Glue organization name
            servicenow_gateways: List of ServiceNow voice gateway CI data
            
        Returns:
            Match result or None if no match
        """
        best_match = None
        best_similarity = 0.0
        
        for gateway in servicenow_gateways:
            gateway_name = gateway.get("name", "")
            company_name = gateway.get("company", {}).get("display_value", "")
            
            # Only consider gateways from the same company
            if company_name.lower() != org_name.lower():
                continue
            
            if asset_name and gateway_name:
                similarity = SequenceMatcher(None, asset_name.lower(), gateway_name.lower()).ratio()
                
                if similarity > best_similarity and similarity >= self.fuzzy_threshold:
                    best_similarity = similarity
                    best_match = gateway
        
        if best_match:
            # Determine recommended action based on confidence
            if best_similarity >= self.review_threshold:
                action = "Use Existing"
                notes = f"Matched by similar name with high confidence: {best_similarity:.1%}"
            else:
                action = "Review Match"
                notes = f"Matched by similar name with moderate confidence: {best_similarity:.1%}"
            
            return VoicePBXMatch(
                itglue_id=asset_id,
                itglue_name=asset_name,
                servicenow_id=best_match.get("sys_id"),
                servicenow_name=best_match.get("name"),
                match_type="Fuzzy Name",
                confidence=best_similarity,
                recommended_action=action,
                data_quality="✅ Ready",
                serial_number=best_match.get("serial_number"),
                notes=notes
            )
        
        return None
    
    def _create_no_match_result(self, 
                              asset_id: str, 
                              asset_name: str,
                              org_name: str,
                              serial_number: Optional[str]) -> VoicePBXMatch:
        """
        Create a no-match result.
        
        Args:
            asset_id: IT Glue Voice/PBX asset ID
            asset_name: IT Glue Voice/PBX asset name
            org_name: IT Glue organization name
            serial_number: Serial number from Voice/PBX asset (if available)
            
        Returns:
            No-match result
        """
        return VoicePBXMatch(
            itglue_id=asset_id,
            itglue_name=asset_name,
            servicenow_id=None,
            servicenow_name=None,
            match_type="No Match",
            confidence=0.0,
            recommended_action="Create New",
            data_quality="✅ Ready",
            serial_number=serial_number,
            notes=f"No matching voice gateway found in ServiceNow for {org_name}"
        )
    
    def _extract_serial_number_from_asset(self, asset: Dict) -> Optional[str]:
        """
        Extract serial number from Voice/PBX asset.
        
        Args:
            asset: Voice/PBX asset data
            
        Returns:
            Serial number or None if not found
        """
        try:
            # Extract serial number from traits
            traits = asset.get("attributes", {}).get("traits", {})
            
            # Look for serial number field
            if "serial-number" in traits:
                serial_number = traits.get("serial-number")
                if isinstance(serial_number, str):
                    return serial_number.strip()
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to extract serial number from Voice/PBX asset: {e}")
            return None
    
    def _assess_data_quality(self, 
                           asset_id: str, 
                           asset_name: str,
                           org_name: str,
                           serial_number: Optional[str],
                           asset_attrs: Dict[str, Any],
                           match_result: VoicePBXMatch) -> Tuple[str, Optional[DataQualityIssue]]:
        """
        Assess data quality for a Voice/PBX asset.
        
        Args:
            asset_id: IT Glue Voice/PBX asset ID
            asset_name: IT Glue Voice/PBX asset name
            org_name: IT Glue organization name
            serial_number: Serial number from Voice/PBX asset (if available)
            asset_attrs: Voice/PBX asset attributes
            match_result: Match result
            
        Returns:
            Tuple of (quality label, quality issue or None)
        """
        # Check for missing serial number
        if not serial_number:
            return "⚠️ No Serial", DataQualityIssue(
                asset_id=asset_id,
                asset_name=asset_name,
                organization_name=org_name,
                issue_type="Missing Serial",
                priority="Medium",
                description="Voice/PBX asset does not have a serial number",
                recommendation="Add serial number to Voice/PBX asset or manually map"
            )
        
        # Check for fuzzy matches with low confidence
        if match_result.match_type == "Fuzzy Name" and match_result.confidence < self.review_threshold:
            return "⚠️ Similar Name", DataQualityIssue(
                asset_id=asset_id,
                asset_name=asset_name,
                organization_name=org_name,
                issue_type="Similar Name",
                priority="High",
                description=f"Asset matched by similar name with {match_result.confidence:.1%} confidence",
                recommendation="Review match and confirm or create new"
            )
        
        # Check for missing required fields
        required_fields = ["name", "organization-name"]
        missing_fields = [field for field in required_fields if not asset_attrs.get(field, "").strip()]
        
        if missing_fields:
            return "❌ Missing Data", DataQualityIssue(
                asset_id=asset_id,
                asset_name=asset_name,
                organization_name=org_name,
                issue_type="Missing Required Field",
                priority="High",
                description=f"Voice/PBX asset is missing required fields: {', '.join(missing_fields)}",
                recommendation="Complete asset data in IT Glue"
            )
        
        return "✅ Ready", None
    
    def generate_matching_statistics(self, matches: List[VoicePBXMatch]) -> Dict[str, Any]:
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
        
        return {
            "total": total,
            "by_match_type": match_types,
            "by_recommended_action": actions,
            "by_data_quality": quality
        }