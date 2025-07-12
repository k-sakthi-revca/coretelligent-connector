# Voice PBX Migration

This module provides functionality to migrate Voice/PBX assets from ITGlue to ServiceNow.

## Overview

The Voice PBX migration process consists of two main steps:
1. **Matching**: Matching ITGlue Voice/PBX assets to existing ServiceNow voice gateway CIs
2. **Migration**: Creating or updating ServiceNow voice gateway CIs based on the matching results

## Files

- `voice_pbx_matcher.py`: Contains the `VoicePBXMatcher` class for matching ITGlue Voice/PBX assets to ServiceNow voice gateway CIs
- `voice_pbx_migrator.py`: Contains the `VoicePBXMigrator` class for migrating ITGlue Voice/PBX assets to ServiceNow voice gateway CIs
- `demo_voice_pbx_matcher.py`: Standalone demo script for testing the Voice PBX migration
- `mock_servicenow_voice_gateways.json`: Mock ServiceNow voice gateway CI data for testing
- `data/Voice-PBX/voice-pbx.json`: Sample ITGlue Voice/PBX data for testing

## Usage

### Using the Main Script

```bash
# Run the voice PBX matcher
python main.py voice-pbx

# Run the voice PBX matcher with migration
python main.py voice-pbx --migrate

# Run the voice PBX matcher with migration in dry-run mode
python main.py voice-pbx --migrate --dry-run

# Specify custom file paths
python main.py voice-pbx --itglue-assets path/to/itglue_assets.json --servicenow-gateways path/to/servicenow_gateways.json
```

### Using the Demo Script

```bash
# Run the voice PBX matcher demo
python demo_voice_pbx_matcher.py

# Run the voice PBX matcher demo with migration
python demo_voice_pbx_matcher.py --migrate

# Run the voice PBX matcher demo with migration in dry-run mode
python demo_voice_pbx_matcher.py --migrate --dry-run

# Specify custom file paths
python demo_voice_pbx_matcher.py --itglue-assets path/to/itglue_assets.json --servicenow-gateways path/to/servicenow_gateways.json
```

## Matching Process

The Voice PBX matcher uses the following strategies to match ITGlue Voice/PBX assets to ServiceNow voice gateway CIs:

1. **Serial Number Matching**: Matches based on the serial number field in both systems
2. **Exact Name Matching**: Matches based on exact name and company name
3. **Fuzzy Name Matching**: Matches based on similar names within the same company

## Migration Process

The Voice PBX migrator performs the following actions:

1. For each ITGlue Voice/PBX asset:
   - If a matching ServiceNow voice gateway CI is found, update it with the ITGlue data
   - If no matching ServiceNow voice gateway CI is found, create a new one

## Field Mappings

The following fields are mapped from ITGlue Voice/PBX to ServiceNow voice gateway CI:

| ITGlue Field | ServiceNow Field |
|--------------|------------------|
| title | name |
| system-type | u_system_type |
| version | version |
| serial-number | serial_number |
| ip-address | ip_address |
| mac-address | mac_address |
| phone-numbers | u_phone_numbers |
| service-provider | u_service_provider |
| support-contact | u_support_contact |
| admin-portal | u_admin_portal |
| notes | comments |

## Reports

The migration process generates the following reports:

- `voice_pbx_matches.json`: Contains the matching results
- `voice_pbx_quality_issues.json`: Contains data quality issues found during matching
- `voice_pbx_match_stats.json`: Contains statistics about the matching process
- `voice_pbx_migration_results.json`: Contains the migration results
- `voice_pbx_migration_report.json`: Contains statistics about the migration process