"""
Printing matcher for the migration demo.
"""

import re
import logging
from difflib import SequenceMatcher
from dataclasses import dataclass
from typing import Dict, List, Any, Tuple, Optional

from config import config


@dataclass
class PrintingMatch:
    """Result of matching an IT Glue printing asset to a ServiceNow printer CI."""
    itglue_id: str
    itglue_name: str
    servicenow_id: Optional[str]
    servicenow_name: Optional[str]
    match_type: str  # 'Exact Name', 'Fuzzy Name', 'No Match'
    confidence: float  # 0.0 to 1.0
    recommended_action: str  # 'Use Existing', 'Review Match', 'Create New', 'Skip'
    data_quality: str  # '✅ Ready', '⚠️ Missing Data', '❌ Invalid Data'
    printer_type: Optional[str] = None
    notes: str = ""


@dataclass
class DataQualityIssue:
    """Data quality issue for a printing asset."""
    asset_id: str
    asset_name: str
    issue_type: str  # 'Missing Required Field', 'Similar Name', 'Invalid Printer Type'
    priority: str  # 'High', 'Medium', 'Low'
    description: str
    recommendation: str


class PrintingMatcher:
    """Matches IT Glue printing assets to ServiceNow printer CIs."""
    
    def __init__(self):
        """Initialize printing matcher."""
        self.logger = logging.getLogger(__name__)
        self.matching_settings = config.get("printing_matching", {})
        
        # Extract matching settings or use defaults if not specified
        self.strategies = self.matching_settings.get("strategies", ["exact_name", "fuzzy_name"])
        self.fuzzy_threshold = self.matching_settings.get("fuzzy_matching", {}).get("threshold", 0.8)
        self.review_threshold = self.matching_settings.get("fuzzy_matching", {}).get("review_threshold", 0.95)
        self.normalization_patterns = self.matching_settings.get("normalization_patterns", [])
        
        # Valid printer types
        self.valid_printer_types = self.matching_settings.get("valid_printer_types", [
            "Laser", "Inkjet", "Thermal", "Dot Matrix", "3D", "Label", "Multifunction", "Other"
        ])
        
        self.logger.info(f"Printing Matcher initialized with strategies: {', '.join(self.strategies)}")
    
    def match_printing_assets(self, 
                         itglue_assets: List[Dict], 
                         servicenow_printers: List[Dict]) -> Tuple[List[PrintingMatch], List[DataQualityIssue]]:
        """
        Match IT Glue printing assets to ServiceNow printer CIs.
        
        Args:
            itglue_assets: List of IT Glue printing asset data
            servicenow_printers: List of ServiceNow printer CI data
            
        Returns:
            Tuple of (matches, data quality issues)
        """
        self.logger.info(f"Matching {len(itglue_assets)} IT Glue printing assets to {len(servicenow_printers)} ServiceNow printer CIs")
        
        # Match each asset
        matches = []
        quality_issues = []
        
        for asset in itglue_assets:
            asset_id = asset.get("id")
            attributes = asset.get("attributes", {})
            asset_name = attributes.get("name", "Unknown")
            
            # Get traits
            traits = attributes.get("traits", {})
            
            # Extract printers from the asset
            printers = self._extract_printers(traits)
            
            if not printers:
                # If no printers found, create a single match for the asset itself
                match_result = self.match_single_asset(
                    asset_id, asset_name, None, servicenow_printers
                )
                
                # Assess data quality
                quality_label, quality_issue = self._assess_data_quality(
                    asset_id, asset_name, None, traits, match_result
                )
                
                # Update match result with data quality
                match_result.data_quality = quality_label
                
                # Add to results
                matches.append(match_result)
                
                if quality_issue:
                    quality_issues.append(quality_issue)
            else:
                # Match each printer in the asset
                for printer in printers:
                    printer_name = printer.get("name", "Unknown Printer")
                    printer_type = self._determine_printer_type(printer_name)
                    
                    match_result = self.match_single_asset(
                        asset_id, printer_name, printer_type, servicenow_printers
                    )
                    
                    # Assess data quality
                    quality_label, quality_issue = self._assess_data_quality(
                        asset_id, printer_name, printer_type, traits, match_result
                    )
                    
                    # Update match result with data quality
                    match_result.data_quality = quality_label
                    
                    # Add to results
                    matches.append(match_result)
                    
                    if quality_issue:
                        quality_issues.append(quality_issue)
        
        self.logger.info(f"Matched {len(matches)} printing assets with {len(quality_issues)} data quality issues")
        return matches, quality_issues
    
    def match_single_asset(self, 
                         asset_id: str, 
                         asset_name: str, 
                         printer_type: Optional[str],
                         servicenow_printers: List[Dict]) -> PrintingMatch:
        """
        Match a single IT Glue printing asset to a ServiceNow printer CI.
        
        Args:
            asset_id: IT Glue asset ID
            asset_name: IT Glue asset name
            printer_type: Printer type
            servicenow_printers: List of ServiceNow printer CI data
            
        Returns:
            Match result
        """
        # Try each matching strategy in order
        for strategy in self.strategies:
            if strategy == "exact_name":
                # Try exact name matching
                match = self._match_by_exact_name(asset_id, asset_name, printer_type, servicenow_printers)
                if match:
                    return match
            
            elif strategy == "fuzzy_name":
                # Try fuzzy name matching
                match = self._match_by_fuzzy_name(asset_id, asset_name, printer_type, servicenow_printers)
                if match:
                    return match
        
        # No match found
        return self._create_no_match_result(asset_id, asset_name, printer_type)
    
    def _match_by_exact_name(self, 
                           asset_id: str, 
                           asset_name: str,
                           printer_type: Optional[str],
                           servicenow_printers: List[Dict]) -> Optional[PrintingMatch]:
        """
        Match by exact normalized name.
        
        Args:
            asset_id: IT Glue asset ID
            asset_name: IT Glue asset name
            printer_type: Printer type
            servicenow_printers: List of ServiceNow printer CI data
            
        Returns:
            Match result or None if no match
        """
        normalized_asset_name = self._normalize_printer_name(asset_name)
        
        for printer in servicenow_printers:
            printer_name = printer.get("name", "")
            normalized_printer_name = self._normalize_printer_name(printer_name)
            
            if normalized_asset_name and normalized_printer_name and normalized_asset_name == normalized_printer_name:
                return PrintingMatch(
                    itglue_id=asset_id,
                    itglue_name=asset_name,
                    servicenow_id=printer.get("sys_id"),
                    servicenow_name=printer_name,
                    match_type="Exact Name",
                    confidence=1.0,
                    recommended_action="Use Existing",
                    data_quality="✅ Ready",
                    printer_type=printer_type,
                    notes=f"Matched by exact normalized name: {normalized_asset_name}"
                )
        
        return None
    
    def _match_by_fuzzy_name(self, 
                           asset_id: str, 
                           asset_name: str,
                           printer_type: Optional[str],
                           servicenow_printers: List[Dict]) -> Optional[PrintingMatch]:
        """
        Match by fuzzy name similarity.
        
        Args:
            asset_id: IT Glue asset ID
            asset_name: IT Glue asset name
            printer_type: Printer type
            servicenow_printers: List of ServiceNow printer CI data
            
        Returns:
            Match result or None if no match
        """
        normalized_asset_name = self._normalize_printer_name(asset_name)
        
        best_match = None
        best_similarity = 0.0
        
        for printer in servicenow_printers:
            printer_name = printer.get("name", "")
            normalized_printer_name = self._normalize_printer_name(printer_name)
            
            if normalized_asset_name and normalized_printer_name:
                similarity = SequenceMatcher(None, normalized_asset_name, normalized_printer_name).ratio()
                
                if similarity > best_similarity and similarity >= self.fuzzy_threshold:
                    best_similarity = similarity
                    best_match = printer
        
        if best_match:
            # Determine recommended action based on confidence
            if best_similarity >= self.review_threshold:
                action = "Use Existing"
                notes = f"Matched by similar name with high confidence: {best_similarity:.1%}"
            else:
                action = "Review Match"
                notes = f"Matched by similar name with moderate confidence: {best_similarity:.1%}"
            
            return PrintingMatch(
                itglue_id=asset_id,
                itglue_name=asset_name,
                servicenow_id=best_match.get("sys_id"),
                servicenow_name=best_match.get("name"),
                match_type="Fuzzy Name",
                confidence=best_similarity,
                recommended_action=action,
                data_quality="✅ Ready",
                printer_type=printer_type,
                notes=notes
            )
        
        return None
    
    def _create_no_match_result(self, 
                              asset_id: str, 
                              asset_name: str, 
                              printer_type: Optional[str]) -> PrintingMatch:
        """
        Create a no-match result.
        
        Args:
            asset_id: IT Glue asset ID
            asset_name: IT Glue asset name
            printer_type: Printer type
            
        Returns:
            No-match result
        """
        return PrintingMatch(
            itglue_id=asset_id,
            itglue_name=asset_name,
            servicenow_id=None,
            servicenow_name=None,
            match_type="No Match",
            confidence=0.0,
            recommended_action="Create New",
            data_quality="✅ Ready",
            printer_type=printer_type,
            notes="No matching printer found in ServiceNow"
        )
    
    def _normalize_printer_name(self, name: str) -> str:
        """
        Normalize printer name for comparison.
        
        Args:
            name: Printer name
            
        Returns:
            Normalized name
        """
        if not name:
            return ""
        
        # Convert to lowercase
        normalized = name.lower()
        
        # Remove common prefixes like "PRINTER: "
        normalized = re.sub(r'^printer:\s*', '', normalized)
        
        # Apply normalization patterns
        for pattern in self.normalization_patterns:
            regex = pattern.get("pattern", "")
            replacement = pattern.get("replacement", "")
            
            if regex:
                normalized = re.sub(regex, replacement, normalized)
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _extract_printers(self, traits: Dict[str, Any]) -> List[Dict]:
        """
        Extract printers from asset traits.
        
        Args:
            traits: Asset traits
            
        Returns:
            List of printer data
        """
        printers = []
        
        # Check if printer-s field exists and has values
        printer_field = traits.get("printer-s", {})
        if isinstance(printer_field, dict) and "values" in printer_field:
            printers = printer_field.get("values", [])
        
        return printers
    
    def _determine_printer_type(self, printer_name: str) -> Optional[str]:
        """
        Determine printer type from name.
        
        Args:
            printer_name: Printer name
            
        Returns:
            Printer type or None if unknown
        """
        printer_name_lower = printer_name.lower()
        
        # Check for common printer types in the name
        if "laser" in printer_name_lower:
            return "Laser"
        elif "inkjet" in printer_name_lower:
            return "Inkjet"
        elif "thermal" in printer_name_lower:
            return "Thermal"
        elif "label" in printer_name_lower:
            return "Label"
        elif "3d" in printer_name_lower or "3-d" in printer_name_lower:
            return "3D"
        elif "dot matrix" in printer_name_lower:
            return "Dot Matrix"
        elif "mfp" in printer_name_lower or "multifunction" in printer_name_lower:
            return "Multifunction"
        
        # Check for common manufacturers and their typical printer types
        if any(brand in printer_name_lower for brand in ["hp", "hewlett packard", "laserjet"]):
            return "Laser"
        elif any(brand in printer_name_lower for brand in ["epson", "canon", "brother"]) and "mfc" not in printer_name_lower:
            return "Inkjet"
        elif any(brand in printer_name_lower for brand in ["zebra", "dymo"]):
            return "Label"
        elif any(brand in printer_name_lower for brand in ["xerox", "ricoh", "konica", "minolta", "sharp", "kyocera"]):
            return "Multifunction"
        
        return "Other"
    
    def _assess_data_quality(self, 
                           asset_id: str, 
                           asset_name: str, 
                           printer_type: Optional[str],
                           traits: Dict[str, Any],
                           match_result: PrintingMatch) -> Tuple[str, Optional[DataQualityIssue]]:
        """
        Assess data quality for a printing asset.
        
        Args:
            asset_id: IT Glue asset ID
            asset_name: IT Glue asset name
            printer_type: Printer type
            traits: Asset traits
            match_result: Match result
            
        Returns:
            Tuple of (quality label, quality issue or None)
        """
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
        required_fields = ["location"]
        missing_fields = []
        
        for field in required_fields:
            if field not in traits:
                missing_fields.append(field)
            elif field == "location" and not traits.get(field, {}).get("values", []):
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
    
    def generate_matching_statistics(self, matches: List[PrintingMatch]) -> Dict[str, Any]:
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
        
        # Count by printer type
        printer_types = {}
        for match in matches:
            printer_type = match.printer_type or "Unknown"
            if printer_type not in printer_types:
                printer_types[printer_type] = {"count": 0, "percentage": 0.0}
            printer_types[printer_type]["count"] += 1
        
        # Calculate percentages
        for printer_type in printer_types:
            printer_types[printer_type]["percentage"] = printer_types[printer_type]["count"] / total * 100
        
        return {
            "total": total,
            "by_match_type": match_types,
            "by_recommended_action": actions,
            "by_data_quality": quality,
            "by_printer_type": printer_types
        }