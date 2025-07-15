import json
import csv

# Files
ITGLUE_FILE = '/Users/swapnilmhatre/migration/coretelligent-connector/Connector/itglue_assets_output.json'
SERVICENOW_FILE = '/Users/swapnilmhatre/migration/coretelligent-connector/Connector/servicenow_classes_output.json'
MAPPING_FILE = '/Users/swapnilmhatre/migration/coretelligent-connector/Connector/field_mapping.csv'
OUTPUT_FILE = 'field_comparison_report.json'

def normalize(val):
    return str(val).strip().lower() if val else None

def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def load_mapping(file_path):
    mapping = []
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['ITGlue Field'] and row['SN Field']:
                mapping.append((row['ITGlue Field'], row['SN Field']))
    return mapping

def compare_records(itglue_assets, servicenow_records, mapping):
    comparison_report = []

    for asset in itglue_assets:
        itg_traits = asset['attributes'].get('traits', {})
        itg_id = asset.get('id')
        matched_record = None

        # Try to match SN record using ITGlue id <-> u_itg_id
        for record in servicenow_records:
            if normalize(record.get('u_itg_id')) == normalize(itg_id):
                matched_record = record
                break

        # If match found, compare fields
        if matched_record:
            result = {
                'itglue_asset_name': asset['attributes'].get('name'),
                'itg_id': itg_id,
                'servicenow_sys_id': matched_record.get('sys_id'),
                'field_comparisons': []
            }

            for itg_field, sn_field in mapping:
                itg_value = normalize(itg_traits.get(itg_field)) if itg_field != 'id' else normalize(itg_id)
                sn_value = normalize(matched_record.get(sn_field))

                status = 'Matched' if itg_value == sn_value else (
                    'Missing in SN' if sn_value is None else 'Needs Update'
                )

                result['field_comparisons'].append({
                    'itg_field': itg_field,
                    'sn_field': sn_field,
                    'itg_value': itg_value,
                    'sn_value': sn_value,
                    'status': status
                })

            comparison_report.append(result)

    return comparison_report

def main():
    print("[+] Loading data...")
    itglue_assets = load_json(ITGLUE_FILE)
    servicenow_data = load_json(SERVICENOW_FILE)
    field_mapping = load_mapping(MAPPING_FILE)

    print("[+] Comparing field-level mappings...")
    report = compare_records(itglue_assets, servicenow_data, field_mapping)

    with open(OUTPUT_FILE, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"[✓] Comparison report saved to {OUTPUT_FILE} — {len(report)} assets processed.")

if __name__ == '__main__':
    main()
