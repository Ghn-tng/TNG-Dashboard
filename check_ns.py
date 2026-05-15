import json
with open('history.json') as f:
    h = json.load(f)
print('--- HISTORY NS THIEU ---')
for d in sorted(h.keys())[-7:]:
    print(f"{d}: {h[d].get('ns_thieu')}")

with open('data.json') as f:
    d = json.load(f)
print('\n--- LIVE DATA ---')
print(f"Report Date: {d.get('report_date')}")
print(f"NS Thieu: {d.get('ns_total', {}).get('so_thieu')}")
