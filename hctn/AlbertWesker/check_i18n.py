import json

with open('static/translations.json', encoding='utf-8') as f:
    trans = json.load(f)

en_keys = set(trans['en'].keys())
az_keys = set(trans['az'].keys())
ru_keys = set(trans['ru'].keys())

print(f"English keys: {len(en_keys)}")
print(f"Azerbaijani keys: {len(az_keys)}")
print(f"Russian keys: {len(ru_keys)}")

# Check differences
missing_az = en_keys - az_keys
missing_ru = en_keys - ru_keys
extra_az = az_keys - en_keys
extra_ru = ru_keys - en_keys

if missing_az:
    print(f"\n⚠ Missing in Azerbaijani: {sorted(missing_az)}")
if missing_ru:
    print(f"\n⚠ Missing in Russian: {sorted(missing_ru)}")
if extra_az:
    print(f"\n⚠ Extra in Azerbaijani: {sorted(extra_az)}")
if extra_ru:
    print(f"\n⚠ Extra in Russian: {sorted(extra_ru)}")

if not (missing_az or missing_ru or extra_az or extra_ru):
    print("\n✓ All languages have matching keys!")
