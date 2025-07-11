"""
Data models for matching results.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class OrganizationMatch:
    """Result of matching an IT Glue organization to a ServiceNow company."""
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
class VirtualizationMatch:
    """Result of matching an IT Glue virtualization asset to a ServiceNow server."""
    itglue_id: str
    itglue_name: str
    servicenow_id: Optional[str]
    servicenow_name: Optional[str]
    match_type: str  # 'Exact Name', 'Fuzzy Name', 'No Match'
    confidence: float  # 0.0 to 1.0
    recommended_action: str  # 'Use Existing', 'Review Match', 'Create New', 'Skip'
    data_quality: str  # '✅ Ready', '⚠️ Missing Data', '❌ Invalid Data'
    hypervisor: Optional[str] = None
    notes: str = ""


@dataclass
class DataQualityIssue:
    """Data quality issue for an asset."""
    asset_id: str
    asset_name: str
    issue_type: str  # 'Missing Required Field', 'Similar Name', 'Invalid Hypervisor', etc.
    priority: str  # 'High', 'Medium', 'Low'
    description: str
    recommendation: str