# ITGlue to ServiceNow Migration Demo

This project demonstrates the migration of data from ITGlue to ServiceNow, with a focus on matching organizations, virtualization assets, email services, and LoB applications.

## Project Structure

```
itglue_to_servicenow_demo/
├── config.py                  # Configuration loader
├── config.yaml                # Configuration settings
├── main.py                    # Main CLI script
├── demo_organization_matcher.py  # Demo script for organization matching
├── demo_virtualization_matcher.py  # Demo script for virtualization matching
├── run_email_migration.py     # Script to run email migration
├── run_lob_applications_migration.py  # Script to run LoB applications migration
├── data/                      # Data directory
│   ├── virtualization/        # Virtualization data
│   │   └── virtualization_data.json  # Sample virtualization data
│   ├── emails/                # Email data
│   │   └── emails.json        # Sample email data
│   └── lob/                   # LoB applications data
│       └── lob_applications.json  # Sample LoB applications data
├── logs/                      # Log files
├── matchers/                  # Matcher classes
│   ├── __init__.py
│   ├── organization_matcher.py  # Organization matcher
│   ├── virtualization_matcher.py  # Virtualization matcher
│   ├── email_matcher.py       # Email matcher
│   └── lob_applications_matcher.py  # LoB applications matcher
├── migrators/                 # Migrator classes
│   ├── email_migrator.py      # Email migrator
│   └── lob_applications_migrator.py  # LoB applications migrator
├── models/                    # Data models
│   ├── __init__.py
│   └── match_models.py        # Match result models
├── reports/                   # Report generation
│   ├── __init__.py
│   ├── report_generator.py    # Report generator
│   ├── email_migration_report.json  # Email migration report
│   └── lob_applications_migration_report.json  # LoB applications migration report
├── utils/                     # Utility functions
│   ├── __init__.py
│   ├── file_utils.py          # File operations
│   └── logging_utils.py       # Logging setup
├── mock_servicenow_companies.json  # Mock ServiceNow company data
├── mock_servicenow_servers.json    # Mock ServiceNow server data
├── mock_servicenow_email_services.json  # Mock ServiceNow email services data
├── mock_servicenow_applications.json  # Mock ServiceNow applications data
└── mock_site_summaries.json        # Mock Site Summary data
```

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Configure settings in `config.yaml`

## Usage

### Command Line Interface

The main script provides a command-line interface for running the matchers:

```bash
# Run organization matcher
python main.py organizations [options]

# Run virtualization matcher
python main.py virtualization [options]
```

#### Organization Matcher Options

```
--itglue-orgs FILE           Path to IT Glue organizations JSON file
--servicenow-companies FILE  Path to ServiceNow companies JSON file
--site-summaries FILE        Path to Site Summary JSON file
--output-dir DIR             Output directory for reports (default: reports)
--report-file FILE           Report file name
--log-file FILE              Log file path
--log-level LEVEL            Logging level (default: INFO)
--quiet                      Suppress console output
```

#### Virtualization Matcher Options

```
--itglue-assets FILE         Path to IT Glue virtualization assets JSON file
--servicenow-servers FILE    Path to ServiceNow servers JSON file
--output-dir DIR             Output directory for reports (default: reports)
--report-file FILE           Report file name
--log-file FILE              Log file path
--log-level LEVEL            Logging level (default: INFO)
--quiet                      Suppress console output
```

### Email Migration

The email migration process migrates email assets from IT Glue to ServiceNow. It matches IT Glue email assets to ServiceNow email services, maps fields, and creates or updates records in ServiceNow.

To run the email migration:

```bash
python run_email_migration.py
```

The script will:
1. Fetch email assets from IT Glue
2. Fetch email services from ServiceNow
3. Match IT Glue email assets to ServiceNow email services
4. Map IT Glue fields to ServiceNow fields
5. Create or update ServiceNow email services
6. Generate a migration report

The migration report is saved to `reports/email_migration_report.json` and includes:
- Migration statistics
- Match details for each email asset
- Data quality issues
- Field mappings

### LoB Applications Migration

The LoB applications migration process migrates Line of Business application assets from IT Glue to ServiceNow. It matches IT Glue LoB application assets to ServiceNow application CIs, maps fields, and creates or updates records in ServiceNow.

To run the LoB applications migration:

```bash
python run_lob_applications_migration.py
```

The script will:
1. Fetch LoB application assets from IT Glue
2. Fetch application CIs from ServiceNow
3. Match IT Glue LoB application assets to ServiceNow application CIs
4. Map IT Glue fields to ServiceNow fields
5. Create or update ServiceNow application CIs
6. Generate a migration report

The migration report is saved to `reports/lob_applications_migration_report.json` and includes:
- Migration statistics
- Match details for each LoB application asset
- Data quality issues
- Field mappings

### Demo Scripts

For quick testing, you can use the demo scripts:

```bash
# Run organization matcher demo
python demo_organization_matcher.py

# Run virtualization matcher demo
python demo_virtualization_matcher.py
```

## Configuration

The `config.yaml` file contains settings for the migration process:

- IT Glue API settings
- ServiceNow settings
- Field mappings
- Matching strategies and thresholds
- Normalization patterns
- Valid organization statuses
- Output settings

## Reports

Reports are generated in JSON format and saved to the `reports` directory. They include:

- Match statistics
- Match details for each asset
- Data quality issues
- Recommendations for each match

## Extending the Project

To add support for additional asset types:

1. Create a new matcher class in the `matchers` directory
2. Create a new migrator class in the `migrators` directory (if needed)
3. Add appropriate data models to `models/match_models.py`
4. Update the field mapper to support the new asset type
5. Create a run script for the new migration
6. Update the README.md file to document the new migration