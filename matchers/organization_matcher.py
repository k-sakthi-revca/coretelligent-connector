"""
Organization matcher for the migration demo.
"""

import re
import logging
from difflib import SequenceMatcher
from typing import Dict, List, Any, Tuple, Optional

from config import config
from models.match_models import OrganizationMatch, DataQualityIssue


class OrganizationMatcher:
    """Matches IT Glue organizations to ServiceNow companies."""
    
    def __init__(self):
        """Initialize organization matcher."""
        self.logger = logging.getLogger(__name__)
        self.matching_settings = config.get_matching_settings()
        self.valid_statuses = config.get_valid_statuses()
        
        # Extract matching settings
        self.strategies = self.matching_settings.get("strategies", ["coreid", "exact_name", "fuzzy_name"])
        self.fuzzy_threshold = self.matching_settings.get("fuzzy_matching", {}).get("threshold", 0.8)
        self.review_threshold = self.matching_settings.get("fuzzy_matching", {}).get("review_threshold", 0.95)
        self.normalization_patterns = self.matching_settings.get("normalization_patterns", [])
        
        self.logger.info(f"Organization Matcher initialized with strategies: {', '.join(self.strategies)}")
    
    def match_organizations(self, 
                          itglue_orgs: List[Dict], 
                          servicenow_companies: List[Dict],
                          site_summaries: List[Dict]) -> Tuple[List[OrganizationMatch], List[DataQualityIssue]]:
        """
        Match IT Glue organizations to ServiceNow companies.
        
        Args:
            itglue_orgs: List of IT Glue organization data
            servicenow_companies: List of ServiceNow company data
            site_summaries: List of Site Summary flexible asset data
            
        Returns:
            Tuple of (matches, data quality issues)
        """
        self.logger.info(f"Matching {len(itglue_orgs)} IT Glue organizations to {len(servicenow_companies)} ServiceNow companies")
        
        # Extract CoreIDs from Site Summary flexible assets
        coreid_map = self._extract_coreids_from_site_summaries(site_summaries)
        
        # Match each organization
        matches = []
        quality_issues = []
        
        for org in itglue_orgs:
            org_id = org.get("id")
            attributes = org.get("attributes", {})
            org_name = attributes.get("name", "Unknown")
            org_status = attributes.get("organization-status-name")
            
            # Get CoreID for this organization
            coreid = coreid_map.get(org_id)
            
            # Match organization
            match_result = self.match_single_organization(
                org_id, org_name, coreid, org_status, servicenow_companies
            )
            
            # Assess data quality
            quality_label, quality_issue = self._assess_data_quality(
                org_id, org_name, coreid, attributes, match_result
            )
            
            # Update match result with data quality
            match_result.data_quality = quality_label
            
            # Add to results
            matches.append(match_result)
            
            if quality_issue:
                quality_issues.append(quality_issue)
        
        self.logger.info(f"Matched {len(matches)} organizations with {len(quality_issues)} data quality issues")
        return matches, quality_issues
    
    def match_single_organization(self, 
                                org_id: str, 
                                org_name: str, 
                                coreid: Optional[str],
                                status_filter: Optional[str],
                                servicenow_companies: List[Dict]) -> OrganizationMatch:
        """
        Match a single IT Glue organization to a ServiceNow company.
        
        Args:
            org_id: IT Glue organization ID
            org_name: IT Glue organization name
            coreid: CoreID from Site Summary (if available)
            status_filter: Organization status for filtering
            servicenow_companies: List of ServiceNow company data
            
        Returns:
            Match result
        """
        # Skip inactive organizations
        if status_filter and status_filter not in self.valid_statuses:
            return OrganizationMatch(
                itglue_id=org_id,
                itglue_name=org_name,
                servicenow_id=None,
                servicenow_name=None,
                match_type="Skipped",
                confidence=0.0,
                recommended_action="Skip",
                data_quality="⚠️ Inactive",
                coreid=coreid,
                notes=f"Skipped due to status: {status_filter}"
            )
        
        # Try each matching strategy in order
        for strategy in self.strategies:
            if strategy == "coreid" and coreid:
                # Try CoreID matching
                match = self._match_by_coreid(org_id, org_name, coreid, servicenow_companies)
                if match:
                    return match
            
            elif strategy == "exact_name":
                # Try exact name matching
                match = self._match_by_exact_name(org_id, org_name, servicenow_companies)
                if match:
                    return match
            
            elif strategy == "fuzzy_name":
                # Try fuzzy name matching
                match = self._match_by_fuzzy_name(org_id, org_name, servicenow_companies)
                if match:
                    return match
        
        # No match found
        return self._create_no_match_result(org_id, org_name, coreid, status_filter)
    
    def _match_by_coreid(self, 
                       org_id: str, 
                       org_name: str, 
                       coreid: str,
                       servicenow_companies: List[Dict]) -> Optional[OrganizationMatch]:
        """
        Match by CoreID.
        
        Args:
            org_id: IT Glue organization ID
            org_name: IT Glue organization name
            coreid: CoreID from Site Summary
            servicenow_companies: List of ServiceNow company data
            
        Returns:
            Match result or None if no match
        """
        for company in servicenow_companies:
            company_coreid = company.get("u_core_id", "")
            
            if company_coreid and company_coreid == coreid:
                return OrganizationMatch(
                    itglue_id=org_id,
                    itglue_name=org_name,
                    servicenow_id=company.get("sys_id"),
                    servicenow_name=company.get("name"),
                    match_type="Exact CoreID",
                    confidence=1.0,
                    recommended_action="Use Existing",
                    data_quality="✅ Ready",
                    coreid=coreid,
                    notes=f"Matched by CoreID: {coreid}"
                )
        
        return None
    
    def _match_by_exact_name(self, 
                           org_id: str, 
                           org_name: str,
                           servicenow_companies: List[Dict]) -> Optional[OrganizationMatch]:
        """
        Match by exact normalized name.
        
        Args:
            org_id: IT Glue organization ID
            org_name: IT Glue organization name
            servicenow_companies: List of ServiceNow company data
            
        Returns:
            Match result or None if no match
        """
        normalized_org_name = self._normalize_company_name(org_name)
        
        for company in servicenow_companies:
            company_name = company.get("name", "")
            normalized_company_name = self._normalize_company_name(company_name)
            
            if normalized_org_name and normalized_company_name and normalized_org_name == normalized_company_name:
                return OrganizationMatch(
                    itglue_id=org_id,
                    itglue_name=org_name,
                    servicenow_id=company.get("sys_id"),
                    servicenow_name=company_name,
                    match_type="Exact Name",
                    confidence=1.0,
                    recommended_action="Use Existing",
                    data_quality="✅ Ready",
                    coreid=company.get("u_core_id"),
                    notes=f"Matched by exact normalized name: {normalized_org_name}"
                )
        
        return None
    
    def _match_by_fuzzy_name(self, 
                           org_id: str, 
                           org_name: str,
                           servicenow_companies: List[Dict]) -> Optional[OrganizationMatch]:
        """
        Match by fuzzy name similarity.
        
        Args:
            org_id: IT Glue organization ID
            org_name: IT Glue organization name
            servicenow_companies: List of ServiceNow company data
            
        Returns:
            Match result or None if no match
        """
        normalized_org_name = self._normalize_company_name(org_name)
        
        best_match = None
        best_similarity = 0.0
        
        for company in servicenow_companies:
            company_name = company.get("name", "")
            normalized_company_name = self._normalize_company_name(company_name)
            
            if normalized_org_name and normalized_company_name:
                similarity = SequenceMatcher(None, normalized_org_name, normalized_company_name).ratio()
                
                if similarity > best_similarity and similarity >= self.fuzzy_threshold:
                    best_similarity = similarity
                    best_match = company
        
        if best_match:
            # Determine recommended action based on confidence
            if best_similarity >= self.review_threshold:
                action = "Use Existing"
                notes = f"Matched by similar name with high confidence: {best_similarity:.1%}"
            else:
                action = "Review Match"
                notes = f"Matched by similar name with moderate confidence: {best_similarity:.1%}"
            
            return OrganizationMatch(
                itglue_id=org_id,
                itglue_name=org_name,
                servicenow_id=best_match.get("sys_id"),
                servicenow_name=best_match.get("name"),
                match_type="Fuzzy Name",
                confidence=best_similarity,
                recommended_action=action,
                data_quality="✅ Ready",
                coreid=best_match.get("u_core_id"),
                notes=notes
            )
        
        return None
    
    def _create_no_match_result(self, 
                              org_id: str, 
                              org_name: str, 
                              coreid: Optional[str],
                              status_filter: Optional[str]) -> OrganizationMatch:
        """
        Create a no-match result.
        
        Args:
            org_id: IT Glue organization ID
            org_name: IT Glue organization name
            coreid: CoreID from Site Summary (if available)
            status_filter: Organization status for filtering
            
        Returns:
            No-match result
        """
        if status_filter == "Product Only":
            action = "Conditional"
            notes = "Product Only organization - may not need to be migrated"
        else:
            action = "Create New"
            notes = "No matching company found in ServiceNow"
        
        return OrganizationMatch(
            itglue_id=org_id,
            itglue_name=org_name,
            servicenow_id=None,
            servicenow_name=None,
            match_type="No Match",
            confidence=0.0,
            recommended_action=action,
            data_quality="✅ Ready",
            coreid=coreid,
            notes=notes
        )
    
    def _normalize_company_name(self, name: str) -> str:
        """
        Normalize company name for comparison.
        
        Args:
            name: Company name
            
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
    
    def _extract_coreids_from_site_summaries(self, site_summaries: List[Dict]) -> Dict[str, str]:
        """
        Extract CoreIDs from Site Summary flexible assets.
        
        Args:
            site_summaries: List of Site Summary flexible asset records
            
        Returns:
            Dictionary mapping organization_id to CoreID
        """
        self.logger.info(f"Extracting CoreIDs from {len(site_summaries)} Site Summary assets...")
        
        coreid_map = {}
        
        for site in site_summaries:
            try:
                # Get organization ID
                org_id = site.get("attributes", {}).get("organization-id")
                if not org_id:
                    continue
                
                # Extract CoreID from traits
                traits = site.get("attributes", {}).get("traits", {})
                coreid = None
                
                # Look for CoreID in various field names
                for field_name, field_data in traits.items():
                    field_name_lower = field_name.lower()
                    if "coreid" in field_name_lower or "core_id" in field_name_lower:
                        # Extract value from field data
                        if isinstance(field_data, dict):
                            values = field_data.get("values", [])
                            if values and isinstance(values[0], dict):
                                coreid = values[0].get("value", "").strip()
                        elif isinstance(field_data, str):
                            coreid = field_data.strip()
                        break
                
                if coreid and org_id:
                    coreid_map[str(org_id)] = coreid
                    
            except Exception as e:
                self.logger.warning(f"Failed to extract CoreID from site summary: {e}")
        
        self.logger.info(f"Extracted {len(coreid_map)} CoreIDs from Site Summary assets")
        return coreid_map
    
    def _assess_data_quality(self, 
                           org_id: str, 
                           org_name: str, 
                           coreid: Optional[str],
                           org_attrs: Dict[str, Any],
                           match_result: OrganizationMatch) -> Tuple[str, Optional[DataQualityIssue]]:
        """
        Assess data quality for an organization.
        
        Args:
            org_id: IT Glue organization ID
            org_name: IT Glue organization name
            coreid: CoreID from Site Summary (if available)
            org_attrs: Organization attributes
            match_result: Match result
            
        Returns:
            Tuple of (quality label, quality issue or None)
        """
        # Check for missing CoreID
        if not coreid:
            return "⚠️ No CoreID", DataQualityIssue(
                asset_id=org_id,
                asset_name=org_name,
                issue_type="Missing CoreID",
                priority="Medium",
                description="Organization does not have a CoreID in Site Summary",
                recommendation="Create Site Summary with CoreID or manually map"
            )
        
        # Check for fuzzy matches with low confidence
        if match_result.match_type == "Fuzzy Name" and match_result.confidence < self.review_threshold:
            return "⚠️ Similar Name", DataQualityIssue(
                asset_id=org_id,
                asset_name=org_name,
                issue_type="Similar Name",
                priority="High",
                description=f"Organization matched by similar name with {match_result.confidence:.1%} confidence",
                recommendation="Review match and confirm or create new"
            )
        
        # Check for missing required fields
        required_fields = ["name", "organization-status-name"]
        missing_fields = [field for field in required_fields if not org_attrs.get(field, "").strip()]
        
        if missing_fields:
            return "❌ Missing Data", DataQualityIssue(
                asset_id=org_id,
                asset_name=org_name,
                issue_type="Missing Required Field",
                priority="High",
                description=f"Organization is missing required fields: {', '.join(missing_fields)}",
                recommendation="Complete organization data in IT Glue"
            )
        
        return "✅ Ready", None
    
    def generate_matching_statistics(self, matches: List[OrganizationMatch]) -> Dict[str, Any]:
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