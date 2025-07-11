# ITGlue to ServiceNow Migration Demo

This project demonstrates the migration of data from ITGlue to ServiceNow, with a focus on matching organizations and virtualization assets.

## Project Structure

```
itglue_to_servicenow_demo/
├── config.py                  # Configuration loader
├── config.yaml                # Configuration settings
├── main.py                    # Main CLI script
├── demo_organization_matcher.py  # Demo script for organization matching
├── demo_virtualization_matcher.py  # Demo script for virtualization matching
├── data/                      # Data directory
│   └── virtualization/        # Virtualization data
│       └── virtualization_data.json  # Sample virtualization data
├── logs/                      # Log files
├── matchers/                  # Matcher classes
│   ├── __init__.py
│   ├── organization_matcher.py  # Organization matcher
│   └── virtualization_matcher.py  # Virtualization matcher
├── models/                    # Data models
│   ├── __init__.py
│   └── match_models.py        # Match result models
├── reports/                   # Report generation
│   ├── __init__.py
│   └── report_generator.py    # Report generator
├── utils/                     # Utility functions
│   ├── __init__.py
│   ├── file_utils.py          # File operations
│   └── logging_utils.py       # Logging setup
├── mock_servicenow_companies.json  # Mock ServiceNow company data
├── mock_servicenow_servers.json    # Mock ServiceNow server data
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
2. Add appropriate data models to `models/match_models.py`
3. Update the report generator to support the new asset type
4. Add a new command to `main.py`