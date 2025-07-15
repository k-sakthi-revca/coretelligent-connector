import json
from fuzzywuzzy import fuzz

# Load data
with open('data/temp_itglue_data.json') as f:
    itglue_data = json.load(f)['data']

with open('data/temp_servicenow_data.json') as f:
    servicenow_data = json.load(f)['result']

def normalize(text):
    return text.strip().lower() if isinstance(text, str) else ''

# Compare assets
for it_asset in itglue_data:
    it_attrs = it_asset['attributes']
    it_traits = it_attrs.get('traits', {})

    it_name = normalize(it_attrs.get('name'))
    it_ad_full = normalize(it_traits.get('ad-full-name'))
    it_ad_short = normalize(it_traits.get('ad-short-name'))

    best_match = None
    best_score = 0

    for sn_asset in servicenow_data:
        sn_name = normalize(sn_asset.get('name'))
        sn_ad_full = normalize(sn_asset.get('u_ad_full_name'))
        sn_ad_short = normalize(sn_asset.get('u_ad_short_name'))

        score = 0
        if it_ad_full and it_ad_full == sn_ad_full:
            score += 5
        if it_ad_short and it_ad_short == sn_ad_short:
            score += 3
        if it_name and sn_name:
            similarity = fuzz.token_sort_ratio(it_name, sn_name)
            if similarity > 85:
                score += 2

        if score > best_score:
            best_score = score
            best_match = sn_asset

    print("="*60)
    print(f"ITGlue: {it_name} | AD Full: {it_ad_full} | AD Short: {it_ad_short}")
    if best_score >= 7:
        print(f"✅ Match Found → SN: {best_match.get('name')} (Score: {best_score})")
    elif best_score >= 4:
        print(f"⚠ Possible Match → SN: {best_match.get('name')} (Score: {best_score})")
    else:
        print(f"❌ No match found")
