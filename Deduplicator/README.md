# ITGlue to ServiceNow Deduplication Tool

This tool implements the deduplication strategy for the ITGlue to ServiceNow migration as specified in the requirements document. It identifies potential duplicate records between ITGlue and ServiceNow using a weighted scoring algorithm and processes them based on confidence levels.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Deduplication Process](#deduplication-process)
- [Output Files](#output-files)
- [Manual Review Process](#manual-review-process)
- [Troubleshooting](#troubleshooting)

## Overview

The deduplication tool is designed to:

1. Load data from ITGlue and ServiceNow for a specific organization
2. Apply data filters based on requirements
3. Normalize data fields for consistent comparison
4. Find potential matches between ITGlue and ServiceNow records
5. Calculate match scores using a weighted algorithm
6. Process records based on confidence levels:
   - High confidence (0.8-1.0): Automatic update
   - Medium confidence (0.6-0.8): Manual review
   - Low confidence (0.0-0.6): Create new record
7. Generate reports and export manual review items
8. Apply updates to ServiceNow (optional)

## Installation

### Prerequisites

- Python 3 (compatible with older versions as well)
- Python 3 compatibility mode can be enabled with the `-3` flag: `python -3 deduplicator.py`
- Type annotations have been removed for compatibility with older Python versions
- Required Python packages (all specified in requirements.txt):
  - pandas (data processing)
  - numpy (numerical operations)
  - pyyaml (configuration handling)
  - requests (API interaction)
  - python-Levenshtein (string similarity)
  - python-dateutil (date handling)
  - typing-extensions (enhanced typing support)
  - and more (see requirements.txt for the complete list)

### Setup

1. Clone the repository or download the source code
2. Install required packages:

```bash
pip install -r requirements.txt
```

## Configuration

The deduplication tool can be configured using a YAML or JSON configuration file. If no configuration file is provided, default settings will be used.

### Default Configuration

The default configuration is defined in `config.py` and includes settings for:

- Logging
- Confidence thresholds
- Match weights
- API configuration
- Data filtering
- Output settings
- Error handling

### Custom Configuration

You can create a custom configuration file in YAML or JSON format:

```yaml
# Example config.yaml
logging:
  level: DEBUG
  log_to_file: true
  log_file: deduplication.log

confidence_thresholds:
  high: 0.85
  medium: 0.65

match_weights:
  serial_number: 0.5
  mac_address: 0.3
  hostname: 0.1
  name: 0.1

# Additional settings...
```

## Usage

### Basic Usage

#### Using the Run Scripts (Recommended)

For Windows:
```
# Run directly in Command Prompt (not through Python)
run_deduplication.bat

# OR double-click the batch file in Windows Explorer
```

For Linux/macOS:
```bash
# Make the script executable (first time only)
chmod +x run_deduplication.sh  

# Run the script
./run_deduplication.sh
```

These scripts will:
1. Generate sample data using the example.py script
2. Run the deduplication process with the generated sample data
3. Save the results to the sample_data/output directory

#### Manual Execution

```bash
# First, run the example script to generate sample data
python -3 example.py

# Then run the deduplication process with the generated sample data
python -3 deduplicator.py --organization "Acme Corporation" \
                      --itglue-data sample_data/itglue_sample.json \
                      --servicenow-data sample_data/servicenow_sample.json
```

This will run the deduplication process for the specified organization using default settings with Python 3 compatibility mode enabled.

> **IMPORTANT**: You must provide data files using the `--itglue-data` and `--servicenow-data` parameters. The API-based data loading is not implemented yet.

### Advanced Usage

```bash
python -3 deduplicator.py --organization "Acme Corporation" \
                      --config config.yaml \
                      --itglue-data acme_itglue_data.json \
                      --servicenow-data acme_servicenow_data.json \
                      --output ./output \
                      --apply \
                      --verbose
```

### Command Line Arguments

- `--organization`: Name of the organization to process (required)
- `--config`: Path to configuration file (optional)
- `--itglue-data`: Path to ITGlue data file (optional)
- `--servicenow-data`: Path to ServiceNow data file (optional)
- `--output`: Directory to save output files (optional)
- `--apply`: Apply updates to ServiceNow (optional)
- `--verbose`: Enable verbose logging (optional)

## Deduplication Process

### Step 1: Data Preparation

The tool first loads and prepares data from both ITGlue and ServiceNow:

- Filters out archived records
- Skips records with invalid organization status
- Skips "Product Only" assets containing "Not Managed By Coretelligent"
- Normalizes data fields (trims whitespace, standardizes formats)

### Step 2: Match Identification

For each ITGlue record, the tool:

1. Searches for potential matches in ServiceNow within the same company context
2. Checks primary identifiers first (serial number, MAC address, asset tag)
3. Then checks secondary identifiers (hostname, IP address, name)

### Step 3: Match Scoring

The tool calculates a match score for each potential match using this weighted formula:

```
Match Score = (
    0.4 × serial_number_similarity +
    0.3 × mac_address_similarity +
    0.2 × hostname_similarity +
    0.1 × name_similarity
)
```

Similarity is calculated using Python's difflib SequenceMatcher, which returns a value between 0.0 (no similarity) and 1.0 (exact match).

### Step 4: Processing Based on Confidence

Records are processed based on their match score:

- **High Confidence (0.8-1.0)**: Automatically update the ServiceNow record with ITGlue data
- **Medium Confidence (0.6-0.8)**: Queue for manual review
- **Low Confidence (0.0-0.6)**: Create a new record in ServiceNow

### Step 5: Reporting and Updates

The tool generates:

- A comprehensive report of the deduplication process
- A CSV file of medium confidence matches for manual review
- Optionally applies updates to ServiceNow

## Output Files

### Deduplication Report

A JSON file containing:

- Timestamp
- Statistics (total records, match counts, etc.)
- Counts for each confidence level
- Medium confidence matches
- Errors

Example filename: `deduplication_report_20230715_123045.json`

### Manual Review Items

A CSV file containing medium confidence matches for manual review:

- Match score
- ITGlue record details (ID, name, serial, MAC, hostname)
- ServiceNow record details (sys_id, name, serial, MAC, hostname)
- Decision column (to be filled by reviewer)

Example filename: `manual_review_items_20230715_123045.csv`

## Manual Review Process

For medium confidence matches:

1. Open the manual review CSV file
2. Review each match pair
3. Decide whether to:
   - Update the ServiceNow record with ITGlue data
   - Keep the ServiceNow record as is
   - Create a new record
4. Fill in the decision column with one of:
   - "update" - Update the ServiceNow record
   - "keep" - Keep the ServiceNow record as is
   - "create" - Create a new record
5. Save the CSV file
6. Process the decisions using:

```bash
python -3 process_manual_reviews.py --file manual_review_items_20230715_123045.csv
```

## Troubleshooting

### Common Issues

#### API Connection Errors

- Check API credentials
- Verify network connectivity
- Check rate limiting settings

#### Data Format Issues

- Ensure data files are valid JSON
- Check for required fields
- Verify organization ID matches

#### Performance Issues

- Consider processing organizations in smaller batches
- Adjust batch size in configuration
- Run with verbose logging to identify bottlenecks

### Logging

Enable verbose logging for detailed information:

```bash
python -3 deduplicator.py --organization "Acme Corporation" --verbose
```

Or configure logging to a file:

```yaml
# In config.yaml
logging:
  level: DEBUG
  log_to_file: true
  log_file: deduplication.log
```

### Getting Help

For additional assistance, contact the Coretelligent Migration Team.
