import requests
import json
from requests.auth import HTTPBasicAuth

# ServiceNow credentials
USERNAME = 'openana_api'
PASSWORD = '11eVogR29J4'

# Your instance URL (without trailing slash)
INSTANCE_URL = 'https://coretelligentdev.service-now.com'

# Table names to fetch
TABLE_NAMES = [
    "u_cmdb_ci_service_auth",
    "cmdb_ci_voice_gateway",
    "u_cmdb_ci_ssid",
    "cmdb_ci_appl",
    "cmdb_ci_email_server",
    "cmdb_ci_storage_server",
    "cmdb_ci_circuit",
    "cmdb_ci_ip_network",
    "u_cmdb_ci_user_remote_access",
    "u_cmdb_ci_vendor",
    "ast_contract",
    "u_cmdb_ci_security_services",
    "cmdb_ci_backup_server",
    "cmdb_ci_printer",
    "cmdb_ci_server",
    "cmdb_ci_vpn"
]

# Headers
HEADERS = {
    'Accept': 'application/json'
}

# Output file
OUTPUT_FILE = 'servicenow_all_tables_combined.json'

def fetch_table_data(table_name):
    url = f'{INSTANCE_URL}/api/now/table/{table_name}?sysparm_limit=10000'
    print(f"[+] Fetching data from table: {table_name} ...")
    
    response = requests.get(url, headers=HEADERS, auth=HTTPBasicAuth(USERNAME, PASSWORD))
    response.raise_for_status()
    
    return response.json()['result']

def main():
    combined_data = {}

    for table in TABLE_NAMES:
        try:
            records = fetch_table_data(table)
            combined_data[table] = records
            print(f"[✓] Added {len(records)} records from {table}")
        except requests.HTTPError as e:
            print(f"[!] Failed to fetch from {table}: {e}")
        except Exception as ex:
            print(f"[!] Unexpected error with {table}: {ex}")

    # Save all combined data
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(combined_data, f, indent=2)

    print(f"\n[✓] All data saved to {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
