import json
with open('data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("report_date:", data.get("report_date"))
print("grand_total_gtc:", data.get("grand_total_gtc"))
print("grand_total_gtc_tts:", data.get("grand_total_gtc_tts"))
print("ns_total:", data.get("ns_total"))
print("opr_total:", data.get("opr_total"))
print("gtc_tinh:")
for t in data.get("gtc_tinh", []):
    print("  -", t['tinh'], "total_gtc:", t['total_gtc'])
