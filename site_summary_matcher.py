"""
Site Summary matcher for the migration demo.
"""

import logging
from difflib import SequenceMatcher
from dataclasses import dataclass
from typing import Dict, List, Any, Tuple, Optional

from config import config


@dataclass
class SiteSummaryMatch:
    """Result of matching an IT Glue Site Summary to a ServiceNow site CI."""
    itglue_id: str
    itglue_name: str
    servicenow_id: Optional[str]
    servicenow_name: Optional[str]
    match_type: str  # 'Exact CoreID', 'Exact Name', 'Fuzzy Name', 'No Match'
    confidence: float  # 0.0 to 1.0
    recommended_action: str  # 'Use Existing', 'Review Match', 'Create New', 'Skip'
    data_quality: str  # '✅ Ready', '⚠️ No CoreID', '❌ Missing Data'
    coreid: Optional[str] = None
    notes: str = ""


@dataclass
class DataQualityIssue:
    """Data quality issue for a site summary."""
    site_id: str
    site_name: str
    organization_name: str
    issue_type: str  # 'Missing CoreID', 'Missing Required Field', 'Similar Name'
    priority: str  # 'High', 'Medium', 'Low'
    description: str
    recommendation: str


class SiteSummaryMatcher:
    """Matches IT Glue Site Summary assets to ServiceNow site CIs."""
    
    def __init__(self):
        """Initialize site summary matcher."""
        self.logger = logging.getLogger(__name__)
        self.matching_settings = config.get_matching_settings()
        
        # Extract matching settings
        self.strategies = self.matching_settings.get("strategies", ["coreid", "exact_name", "fuzzy_name"])
        self.fuzzy_threshold = self.matching_settings.get("fuzzy_matching", {}).get("threshold", 0.8)
        self.review_threshold = self.matching_settings.get("fuzzy_matching", {}).get("review_threshold", 0.95)
        
        self.logger.info(f"Site Summary Matcher initialized with strategies: {', '.join(self.strategies)}")
    
    def match_site_summaries(self, 
                           itglue_sites: List[Dict], 
                           servicenow_sites: List[Dict]) -> Tuple[List[SiteSummaryMatch], List[DataQualityIssue]]:
        """
        Match IT Glue Site Summary assets to ServiceNow site CIs.
        
        Args:
            itglue_sites: List of IT Glue Site Summary data
            servicenow_sites: List of ServiceNow site CI data
            
        Returns:
            Tuple of (matches, data quality issues)
        """
        self.logger.info(f"Matching {len(itglue_sites)} IT Glue Site Summaries to {len(servicenow_sites)} ServiceNow sites")
        
        # Match each site summary
        matches = []
        quality_issues = []
        
        for site in itglue_sites:
            site_id = site.get("id")
            attributes = site.get("attributes", {})
            site_name = attributes.get("name", "Unknown")
            org_name = attributes.get("organization-name", "Unknown")
            
            # Get CoreID for this site
            coreid = self._extract_coreid_from_site(site)
            
            # Match site summary
            match_result = self.match_single_site_summary(
                site_id, site_name, org_name, coreid, servicenow_sites
            )
            
            # Assess data quality
            quality_label, quality_issue = self._assess_data_quality(
                site_id, site_name, org_name, coreid, attributes, match_result
            )
            
            # Update match result with data quality
            match_result.data_quality = quality_label
            
            # Add to results
            matches.append(match_result)
            
            if quality_issue:
                quality_issues.append(quality_issue)
        
        self.logger.info(f"Matched {len(matches)} site summaries with {len(quality_issues)} data quality issues")
        return matches, quality_issues
    
    def match_single_site_summary(self, 
                                site_id: str, 
                                site_name: str,
                                org_name: str,
                                coreid: Optional[str],
                                servicenow_sites: List[Dict]) -> SiteSummaryMatch:
        """
        Match a single IT Glue Site Summary to a ServiceNow site CI.
        
        Args:
            site_id: IT Glue Site Summary ID
            site_name: IT Glue Site Summary name
            org_name: IT Glue organization name
            coreid: CoreID from Site Summary (if available)
            servicenow_sites: List of ServiceNow site CI data
            
        Returns:
            Match result
        """
        # Try each matching strategy in order
        for strategy in self.strategies:
            if strategy == "coreid" and coreid:
                # Try CoreID matching
                match = self._match_by_coreid(site_id, site_name, org_name, coreid, servicenow_sites)
                if match:
                    return match
            
            elif strategy == "exact_name":
                # Try exact name matching
                match = self._match_by_exact_name(site_id, site_name, org_name, servicenow_sites)
                if match:
                    return match
            
            elif strategy == "fuzzy_name":
                # Try fuzzy name matching
                match = self._match_by_fuzzy_name(site_id, site_name, org_name, servicenow_sites)
                if match:
                    return match
        
        # No match found
        return self._create_no_match_result(site_id, site_name, org_name, coreid)
    
    def _match_by_coreid(self, 
                       site_id: str, 
                       site_name: str,
                       org_name: str,
                       coreid: str,
                       servicenow_sites: List[Dict]) -> Optional[SiteSummaryMatch]:
        """
        Match by CoreID.
        
        Args:
            site_id: IT Glue Site Summary ID
            site_name: IT Glue Site Summary name
            org_name: IT Glue organization name
            coreid: CoreID from Site Summary
            servicenow_sites: List of ServiceNow site CI data
            
        Returns:
            Match result or None if no match
        """
        for site in servicenow_sites:
            site_coreid = site.get("site_identifier", "")
            
            if site_coreid and site_coreid == coreid:
                return SiteSummaryMatch(
                    itglue_id=site_id,
                    itglue_name=site_name,
                    servicenow_id=site.get("sys_id"),
                    servicenow_name=site.get("name"),
                    match_type="Exact CoreID",
                    confidence=1.0,
                    recommended_action="Use Existing",
                    data_quality="✅ Ready",
                    coreid=coreid,
                    notes=f"Matched by CoreID: {coreid}"
                )
        
        return None
    
    def _match_by_exact_name(self, 
                           site_id: str, 
                           site_name: str,
                           org_name: str,
                           servicenow_sites: List[Dict]) -> Optional[SiteSummaryMatch]:
        """
        Match by exact name and company.
        
        Args:
            site_id: IT Glue Site Summary ID
            site_name: IT Glue Site Summary name
            org_name: IT Glue organization name
            servicenow_sites: List of ServiceNow site CI data
            
        Returns:
            Match result or None if no match
        """
        for site in servicenow_sites:
            site_name_sn = site.get("name", "")
            company_name_sn = site.get("company", {}).get("display_value", "")
            
            if site_name_sn.lower() == site_name.lower() and company_name_sn.lower() == org_name.lower():
                return SiteSummaryMatch(
                    itglue_id=site_id,
                    itglue_name=site_name,
                    servicenow_id=site.get("sys_id"),
                    servicenow_name=site_name_sn,
                    match_type="Exact Name",
                    confidence=1.0,
                    recommended_action="Use Existing",
                    data_quality="✅ Ready",
                    coreid=site.get("site_identifier"),
                    notes=f"Matched by exact name and company: {site_name} / {org_name}"
                )
        
        return None
    
    def _match_by_fuzzy_name(self, 
                           site_id: str, 
                           site_name: str,
                           org_name: str,
                           servicenow_sites: List[Dict]) -> Optional[SiteSummaryMatch]:
        """
        Match by fuzzy name similarity.
        
        Args:
            site_id: IT Glue Site Summary ID
            site_name: IT Glue Site Summary name
            org_name: IT Glue organization name
            servicenow_sites: List of ServiceNow site CI data
            
        Returns:
            Match result or None if no match
        """
        best_match = None
        best_similarity = 0.0
        
        for site in servicenow_sites:
            site_name_sn = site.get("name", "")
            company_name_sn = site.get("company", {}).get("display_value", "")
            
            # Only consider sites from the same company
            if company_name_sn.lower() != org_name.lower():
                continue
            
            if site_name and site_name_sn:
                similarity = SequenceMatcher(None, site_name.lower(), site_name_sn.lower()).ratio()
                
                if similarity > best_similarity and similarity >= self.fuzzy_threshold:
                    best_similarity = similarity
                    best_match = site
        
        if best_match:
            # Determine recommended action based on confidence
            if best_similarity >= self.review_threshold:
                action = "Use Existing"
                notes = f"Matched by similar name with high confidence: {best_similarity:.1%}"
            else:
                action = "Review Match"
                notes = f"Matched by similar name with moderate confidence: {best_similarity:.1%}"
            
            return SiteSummaryMatch(
                itglue_id=site_id,
                itglue_name=site_name,
                servicenow_id=best_match.get("sys_id"),
                servicenow_name=best_match.get("name"),
                match_type="Fuzzy Name",
                confidence=best_similarity,
                recommended_action=action,
                data_quality="✅ Ready",
                coreid=best_match.get("site_identifier"),
                notes=notes
            )
        
        return None
    
    def _create_no_match_result(self, 
                              site_id: str, 
                              site_name: str,
                              org_name: str,
                              coreid: Optional[str]) -> SiteSummaryMatch:
        """
        Create a no-match result.
        
        Args:
            site_id: IT Glue Site Summary ID
            site_name: IT Glue Site Summary name
            org_name: IT Glue organization name
            coreid: CoreID from Site Summary (if available)
            
        Returns:
            No-match result
        """
        return SiteSummaryMatch(
            itglue_id=site_id,
            itglue_name=site_name,
            servicenow_id=None,
            servicenow_name=None,
            match_type="No Match",
            confidence=0.0,
            recommended_action="Create New",
            data_quality="✅ Ready",
            coreid=coreid,
            notes=f"No matching site found in ServiceNow for {org_name}"
        )
    
    def _extract_coreid_from_site(self, site: Dict) -> Optional[str]:
        """
        Extract CoreID from Site Summary.
        
        Args:
            site: Site Summary data
            
        Returns:
            CoreID or None if not found
        """
        try:
            # Extract CoreID from traits
            traits = site.get("attributes", {}).get("traits", {})
            
            # Look for CoreID in various field names
            for field_name, field_data in traits.items():
                field_name_lower = field_name.lower()
                if "coreid" in field_name_lower or "core_id" in field_name_lower:
                    # Extract value from field data
                    if isinstance(field_data, dict):
                        values = field_data.get("values", [])
                        if values and isinstance(values[0], dict):
                            return values[0].get("value", "").strip()
                    elif isinstance(field_data, str):
                        return field_data.strip()
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Failed to extract CoreID from site summary: {e}")
            return None
    
    def _assess_data_quality(self, 
                           site_id: str, 
                           site_name: str,
                           org_name: str,
                           coreid: Optional[str],
                           site_attrs: Dict[str, Any],
                           match_result: SiteSummaryMatch) -> Tuple[str, Optional[DataQualityIssue]]:
        """
        Assess data quality for a site summary.
        
        Args:
            site_id: IT Glue Site Summary ID
            site_name: IT Glue Site Summary name
            org_name: IT Glue organization name
            coreid: CoreID from Site Summary (if available)
            site_attrs: Site Summary attributes
            match_result: Match result
            
        Returns:
            Tuple of (quality label, quality issue or None)
        """
        # Check for missing CoreID
        if not coreid:
            return "⚠️ No CoreID", DataQualityIssue(
                site_id=site_id,
                site_name=site_name,
                organization_name=org_name,
                issue_type="Missing CoreID",
                priority="Medium",
                description="Site Summary does not have a CoreID",
                recommendation="Add CoreID to Site Summary or manually map"
            )
        
        # Check for fuzzy matches with low confidence
        if match_result.match_type == "Fuzzy Name" and match_result.confidence < self.review_threshold:
            return "⚠️ Similar Name", DataQualityIssue(
                site_id=site_id,
                site_name=site_name,
                organization_name=org_name,
                issue_type="Similar Name",
                priority="High",
                description=f"Site matched by similar name with {match_result.confidence:.1%} confidence",
                recommendation="Review match and confirm or create new"
            )
        
        # Check for missing required fields
        required_fields = ["name", "organization-name"]
        missing_fields = [field for field in required_fields if not site_attrs.get(field, "").strip()]
        
        if missing_fields:
            return "❌ Missing Data", DataQualityIssue(
                site_id=site_id,
                site_name=site_name,
                organization_name=org_name,
                issue_type="Missing Required Field",
                priority="High",
                description=f"Site Summary is missing required fields: {', '.join(missing_fields)}",
                recommendation="Complete site summary data in IT Glue"
            )
        
        return "✅ Ready", None
    
    def generate_matching_statistics(self, matches: List[SiteSummaryMatch]) -> Dict[str, Any]:
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