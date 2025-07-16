"""
ITGlue to ServiceNow Deduplication Tool

This package implements the deduplication strategy for the ITGlue to ServiceNow migration
as specified in the requirements document. It identifies potential duplicate records
between ITGlue and ServiceNow using a weighted scoring algorithm and processes them
based on confidence levels.

Author: Coretelligent Migration Team
Date: July 2023
"""

from .deduplicator import Deduplicator
from .process_manual_reviews import ManualReviewProcessor
from .utils import (
    normalize_data,
    calculate_similarity,
    calculate_match_score,
    setup_logging,
    load_config,
    save_results
)
from .config import get_default_config

__all__ = [
    'Deduplicator',
    'ManualReviewProcessor',
    'normalize_data',
    'calculate_similarity',
    'calculate_match_score',
    'setup_logging',
    'load_config',
    'save_results',
    'get_default_config'
]

__version__ = '1.0.0'
