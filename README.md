# IT Glue to ServiceNow Migration Demo

This project demonstrates the migration of organizations from IT Glue to ServiceNow. It can use real IT Glue organization data or mock data for demonstration purposes.

## Features

- Connects to the IT Glue API to fetch real organization data (optional)
- Simulates ServiceNow with mock data based on real ServiceNow companies
- Demonstrates organization matching using CoreID, exact name, and fuzzy name matching
- Shows detailed migration process with field mappings
- Generates reports on migration results
- Identifies data quality issues and provides recommendations

## Setup

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. If using real IT Glue API:
   - Create a `.env` file with your IT Glue API credentials (see `.env.example`)
4. Run the demo: `python main.py`

## Project Structure

- `main.py`: Entry point for the demo
- `itglue_client.py`: Client for connecting to IT Glue API or using mock data
- `servicenow_mock.py`: Mock ServiceNow client
- `organization_migrator.py`: Core migration logic
- `organization_matcher.py`: Matching logic for organizations
- `field_mapper.py`: Field mapping definitions
- `utils.py`: Utility functions
- `config.py`: Configuration loading
- `mock_servicenow_companies.json`: Mock ServiceNow company data
- `mock_site_summaries.json`: Mock Site Summary flexible asset data

## Running the Demo

### Using Mock Data (Default)

```bash
# Run with mock data (no API calls)
python main.py
```

This will use the included mock data files:
- `organizations.txt`: Contains IT Glue organization data
- `mock_servicenow_companies.json`: Contains mock ServiceNow company data
- `mock_site_summaries.json`: Contains mock Site Summary flexible asset data

### Using Real IT Glue API

```bash
# Run with real IT Glue API
python main.py --use-real-api
```

This will connect to the IT Glue API using the credentials in your `.env` file.

## Mock Data

The mock data included in this demo is based on real IT Glue and ServiceNow data, with the following characteristics:

1. **IT Glue Organizations**:
   - 10 organizations with various statuses and types
   - Some with CoreIDs, some without
   - Various data quality issues to demonstrate the matching process

2. **ServiceNow Companies**:
   - Matching companies for the IT Glue organizations
   - Some with exact name matches, some with fuzzy matches
   - Some with CoreID matches

3. **Site Summaries**:
   - Flexible assets containing CoreIDs for some organizations
   - Missing for others to demonstrate data quality issues

## Migration Process

The demo follows this process:

1. **Data Collection**:
   - Fetches organization data from IT Glue (or mock data)
   - Loads ServiceNow company data (mock)
   - Extracts CoreIDs from Site Summary flexible assets

2. **Organization Matching**:
   - Tries to match by CoreID first (most reliable)
   - Falls back to exact name matching
   - Uses fuzzy name matching as a last resort
   - Recommends creating new companies when no match is found

3. **Data Quality Assessment**:
   - Identifies missing CoreIDs
   - Flags organizations with fuzzy matches
   - Checks for missing required fields

4. **Migration Simulation**:
   - Maps IT Glue fields to ServiceNow fields
   - Creates or updates companies in the mock ServiceNow
   - Generates detailed reports on the migration

5. **Reporting**:
   - Shows detailed console output
   - Saves a comprehensive JSON report
   - Provides statistics on matching and data quality

## Client Demo Instructions

To demonstrate this to a client:

1. Run the demo with mock data first to show the process:
   ```
   python main.py
   ```

2. If you have IT Glue API credentials, you can run with real data:
   ```
   python main.py --use-real-api
   ```

3. Explain the key aspects:
   - The matching process (CoreID, exact name, fuzzy name)
   - Data quality assessment and recommendations
   - Field mapping from IT Glue to ServiceNow
   - The migration process and reporting

4. Show how the demo identifies and handles:
   - Organizations with CoreIDs (direct matches)
   - Organizations without CoreIDs (name matching)
   - Data quality issues and recommendations

This demo provides a realistic preview of how the migration would work in a production environment, using real IT Glue data structure while simulating the ServiceNow side.