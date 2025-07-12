# Site Summary Migration

This module provides functionality to migrate Site Summary assets from ITGlue to ServiceNow.

## Overview

The Site Summary migration process consists of two main steps:
1. **Matching**: Matching ITGlue Site Summary assets to existing ServiceNow site CIs
2. **Migration**: Creating or updating ServiceNow site CIs based on the matching results

## Files

- `site_summary_matcher.py`: Contains the `SiteSummaryMatcher` class for matching ITGlue Site Summary assets to ServiceNow site CIs
- `site_summary_migrator.py`: Contains the `SiteSummaryMigrator` class for migrating ITGlue Site Summary assets to ServiceNow site CIs
- `demo_site_summary_matcher.py`: Standalone demo script for testing the Site Summary migration
- `mock_servicenow_sites.json`: Mock ServiceNow site CI data for testing
- `data/Site-Summary/site-summary.json`: Sample ITGlue Site Summary data for testing

## Usage

### Using the Main Script

```bash
# Run the site summary matcher
python main.py site-summary

# Run the site summary matcher with migration
python main.py site-summary --migrate

# Run the site summary matcher with migration in dry-run mode
python main.py site-summary --migrate --dry-run

# Specify custom file paths
python main.py site-summary --itglue-sites path/to/itglue_sites.json --servicenow-sites path/to/servicenow_sites.json
```

### Using the Demo Script

```bash
# Run the site summary matcher demo
python demo_site_summary_matcher.py

# Run the site summary matcher demo with migration
python demo_site_summary_matcher.py --migrate

# Run the site summary matcher demo with migration in dry-run mode
python demo_site_summary_matcher.py --migrate --dry-run

# Specify custom file paths
python demo_site_summary_matcher.py --itglue-sites path/to/itglue_sites.json --servicenow-sites path/to/servicenow_sites.json
```

## Matching Process

The Site Summary matcher uses the following strategies to match ITGlue Site Summary assets to ServiceNow site CIs:

1. **CoreID Matching**: Matches based on the CoreID field in both systems
2. **Exact Name Matching**: Matches based on exact name and company name
3. **Fuzzy Name Matching**: Matches based on similar names within the same company

## Migration Process

The Site Summary migrator performs the following actions:

1. For each ITGlue Site Summary asset:
   - If a matching ServiceNow site CI is found, update it with the ITGlue data
   - If no matching ServiceNow site CI is found, create a new one

## Field Mappings

The following fields are mapped from ITGlue Site Summary to ServiceNow site CI:

| ITGlue Field | ServiceNow Field |
|--------------|------------------|
| title | name |
| coreid | site_identifier |
| website | u_website |
| primary-contact-phone | u_primary_contact_phone |
| known-issues | comments |

## Reports

The migration process generates the following reports:

- `site_summary_matches.json`: Contains the matching results
- `site_summary_quality_issues.json`: Contains data quality issues found during matching
- `site_summary_match_stats.json`: Contains statistics about the matching process
- `site_summary_migration_results.json`: Contains the migration results
- `site_summary_migration_report.json`: Contains statistics about the migration process