# ITGlue Data Extraction Tool

This project provides Python scripts to extract data from ITGlue's API. The extraction process involves connecting to ITGlue's API, retrieving various types of data, and saving it in structured formats for further analysis or integration with other systems.

## Project Structure

- `itglue_connector.py`: Core connector for ITGlue API with authentication and base API functionality
- `itglue_data_extractor.py`: Module for extracting and processing data from ITGlue
- `example.py`: Example script demonstrating how to use the data extractor
- `itglue_api_example.py`: Simple example demonstrating direct usage of the ITGlue connector
- `run_extraction.py`: Script to run a sample extraction and display the results
- `extract_cli.py`: Command-line interface for flexible data extraction
- `itglue_to_servicenow.py`: Script for future integration with ServiceNow (not required for current usage)

## Requirements

- Python 3.7+
- Required Python packages:
  - requests
  - pandas

You can install the required packages using pip:

```bash
pip install -r requirements.txt
```

## Configuration

Before running the extraction, you need to configure the following:

1. ITGlue API Key: You need a valid API key from ITGlue to access their API

## Usage

### Basic Usage with Data Extractor

The data extractor provides a higher-level interface that handles pagination, data processing, and saving to files.

```python
from itglue_data_extractor import ITGlueDataExtractor

# Initialize the data extractor with your ITGlue API key
extractor = ITGlueDataExtractor(
    api_key="your-itglue-api-key"
)

# Extract organizations
organizations = extractor.extract_organizations()
print(f"Extracted {len(organizations)} organizations")

# Extract servers
servers = extractor.extract_configurations(
    config_type_id=703409, 
    config_type_name="servers"
)
print(f"Extracted {len(servers)} servers")

# Extract all data
all_data = extractor.extract_all_data()
```

### Direct API Usage

For more control, you can use the ITGlue connector directly:

```python
from itglue_connector import ITGlueConnector

# Initialize the connector with your ITGlue API key
connector = ITGlueConnector(
    api_key="your-itglue-api-key"
)

# Get organizations
organizations = connector.get_organizations()
print(f"Found {len(organizations)} organizations")

# Get configurations of a specific type (servers)
servers = connector.get_configurations(config_type_id=703409)
print(f"Found {len(servers)} servers")
```

### Running the Examples

You can run the provided example scripts:

```bash
python Connectors/example.py
```

or

```bash
python Connectors/itglue_api_example.py
```

### Quick Sample Extraction

To run a sample extraction and see the results immediately:

```bash
python Connectors/run_extraction.py
```

This script will extract several data types and display samples of the extracted data.

### Command-Line Interface

For more flexible extraction options, use the command-line interface:

```bash
# Extract all data
python Connectors/extract_cli.py --all

# Extract specific data types
python Connectors/extract_cli.py --organizations --domains

# Extract specific configuration types
python Connectors/extract_cli.py --configs servers network_devices

# Extract specific flexible asset types
python Connectors/extract_cli.py --assets voice_pbx wireless_networks

# Combine multiple options
python Connectors/extract_cli.py --organizations --configs servers --assets voice_pbx
```

Available options:
- `--api-key`: ITGlue API key (can also be set via ITGLUE_API_KEY environment variable)
- `--output-dir`: Directory to save extracted data
- `--all`: Extract all data types
- `--organizations`: Extract organizations
- `--domains`: Extract domains
- `--asset-types`: Extract flexible asset types
- `--configs`: Extract configurations of specified types
- `--assets`: Extract flexible assets of specified types

## Data Flow

1. **Connection**: The ITGlue connector establishes a connection to the ITGlue API using your API key
2. **Extraction**: Data is extracted from various ITGlue API endpoints
3. **Processing**: The data extractor processes the raw API responses into more usable formats
4. **Storage**: Processed data is saved as JSON and CSV files in the `extracted_data` directory

## Supported Data Types

The extraction tool currently supports the following data types from ITGlue:

- Organizations (Companies)
- Flexible Asset Types
- Flexible Assets (various types)
- Configurations (Servers, Workstations, Laptops, etc.)
- Domains
- Attachments

### Configuration Types

The tool supports extracting the following configuration types:
- Servers
- Workstations
- Laptops
- Desktops
- Network Devices (Routers, Switches, Firewalls)
- Printers
- Mobile Devices
- Storage Devices
- Application Servers
- Unified Communications Equipment
- SSL Certificates
- UPS

### Flexible Asset Types

The tool supports extracting the following flexible asset types:
- Voice/PBX
- Wireless Networks
- Line of Business Applications
- Email Systems
- Identity Services
- Backup Solutions
- Security Systems
- Licensing & Renewals

## Extending the Tool

To extend the tool for additional data types:

1. Add new methods to `ITGlueConnector` for any additional API endpoints
2. Add extraction methods to `ITGlueDataExtractor` for the new data types

## Logging

The extraction process logs information to both the console and log files. You can adjust the logging level and format in the scripts if needed.

## Notes

- The API key in the scripts is a placeholder and should be replaced with your actual ITGlue API key
- The tool handles pagination automatically, retrieving all pages of results for each API call
- Extracted data is saved in both raw JSON format (preserving all original API response data) and processed CSV format (with key fields extracted for easier analysis)
- For large ITGlue instances, the extraction process may take some time due to API rate limits and the volume of data

## Future Integration with ServiceNow

While the current focus is on data extraction from ITGlue, the repository includes a placeholder script (`itglue_to_servicenow.py`) for future integration with ServiceNow. This script is not required for the current data extraction functionality.