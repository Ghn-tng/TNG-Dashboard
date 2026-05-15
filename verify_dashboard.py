import json
import os

def verify():
    data_path = 'data.json'
    if not os.path.exists(data_path):
        print("❌ Error: data.json not found!")
        return False
    
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    issues = []
    
    # 1. Check AM count
    ams = [x['am'] for x in data.get('gtc_am', []) if x['am'] != 'Grand Total']
    if len(ams) != 15:
        issues.append(f"⚠️ AM count mismatch: Found {len(ams)}, expected 15.")
    
    # 2. Check Province count
    provinces = [x['tinh'] for x in data.get('gtc_tinh', [])]
    if len(provinces) != 4:
        issues.append(f"⚠️ Province count mismatch: Found {len(provinces)}, expected 4.")
    
    # 3. Check for 0 values in Grand Total
    gt = data.get('grand_total_gtc', {})
    if gt.get('vol', 0) == 0:
        issues.append("⚠️ Grand Total Volume is 0.")
    
    # 4. Check for missing keys
    required_keys = ['gtc_am', 'gtc_tinh', 'gtc_bc', 'ns_am', 'bc_kd_lay']
    for k in required_keys:
        if k not in data or not data[k]:
            issues.append(f"⚠️ Missing or empty data key: {k}")

    if not issues:
        print("✅ Data verification passed! All AMs and provinces accounted for.")
        return True
    else:
        print("❌ Data verification FAILED:")
        for issue in issues:
            print(f"  - {issue}")
        return False

if __name__ == "__main__":
    verify()
