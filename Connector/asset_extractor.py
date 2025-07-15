import requests
import json
import time

# Your API token here
API_TOKEN = 'ITG.ae2832744821bd14ae2f43ece15219b2.Jsa1h3WB3jf1YTjC4TSYj0QtnroW1s7aoWFm-aTTc1UnVbnslsQRzvcBpfOT4bmB'

# Base URL
BASE_URL = 'https://api.itglue.com'
HEADERS = {
   'X-API-KEY': API_TOKEN,
    'Accept': 'application/vnd.itglue+json',
    'Content-Type': 'application/json'
}

# Output file
OUTPUT_FILE = 'itglue_assets_output.json'


def fetch_asset_types():
    url = f'{BASE_URL}/flexible_asset_types'
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()['data']


def fetch_assets_by_type(asset_type_id):
    url = f'{BASE_URL}/flexible_assets?filter[flexible-asset-type-id]={asset_type_id}'
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()['data']


def main():
    all_assets = {}

    print("[+] Fetching asset types...")
    asset_types = fetch_asset_types()

    for asset_type in asset_types:
        asset_type_id = asset_type['id']
        asset_type_name = asset_type['attributes']['name']
        print(f"[+] Fetching assets for type: {asset_type_name} (ID: {asset_type_id})")
        
        try:
            assets = fetch_assets_by_type(asset_type_id)
            all_assets[asset_type_name] = assets
            time.sleep(1)  # to avoid hitting rate limits
        except requests.HTTPError as e:
            print(f"[!] Failed to fetch assets for type ID {asset_type_id}: {e}")
            continue

    print(f"[+] Saving output to {OUTPUT_FILE}")
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(all_assets, f, indent=2)

    print("[✓] Done!")


if __name__ == '__main__':
    main()
