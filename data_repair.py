import json
import os
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    filename='data_repair.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def log_fix(msg):
    logging.info(f"FIX: {msg}")
    print(f"[REPAIR] {msg}")

def safe_num(v):
    try: return float(v) if v is not None else 0
    except: return 0

def validate_and_repair(data_path):
    if not os.path.exists(data_path):
        logging.error(f"Data file not found: {data_path}")
        return False

    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        logging.error(f"Failed to load data for repair: {e}")
        return False

    original_data = json.dumps(data) # For comparison
    
    # 1. Basic Structure Validation
    required_keys = ['gtc_am', 'gtc_bc', 'gtc_tts', 'ltc_am', 'ontime_tts']
    for key in required_keys:
        if key not in data:
            data[key] = []
            log_fix(f"Missing key '{key}' initialized as empty list.")

    # 2. Normalize Names (AM and BC)
    def normalize_name(name):
        if not name: return ""
        # Remove extra spaces, standardize case if needed (keeping original for display)
        return " ".join(str(name).strip().split())

    # 3. Repair GTC AM Data
    for x in data.get('gtc_am', []):
        x['am'] = normalize_name(x.get('am', ''))
        # Ensure percentages are valid
        for k in ['ca1_gan', 'ca1_gtc', 'ca2_gan', 'ca2_gtc', 'ton_gan', 'ton_gtc', 'total_gan', 'total_gtc']:
            v = safe_num(x.get(k, 0))
            if v < 0: 
                x[k] = 0
                log_fix(f"Negative percentage {k} for {x['am']} reset to 0.")
            elif v > 1.0: 
                # GTC, GAN, LTC, OPR, ODR should never exceed 1.0 (100%)
                if any(p in k for p in ['gtc', 'gan', 'ltc', 'opr', 'ontime', 'today']):
                    x[k] = 1.0
                    log_fix(f"Excessive percentage {k} ({v}) for {x['am']} capped at 1.0.")
        
        # Re-calculate totals if inconsistent
        total_vol = safe_num(x.get('ca1_vol',0)) + safe_num(x.get('ca2_vol',0)) + safe_num(x.get('ton_vol',0))
        if abs(total_vol - safe_num(x.get('total_vol',0))) > 1:
            log_fix(f"Corrected total_vol for {x['am']}: {x['total_vol']} -> {total_vol}")
            x['total_vol'] = total_vol

    # 4. Repair GTC BC Data
    valid_gtc_bc = []
    for x in data.get('gtc_bc', []):
        if not x.get('bc'): 
            log_fix("Removed GTC BC entry with missing bưu cục name.")
            continue
        x['bc'] = normalize_name(x['bc'])
        x['am'] = normalize_name(x.get('am', ''))
        
        # Ensure leadtime is positive
        if safe_num(x.get('leadtime', 0)) < 0:
            x['leadtime'] = 0
            log_fix(f"Negative leadtime for {x['bc']} reset to 0.")
        
        valid_gtc_bc.append(x)
    data['gtc_bc'] = valid_gtc_bc

    # 5. Cross-Check consistency: GTC AM vs GTC BC
    # Sum of GTC BC volumes for an AM should roughly match GTC AM total_vol
    am_bc_vols = {}
    for x in data.get('gtc_bc', []):
        am = x.get('am')
        if am:
            am_bc_vols[am] = am_bc_vols.get(am, 0) + safe_num(x.get('total_vol', 0))
    
    for am_row in data.get('gtc_am', []):
        am = am_row.get('am')
        if am in am_bc_vols:
            bc_total = am_bc_vols[am]
            am_total = safe_num(am_row.get('total_vol', 0))
            if am_total > 0 and abs(bc_total - am_total) / am_total > 0.2: # More than 20% diff
                log_fix(f"Large discrepancy for {am}: AM report={am_total}, BC report sum={bc_total}")

    # 6. Repair HR Data (ns_am, ns_bc)
    for x in data.get('ns_am', []):
        x['am'] = normalize_name(x.get('am', ''))
        for k in ['ptt_can', 'ptt_co', 'so_thieu']:
            if safe_num(x.get(k, 0)) < 0:
                x[k] = 0
                log_fix(f"Negative HR metric {k} for {x['am']} reset to 0.")

    # 8. Smart Recalculation for Missing Totals
    # 8a. GTC Grand Totals
    gt_gtc = data.get('grand_total_gtc', {})
    if safe_num(gt_gtc.get('vol', 0)) == 0 and data.get('gtc_tinh'):
        log_fix("Recalculating grand_total_gtc from gtc_tinh.")
        vol = sum(safe_num(x.get('total_vol', 0)) for x in data['gtc_tinh'])
        gan = sum(safe_num(x.get('total_vol', 0)) * safe_num(x.get('total_gan', 0)) for x in data['gtc_tinh']) / max(vol, 1)
        gtc = sum(safe_num(x.get('total_vol', 0)) * safe_num(x.get('total_gtc', 0)) for x in data['gtc_tinh']) / max(vol, 1)
        data['grand_total_gtc'] = {'vol': vol, 'gan': gan, 'gtc': gtc}

    gt_tts = data.get('grand_total_gtc_tts', {})
    if safe_num(gt_tts.get('vol', 0)) == 0 and data.get('gtc_tts_tinh'):
        log_fix("Recalculating grand_total_gtc_tts from gtc_tts_tinh.")
        vol = sum(safe_num(x.get('total_vol', 0)) for x in data['gtc_tts_tinh'])
        gan = sum(safe_num(x.get('total_vol', 0)) * safe_num(x.get('total_gan', 0)) for x in data['gtc_tts_tinh']) / max(vol, 1)
        gtc = sum(safe_num(x.get('total_vol', 0)) * safe_num(x.get('total_gtc', 0)) for x in data['gtc_tts_tinh']) / max(vol, 1)
        data['grand_total_gtc_tts'] = {'vol': vol, 'gan': gan, 'gtc': gtc}

    # 8b. HR Totals
    ns_total = data.get('ns_total', {})
    if safe_num(ns_total.get('so_thieu', 0)) == 0 and safe_num(ns_total.get('ptt_can', 0)) > safe_num(ns_total.get('ptt_co', 0)):
        log_fix("Recalculating ns_total shortage.")
        ns_total['so_thieu'] = safe_num(ns_total.get('ptt_can', 0)) - safe_num(ns_total.get('ptt_co', 0))
    
    # Ensure ns_total is consistent with ns_am
    if data.get('ns_am'):
        am_can = sum(safe_num(x.get('ptt_can', 0)) for x in data['ns_am'])
        am_co = sum(safe_num(x.get('ptt_co', 0)) for x in data['ns_am'])
        if am_can > 0 and abs(am_can - safe_num(ns_total.get('ptt_can', 0))) > 5:
             log_fix(f"Updating ns_total from ns_am sum. Can: {ns_total.get('ptt_can')} -> {am_can}")
             ns_total['ptt_can'] = am_can
             ns_total['ptt_co'] = am_co
             ns_total['so_thieu'] = am_can - am_co
    data['ns_total'] = ns_total

    # 9. Final Save
    if json.dumps(data) != original_data:
        try:
            with open(data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            log_fix("Data repair completed and saved.")
        except Exception as e:
            logging.error(f"Failed to save repaired data: {e}")
            return False
    else:
        logging.info("Data validation passed. No fixes needed.")
    
    # Also update data.js
    try:
        with open(data_path.replace('.json', '.js'), 'w', encoding='utf-8') as f:
            f.write('window.globalData = ' + json.dumps(data, ensure_ascii=False) + ';')
    except: pass

    return True

if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else 'data.json'
    validate_and_repair(path)
