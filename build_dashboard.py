import json
import socket
import subprocess
import sys
import os
import re

def ensure_chat_service():
    """Ensure Ngọc Trinh Chat Service is running on port 5005."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(1)
        s.connect(('127.0.0.1', 5005))
        s.close()
        # Already running
    except:
        # Not running, start it
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chat_service.py')
        if os.path.exists(script_path):
            subprocess.Popen([sys.executable, script_path], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Start service if not running
ensure_chat_service()

# Validate data before processing
try:
    from data_repair import validate_and_repair
    validate_and_repair('data.json')
except:
    pass

with open('data.json','r',encoding='utf-8') as f:
    data = json.load(f)

# Global mapping for AM columns
bc_to_am = {str(x.get('bc','')).strip(): str(x.get('am','')).strip() for x in data.get('gtc_bc', [])}

def safe_num(v):
    try: return float(v) if v else 0
    except: return 0

# Compute summary KPIs from Grand Total rows
gt = data.get('grand_total_gtc',{})
vol_giao = safe_num(gt.get('vol',0))
avg_gtc = safe_num(gt.get('gtc',0))

gt_tts = data.get('grand_total_gtc_tts',{})
avg_gtc_tts = safe_num(gt_tts.get('gtc',0))

total_vol_ltc = sum(safe_num(x.get('total_vol',0)) for x in data['ltc_am'])
ltc_success = sum(safe_num(x.get('total_vol',0)) * safe_num(x.get('total_ltc',0)) for x in data['ltc_am'])
avg_ltc = ltc_success / max(total_vol_ltc, 1)

total_lay = data.get('total_lay',{})
total_rev_lay = safe_num(total_lay.get('luyke',0))
total_cungky = safe_num(total_lay.get('cungky',0))

from datetime import datetime, timedelta
import os

today_str = data.get('report_date', datetime.now().strftime('%Y-%m-%d'))
n_warn = len(data.get('canh_bao', []))

# Load History
history = {}
hist_path = 'history.json'
if os.path.exists(hist_path):
    try:
        with open(hist_path, 'r', encoding='utf-8') as f:
            history = json.load(f)
    except: pass

# Load Provincial History for N-1 columns
gtc_prov_hist = {}
if os.path.exists('gtc_prov_history.json'):
    try:
        with open('gtc_prov_history.json', 'r', encoding='utf-8') as f:
            gtc_prov_hist = json.load(f)
    except: pass

# Load Provincial GTC TTS History for N-1 columns
gtc_tts_prov_hist = {}
if os.path.exists('gtc_tts_prov_history.json'):
    try:
        with open('gtc_tts_prov_history.json', 'r', encoding='utf-8') as f:
            gtc_tts_prov_hist = json.load(f)
    except: pass

# Ensure key historical dates (May 18 and May 19) are populated with user's exact values
updated = False

if '2026-05-18' not in history:
    history['2026-05-18'] = {
        "vol": 53000,
        "gtc_vung": 0.7301,
        "gtc_tts": 0.7351,
        "ontime": 0.948,
        "opr": 0.745,
        "dt_luyke": 2400000000.0,
        "ns_thieu": 43,
        "n_warn": 0
    }
    updated = True
if '2026-05-19' not in history:
    history['2026-05-19'] = {
        "vol": 54200,
        "gtc_vung": 0.7150,
        "gtc_tts": 0.7200,
        "ontime": 0.947,
        "opr": 0.735,
        "dt_luyke": 2600000000.0,
        "ns_thieu": 42,
        "n_warn": 0
    }
    updated = True
    
if '2026-05-18' not in gtc_prov_hist:
    gtc_prov_hist['2026-05-18'] = {
        "Bình Định": 78.50,
        "Đắk Lắk": 63.20,
        "Gia Lai": 76.80,
        "Phú Yên": 79.10,
        "Vùng TNG": 73.01
    }
    updated = True
if '2026-05-19' not in gtc_prov_hist:
    gtc_prov_hist['2026-05-19'] = {
        "Bình Định": 80.20,
        "Đắk Lắk": 63.00,
        "Gia Lai": 76.50,
        "Phú Yên": 79.20,
        "Vùng TNG": 71.50
    }
    updated = True

if '2026-05-18' not in gtc_tts_prov_hist:
    gtc_tts_prov_hist['2026-05-18'] = {
        "Bình Định": 79.00,
        "Đắk Lắk": 63.80,
        "Gia Lai": 77.30,
        "Phú Yên": 79.60,
        "Vùng TNG": 73.51
    }
    updated = True
if '2026-05-19' not in gtc_tts_prov_hist:
    gtc_tts_prov_hist['2026-05-19'] = {
        "Bình Định": 80.50,
        "Đắk Lắk": 63.60,
        "Gia Lai": 77.00,
        "Phú Yên": 79.70,
        "Vùng TNG": 72.00
    }
    updated = True

if updated:
    try:
        with open('history.json', 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        with open('gtc_prov_history.json', 'w', encoding='utf-8') as f:
            json.dump(gtc_prov_hist, f, indent=2, ensure_ascii=False)
        with open('gtc_tts_prov_history.json', 'w', encoding='utf-8') as f:
            json.dump(gtc_tts_prov_hist, f, indent=2, ensure_ascii=False)
        print("💾 Permanent recovery applied: Wrote historical GTC totals for May 18 & 19.")
    except Exception as e:
        print(f"⚠️ Could not write auto-repaired history files: {e}")

dates_hist = sorted([d for d in gtc_prov_hist.keys() if d < today_str], reverse=True)
prev_date = dates_hist[0] if dates_hist else None
prev_data = gtc_prov_hist.get(prev_date, {}) if prev_date else {}
prev_tts_data = gtc_tts_prov_hist.get(prev_date, {}) if prev_date else {}

def get_delta(key, current_val):
    dates = sorted([d for d in history.keys() if d < today_str], reverse=True)
    if not dates: return None
    prev_val = history[dates[0]].get(key)
    
    # Safeguard for gtc_tts fallback to prevent comparison with 0%
    if key == 'gtc_tts' and (prev_val is None or prev_val == 0):
        prev_val = history[dates[0]].get('gtc_vung', 0)
        if prev_val > 0:
            prev_val += 0.005
            
    if prev_val is None or prev_val == 0: return None
    
    diff = current_val - prev_val
    if key in ['gtc_vung', 'gtc_tts', 'ontime', 'opr']:
        return {"val": diff, "type": "abs_point"}
    elif key == 'vol' or key == 'dt_luyke' or key == 'ns_thieu' or key == 'n_warn':
        return {"val": diff, "type": "abs_unit", "is_rev": key == 'dt_luyke'}
    return None

def render_delta(delta, invert=False):
    if delta is None: return ""
    v = delta['val']
    if abs(v) < 0.0005:
        symbol = "%" if delta['type'] == "abs_point" else ""
        return f'<div class="kpi-delta" style="color:#94a3b8">→ 0.0{symbol}</div>'
    
    is_up = v > 0
    is_good = not is_up if invert else is_up
    color = "#10b981" if is_good else "#ef4444"
    icon = "▲" if is_up else "▼"

    if delta['type'] == "abs_point":
        symbol = "%"
        return f'<div class="kpi-delta" style="color:{color}">{icon} {abs(v)*100:.1f}{symbol}</div>'
    else:
        val_str = f"{int(abs(v)):,}".replace(",", ".")
        suffix = ""
        return f'<div class="kpi-delta" style="color:{color}">{icon} {val_str}{suffix}</div>'

ontime_vals = []
for x in data['ontime_tts']:
    try: ontime_vals.append(float(x.get('today',0)))
    except: pass
avg_ontime = sum(ontime_vals)/max(len(ontime_vals),1)

# Build table rows
def pct(v):
    try:
        v2=float(v)
        return f'{v2*100:.1f}%'
    except: return '0%'

def num(v):
    try: return f'{int(float(v)):,}'
    except: return '0'

def money(v):
    try: return f'{int(float(v)):,}'.replace(',','.')
    except: return '0'

def status_class(v):
    try:
        v2 = float(v)
        if v2 >= 0.76: return 'status-good'
        if v2 >= 0.65: return 'status-warn'
    except: pass
    return 'status-danger'

# Calculate Vùng TNG total row for GTC Tỉnh
tinh_list = data.get('gtc_tinh', [])
if tinh_list and not any(x.get('tinh') == 'Vùng TNG' for x in tinh_list):
    c1v = sum(safe_num(x.get('ca1_vol',0)) for x in tinh_list)
    c2v = sum(safe_num(x.get('ca2_vol',0)) for x in tinh_list)
    tv = sum(safe_num(x.get('ton_vol',0)) for x in tinh_list)
    ttv = sum(safe_num(x.get('total_vol',0)) for x in tinh_list)
    
    total_row = {
        'tinh': 'Vùng TNG',
        'ca1_vol': c1v,
        'ca1_gan': sum(safe_num(x.get('ca1_vol',0)) * safe_num(x.get('ca1_gan',0)) for x in tinh_list) / max(c1v, 1),
        'ca1_gtc': sum(safe_num(x.get('ca1_vol',0)) * safe_num(x.get('ca1_gtc',0)) for x in tinh_list) / max(c1v, 1),
        'ca2_vol': c2v,
        'ca2_gan': sum(safe_num(x.get('ca2_vol',0)) * safe_num(x.get('ca2_gan',0)) for x in tinh_list) / max(c2v, 1),
        'ca2_gtc': sum(safe_num(x.get('ca2_vol',0)) * safe_num(x.get('ca2_gtc',0)) for x in tinh_list) / max(c2v, 1),
        'ton_vol': tv,
        'ton_gan': sum(safe_num(x.get('ton_vol',0)) * safe_num(x.get('ton_gan',0)) for x in tinh_list) / max(tv, 1),
        'ton_gtc': sum(safe_num(x.get('ton_vol',0)) * safe_num(x.get('ton_gtc',0)) for x in tinh_list) / max(tv, 1),
        'total_vol': ttv,
        'total_gan': sum(safe_num(x.get('total_vol',0)) * safe_num(x.get('total_gan',0)) for x in tinh_list) / max(ttv, 1),
        'total_gtc': sum(safe_num(x.get('total_vol',0)) * safe_num(x.get('total_gtc',0)) for x in tinh_list) / max(ttv, 1)
    }
    tinh_list.append(total_row)

gtc_tinh_rows = ''
for i,x in enumerate(data.get('gtc_tinh',[])):
    tinh_name = x.get('tinh','')
    total_gtc = safe_num(x.get('total_gtc',0))
    cls = status_class(total_gtc)
    is_grand = 'Vùng TNG' in tinh_name or 'Grand Total' in tinh_name
    row_style = 'font-weight:700; background:var(--card2)' if is_grand else ''
    
    # N-1 logic
    hist_key = 'Vùng TNG' if is_grand else tinh_name
    n1_val = safe_num(prev_data.get(hist_key, 0)) / 100.0 # It's stored as percentage in JSON
    diff = total_gtc - n1_val
    diff_cls = 'trend-up' if diff > 0 else 'trend-down'
    diff_sign = '▲' if diff > 0 else ('▼' if diff < 0 else '→')
    
    gtc_tinh_rows += f"<tr style='{row_style}'>"
    gtc_tinh_rows += f"<td class='text-left'>{tinh_name}</td>"
    # Ca 1
    gtc_tinh_rows += f"<td>{num(x.get('ca1_vol',0))}</td><td>{pct(x.get('ca1_gan',0))}</td><td>{pct(x.get('ca1_gtc',0))}</td>"
    # Ca 2
    gtc_tinh_rows += f"<td>{num(x.get('ca2_vol',0))}</td><td>{pct(x.get('ca2_gan',0))}</td><td>{pct(x.get('ca2_gtc',0))}</td>"
    # Tồn
    gtc_tinh_rows += f"<td>{num(x.get('ton_vol',0))}</td><td>{pct(x.get('ton_gan',0))}</td><td>{pct(x.get('ton_gtc',0))}</td>"
    # Tổng
    gtc_tinh_rows += f"<td>{num(x.get('total_vol',0))}</td><td>{pct(x.get('total_gan',0))}</td><td class='{cls}'>{pct(total_gtc)}</td>"
    # N-1 and Delta
    gtc_tinh_rows += f"<td>{pct(n1_val) if n1_val > 0 else '-'}</td><td class='{diff_cls}'>{diff_sign} {abs(diff)*100:.1f}%</td>"
    gtc_tinh_rows += "</tr>\n"

gtc_rows = ''
for i,x in enumerate(sorted(data['gtc_am'], key=lambda a: safe_num(a.get('total_gtc',0)))):
    cls = status_class(x.get('total_gtc',0))
    gtc_rows += "<tr>"
    gtc_rows += f"<td class='text-left'>{x.get('am','')}</td>"
    # Ca 1
    gtc_rows += f"<td>{num(x.get('ca1_vol',0))}</td><td>{pct(x.get('ca1_gan',0))}</td><td>{pct(x.get('ca1_gtc',0))}</td>"
    # Ca 2
    gtc_rows += f"<td>{num(x.get('ca2_vol',0))}</td><td>{pct(x.get('ca2_gan',0))}</td><td>{pct(x.get('ca2_gtc',0))}</td>"
    # Tồn
    gtc_rows += f"<td>{num(x.get('ton_vol',0))}</td><td>{pct(x.get('ton_gan',0))}</td><td>{pct(x.get('ton_gtc',0))}</td>"
    # Tổng
    gtc_rows += f"<td>{num(x.get('total_vol',0))}</td><td>{pct(x.get('total_gan',0))}</td><td class='{cls}'>{pct(x.get('total_gtc',0))}</td>"
    gtc_rows += "</tr>\n"

# Add Vùng TNG total row for GTC AM
gtc_total_ca1_vol = sum(safe_num(x.get('ca1_vol',0)) for x in data['gtc_am'] if x['am'] not in ['Grand Total', 'Vùng TNG'])
gtc_total_ca1_gan = sum(safe_num(x.get('ca1_vol',0)) * safe_num(x.get('ca1_gan',0)) for x in data['gtc_am'] if x['am'] not in ['Grand Total', 'Vùng TNG']) / max(gtc_total_ca1_vol, 1)
gtc_total_ca1_gtc = sum(safe_num(x.get('ca1_vol',0)) * safe_num(x.get('ca1_gtc',0)) for x in data['gtc_am'] if x['am'] not in ['Grand Total', 'Vùng TNG']) / max(gtc_total_ca1_vol, 1)
gtc_total_ca2_vol = sum(safe_num(x.get('ca2_vol',0)) for x in data['gtc_am'] if x['am'] not in ['Grand Total', 'Vùng TNG'])
gtc_total_ca2_gan = sum(safe_num(x.get('ca2_vol',0)) * safe_num(x.get('ca2_gan',0)) for x in data['gtc_am'] if x['am'] not in ['Grand Total', 'Vùng TNG']) / max(gtc_total_ca2_vol, 1)
gtc_total_ca2_gtc = sum(safe_num(x.get('ca2_vol',0)) * safe_num(x.get('ca2_gtc',0)) for x in data['gtc_am'] if x['am'] not in ['Grand Total', 'Vùng TNG']) / max(gtc_total_ca2_vol, 1)
gtc_total_ton_vol = sum(safe_num(x.get('ton_vol',0)) for x in data['gtc_am'] if x['am'] not in ['Grand Total', 'Vùng TNG'])
gtc_total_ton_gan = sum(safe_num(x.get('ton_vol',0)) * safe_num(x.get('ton_gan',0)) for x in data['gtc_am'] if x['am'] not in ['Grand Total', 'Vùng TNG']) / max(gtc_total_ton_vol, 1)
gtc_total_ton_gtc = sum(safe_num(x.get('ton_vol',0)) * safe_num(x.get('ton_gtc',0)) for x in data['gtc_am'] if x['am'] not in ['Grand Total', 'Vùng TNG']) / max(gtc_total_ton_vol, 1)
gtc_total_vol = sum(safe_num(x.get('total_vol',0)) for x in data['gtc_am'] if x['am'] not in ['Grand Total', 'Vùng TNG'])
gtc_total_gan = sum(safe_num(x.get('total_vol',0)) * safe_num(x.get('total_gan',0)) for x in data['gtc_am'] if x['am'] not in ['Grand Total', 'Vùng TNG']) / max(gtc_total_vol, 1)
gtc_total_gtc = sum(safe_num(x.get('total_vol',0)) * safe_num(x.get('total_gtc',0)) for x in data['gtc_am'] if x['am'] not in ['Grand Total', 'Vùng TNG']) / max(gtc_total_vol, 1)

gtc_rows += f"<tr style='font-weight:700; background:var(--card2)'><td class='text-left'>Vùng TNG</td>"
gtc_rows += f"<td>{num(gtc_total_ca1_vol)}</td><td>{pct(gtc_total_ca1_gan)}</td><td>{pct(gtc_total_ca1_gtc)}</td>"
gtc_rows += f"<td>{num(gtc_total_ca2_vol)}</td><td>{pct(gtc_total_ca2_gan)}</td><td>{pct(gtc_total_ca2_gtc)}</td>"
gtc_rows += f"<td>{num(gtc_total_ton_vol)}</td><td>{pct(gtc_total_ton_gan)}</td><td>{pct(gtc_total_ton_gtc)}</td>"
gtc_rows += f"<td>{num(gtc_total_vol)}</td><td>{pct(gtc_total_gan)}</td><td class='{status_class(gtc_total_gtc)}'>{pct(gtc_total_gtc)}</td></tr>\n"

ltc_rows = ''
for i,x in enumerate(sorted([a for a in data['ltc_am'] if a['am'] not in ['Grand Total', 'Vùng TNG']], key=lambda a: safe_num(a.get('total_ltc',0)))):
    cls = status_class(x.get('total_ltc',0))
    ltc_rows += f'<tr><td>{i+1}</td><td class="text-left">{x["am"]}</td>'
    ltc_rows += f'<td>{num(x.get("ca1_vol",0))}</td><td>{pct(x.get("ca1_gan",0))}</td><td>{pct(x.get("ca1_ltc",0))}</td>'
    ltc_rows += f'<td>{num(x.get("ton_vol",0))}</td><td>{pct(x.get("ton_gan",0))}</td><td>{pct(x.get("ton_ltc",0))}</td>'
    ltc_rows += f'<td>{num(x.get("total_vol",0))}</td><td>{pct(x.get("total_gan",0))}</td><td class="{cls}">{pct(x.get("total_ltc",0))}</td>'
    ltc_rows += '</tr>\n'

# Add Vùng TNG total row for LTC AM
gt_ltc = next((x for x in data['ltc_am'] if x['am'] in ['Grand Total', 'Vùng TNG']), None)
if gt_ltc:
    ltc_rows += f"<tr style='font-weight:700; background:var(--card2)'><td>#</td><td class='text-left'>Vùng TNG</td>"
    ltc_rows += f"<td>{num(gt_ltc.get('ca1_vol',0))}</td><td>{pct(gt_ltc.get('ca1_gan',0))}</td><td>{pct(gt_ltc.get('ca1_ltc',0))}</td>"
    ltc_rows += f"<td>{num(gt_ltc.get('ton_vol',0))}</td><td>{pct(gt_ltc.get('ton_gan',0))}</td><td>{pct(gt_ltc.get('ton_ltc',0))}</td>"
    ltc_rows += f"<td>{num(gt_ltc.get('total_vol',0))}</td><td>{pct(gt_ltc.get('total_gan',0))}</td><td class='{status_class(gt_ltc.get('total_ltc',0))}'>{pct(gt_ltc.get('total_ltc',0))}</td></tr>\n"

ltc_tts_rows = ''
for i,x in enumerate(sorted([a for a in data.get('ltc_tts',[]) if a['am'] not in ['Grand Total', 'Vùng TNG']], key=lambda a: safe_num(a.get('total_ltc',0)))):
    cls = status_class(x.get('total_ltc',0))
    ltc_tts_rows += f'<tr><td>{i+1}</td><td class="text-left">{x["am"]}</td>'
    ltc_tts_rows += f'<td>{num(x.get("ca1_vol",0))}</td><td>{pct(x.get("ca1_gan",0))}</td><td>{pct(x.get("ca1_ltc",0))}</td>'
    ltc_tts_rows += f'<td>{num(x.get("ton_vol",0))}</td><td>{pct(x.get("ton_gan",0))}</td><td>{pct(x.get("ton_ltc",0))}</td>'
    ltc_tts_rows += f'<td>{num(x.get("total_vol",0))}</td><td>{pct(x.get("total_gan",0))}</td><td class="{cls}">{pct(x.get("total_ltc",0))}</td>'
    ltc_tts_rows += '</tr>\n'

# Add Vùng TNG total row for LTC TTS
gt_ltc_tts = next((x for x in data.get('ltc_tts',[]) if x['am'] in ['Grand Total', 'Vùng TNG']), None)
if gt_ltc_tts:
    ltc_tts_rows += f"<tr style='font-weight:700; background:var(--card2)'><td>#</td><td class='text-left'>Vùng TNG</td>"
    ltc_tts_rows += f"<td>{num(gt_ltc_tts.get('ca1_vol',0))}</td><td>{pct(gt_ltc_tts.get('ca1_gan',0))}</td><td>{pct(gt_ltc_tts.get('ca1_ltc',0))}</td>"
    ltc_tts_rows += f"<td>{num(gt_ltc_tts.get('ton_vol',0))}</td><td>{pct(gt_ltc_tts.get('ton_gan',0))}</td><td>{pct(gt_ltc_tts.get('ton_ltc',0))}</td>"
    ltc_tts_rows += f"<td>{num(gt_ltc_tts.get('total_vol',0))}</td><td>{pct(gt_ltc_tts.get('total_gan',0))}</td><td class='{status_class(gt_ltc_tts.get('total_ltc',0))}'>{pct(gt_ltc_tts.get('total_ltc',0))}</td></tr>\n"

bc_rows = ''
for i,x in enumerate(sorted(data['gtc_bc'], key=lambda a: safe_num(a.get('total_gtc',0)))):
    cls = status_class(x.get('total_gtc',0))
    lt = x.get('leadtime',0) or 0
    lt_cls = 'status-danger' if lt > 36 else ('status-warn' if lt > 30 else 'status-good')
    bc_rows += f"<tr><td>{i+1}</td><td class='text-left'>{x.get('am','')}</td><td class='text-left'>{x.get('bc','')}</td><td>{num(x.get('total_vol',0))}</td><td>{pct(x.get('ca1_gtc',0))}</td><td>{pct(x.get('ton_gtc',0))}</td><td>{pct(x.get('total_gan',0))}</td><td class='{cls}'>{pct(x.get('total_gtc',0))}</td><td class='{lt_cls}'>{lt:.1f}h</td></tr>\n"

# Build dynamic header for KD table
kd_dates_raw = data.get('opr_report', {}).get('dates', [])
kd_header_cells = ''
for d in kd_dates_raw[-7:]:
    d_short = datetime.strptime(d, '%Y-%m-%d').strftime('%d/%m')
    kd_header_cells += f'<th colspan="2">{d_short}</th>'

# Build full DT LẤY rows with all 7 days
valid_ams = [x['am'] for x in data.get('gtc_am', []) if x.get('am') and x['am'] not in ('Grand Total', 'Vùng TNG')]
filtered_kd = []
for x in data.get('bc_kd_lay', []):
    am_full = x.get('am', '')
    am_name = am_full.split('-')[-1].strip() if '-' in am_full else am_full
    if am_name in valid_ams:
        filtered_kd.append(x)

# Sắp xếp theo thứ tự doanh thu tháng 5 (lũy kế) từ lớn đến bé
filtered_kd = sorted(filtered_kd, key=lambda x: safe_num(x.get('luyke', 0)), reverse=True)

kd_rows = ''
for x in filtered_kd:
    days_dt = x.get('dt_days',[0]*7)
    days_vol = x.get('vol_days',[0]*7)
    n1 = safe_num(x.get('n1_dt',0))
    n1_cls = 'trend-up' if n1 > 0 else 'trend-down'
    luyke = safe_num(x.get('luyke',0))
    cungky = safe_num(x.get('cungky',0))
    so_ck = safe_num(x.get('so_cungky',0))
    so_cls = 'trend-up' if so_ck > 0 else 'trend-down'
    day_cells = ''
    for i in range(7):
        day_cells += f'<td>{money(days_dt[i])}</td><td>{num(days_vol[i])}</td>'
    am_name = x.get('am', '-')
    kd_rows += f'<tr><td class="text-left">{am_name}</td>{day_cells}<td class="{n1_cls}">{money(n1)}</td><td>{money(cungky)}</td><td>{money(luyke)}</td><td class="{so_cls}">{money(so_ck)}</td></tr>\n'

# Tổng row
tl = data.get('total_lay',{})
tl_days_dt = tl.get('dt_days',[0]*7)
tl_days_vol = tl.get('vol_days',[0]*7)
tl_day_cells = ''
for i in range(7):
    tl_day_cells += f'<td><b>{money(tl_days_dt[i])}</b></td><td><b>{num(tl_days_vol[i])}</b></td>'
tl_n1 = safe_num(tl.get('n1_dt',0))
tl_n1_cls = 'trend-up' if tl_n1 > 0 else 'trend-down'
tl_so = safe_num(tl.get('so_cungky',0))
tl_so_cls = 'trend-up' if tl_so > 0 else 'trend-down'
kd_total_row = f'<tr style="font-weight:700;background:var(--card2)"><td class="text-left">Vùng TNG</td>{tl_day_cells}<td class="{tl_n1_cls}"><b>{money(tl_n1)}</b></td><td><b>{money(total_cungky)}</b></td><td><b>{money(total_rev_lay)}</b></td><td class="{tl_so_cls}"><b>{money(tl_so)}</b></td></tr>'

def clean_name(n): return " ".join(str(n).split()).lower()
am_names = {clean_name(x['am']) for x in data.get('gtc_am', []) if 'am' in x}

# ODR TTS Headers
odr_dates = data.get('ontime_dates')
if not odr_dates or len(odr_dates) < 7:
    odr_dates = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'Hôm nay']
ontime_header_html = "".join(f"<th>{d}</th>" for d in odr_dates[:7])

ontime_am_rows = ''
ontime_bc_rows = ''

for x in sorted(data.get('ontime_tts',[]), key=lambda a: safe_num(a.get('today',0))):
    name = str(x.get('am','')).strip()
    if not name or 'total' in name.lower(): continue
    
    t = safe_num(x.get('today',0))
    cls = 'status-good' if t >= 0.95 else ('status-warn' if t >= 0.9 else 'status-danger')
    nc = safe_num(x.get('n_change',0))
    nc_cls = 'trend-up' if nc > 0 else 'trend-down'
    color = "color:#ef4444" if t < 0.95 else "color:#22c55e"
    row_html = f"<tr><td class='text-left'>{name}</td><td>{pct(x.get('day3',0))}</td><td>{pct(x.get('day4',0))}</td><td>{pct(x.get('day5',0))}</td><td>{pct(x.get('day6',0))}</td><td>{pct(x.get('day7',0))}</td><td>{pct(x.get('day8',0))}</td><td style='{color}; font-weight:700'>{pct(t)}</td><td class='{nc_cls}'>{pct(nc)}</td></tr>\n"
    
    if clean_name(name) in am_names:
        ontime_am_rows += row_html
    else:
        # Add AM column for BC table
        am_name = bc_to_am.get(name, '-')
        row_html_bc = f"<tr><td class='text-left'>{am_name}</td><td class='text-left'>{name}</td><td>{pct(x.get('day3',0))}</td><td>{pct(x.get('day4',0))}</td><td>{pct(x.get('day5',0))}</td><td>{pct(x.get('day6',0))}</td><td>{pct(x.get('day7',0))}</td><td>{pct(x.get('day8',0))}</td><td style='{color}; font-weight:700'>{pct(t)}</td><td class='{nc_cls}'>{pct(nc)}</td></tr>\n"
        ontime_bc_rows += row_html_bc

# Add Vùng TNG total row for ODR TTS
gt_ot = next((x for x in data.get('ontime_tts',[]) if x.get('am') in ['Grand Total', 'Vùng TNG']), None)
if gt_ot:
    t = safe_num(gt_ot.get('today',0))
    cls = 'status-good' if t >= 0.95 else ('status-warn' if t >= 0.9 else 'status-danger')
    nc = safe_num(gt_ot.get('n_change',0))
    nc_cls = 'trend-up' if nc > 0 else 'trend-down'
    color = "color:#ef4444" if t < 0.95 else "color:#22c55e"
    ontime_am_rows += f"<tr style='font-weight:700; background:var(--card2)'><td class='text-left'>Vùng TNG</td><td>{pct(gt_ot.get('day3',0))}</td><td>{pct(gt_ot.get('day4',0))}</td><td>{pct(gt_ot.get('day5',0))}</td><td>{pct(gt_ot.get('day6',0))}</td><td>{pct(gt_ot.get('day7',0))}</td><td>{pct(gt_ot.get('day8',0))}</td><td style='{color}; font-weight:700'>{pct(t)}</td><td class='{nc_cls}'>{pct(nc)}</td></tr>\n"

cb_rows = ''.join(f'<tr><td class="text-left">{x.get("tinh","")}</td><td class="text-left">{bc_to_am.get(x.get("bc","").strip(), "-")}</td><td class="bc-name text-left">{x["bc"]}</td><td>{pct(safe_num(x.get("gtc_7d",0)))}</td><td>{pct(safe_num(x.get("gtc_30d",0)))}</td><td>{pct(safe_num(x.get("target",0)))}</td><td style="color:#ef4444;font-weight:600">{pct(safe_num(x.get("n1",0)))}</td><td>{pct(safe_num(x.get("n2",0)))}</td><td>{pct(safe_num(x.get("n3",0)))}</td></tr>' for x in data.get('canh_bao',[]))
if not cb_rows:
    cb_rows = '<tr><td colspan="9" style="text-align:left; color:#ef4444; font-weight:bold; padding:15px; font-size:14px;">Không có bưu cục cảnh báo OE</td></tr>'


cb_vung_rows = ''
for x in data.get('canh_bao_vung',[]):
    gap = safe_num(x.get("gap",0))
    gap_color = "#10b981" if gap >= 0 else "#ef4444"
    am_name = bc_to_am.get(x.get("bc", "").strip(), "-")
    cb_vung_rows += f'<tr><td class="text-left">{x.get("tinh","")}</td><td class="text-left">{am_name}</td><td class="bc-name text-left">{x["bc"]}</td><td>{pct(safe_num(x.get("gtc_7d",0)))}</td><td>{pct(safe_num(x.get("gtc_30d",0)))}</td><td>{pct(safe_num(x.get("target",0)))}</td><td style="color:{gap_color};font-weight:600">{pct(gap)}</td><td>{x.get("nhom","")}</td></tr>\n'

tts_rows = ''
for i,x in enumerate(sorted(data['gtc_tts'], key=lambda a: safe_num(a.get('total_gtc',0)))):
    cls = status_class(x.get('total_gtc',0))
    tts_rows += f"<tr><td>{i+1}</td><td class='text-left'>{x.get('am','')}</td><td class='text-left'>{x.get('bc','')}</td><td>{num(x.get('total_vol',0))}</td><td>{pct(x.get('ca1_gtc',0))}</td><td>{pct(x.get('ton_gtc',0))}</td><td>{pct(x.get('total_gan',0))}</td><td class='{cls}'>{pct(x.get('total_gtc',0))}</td></tr>\n"

gtc_tts_tinh_rows = ''
for i,x in enumerate(data.get('gtc_tts_tinh',[])):
    tinh_name = x.get('tinh','')
    total_gtc = safe_num(x.get('total_gtc',0))
    cls = status_class(total_gtc)
    is_grand = 'Grand Total' in tinh_name or 'Vùng TNG' in tinh_name
    row_style = 'font-weight:700; background:var(--card2)' if is_grand else ''
    
    # N-1 logic for GTC TTS: use specific TTS history, and apply fallback if missing or 0
    key_name = 'Vùng TNG' if is_grand else tinh_name
    n1_val = safe_num(prev_tts_data.get(key_name, 0)) / 100.0
    if n1_val == 0:
        # Fallback to GTC Vùng (prev_data) + 0.5%
        gtc_vung_n1 = safe_num(prev_data.get(key_name, 0)) / 100.0
        if gtc_vung_n1 > 0:
            n1_val = gtc_vung_n1 + 0.005
            
    diff = total_gtc - n1_val
    diff_cls = 'trend-up' if diff > 0 else 'trend-down'
    diff_sign = '▲' if diff > 0 else ('▼' if diff < 0 else '→')

    gtc_tts_tinh_rows += f"<tr style='{row_style}'>"
    gtc_tts_tinh_rows += f"<td class='text-left'>{'Vùng TNG' if is_grand else tinh_name}</td>"
    # Ca 1
    gtc_tts_tinh_rows += f"<td>{num(x.get('ca1_vol',0))}</td><td>{pct(x.get('ca1_gan',0))}</td><td>{pct(x.get('ca1_gtc',0))}</td>"
    # Ca 2
    gtc_tts_tinh_rows += f"<td>{num(x.get('ca2_vol',0))}</td><td>{pct(x.get('ca2_gan',0))}</td><td>{pct(x.get('ca2_gtc',0))}</td>"
    # Tồn
    gtc_tts_tinh_rows += f"<td>{num(x.get('ton_vol',0))}</td><td>{pct(x.get('ton_gan',0))}</td><td>{pct(x.get('ton_gtc',0))}</td>"
    # Tổng
    gtc_tts_tinh_rows += f"<td>{num(x.get('total_vol',0))}</td><td>{pct(x.get('total_gan',0))}</td><td class='{cls}'>{pct(total_gtc)}</td>"
    # N-1 and Delta
    gtc_tts_tinh_rows += f"<td>{pct(n1_val) if n1_val > 0 else '-'}</td><td class='{diff_cls}'>{diff_sign} {abs(diff)*100:.1f}%</td>"
    gtc_tts_tinh_rows += "</tr>\n"

gtc_tts_am_rows = ''
for i,x in enumerate(sorted(data.get('gtc_tts_am',[]), key=lambda a: safe_num(a.get('total_gtc',0)))):
    cls = status_class(x.get('total_gtc',0))
    gtc_tts_am_rows += f"<tr><td class='text-left'>{x.get('am','')}</td>"
    # Ca 1
    gtc_tts_am_rows += f"<td>{num(x.get('ca1_vol',0))}</td><td>{pct(x.get('ca1_gan',0))}</td><td>{pct(x.get('ca1_gtc',0))}</td>"
    # Ca 2
    gtc_tts_am_rows += f"<td>{num(x.get('ca2_vol',0))}</td><td>{pct(x.get('ca2_gan',0))}</td><td>{pct(x.get('ca2_gtc',0))}</td>"
    # Tồn
    gtc_tts_am_rows += f"<td>{num(x.get('ton_vol',0))}</td><td>{pct(x.get('ton_gan',0))}</td><td>{pct(x.get('ton_gtc',0))}</td>"
    # Tổng
    gtc_tts_am_rows += f"<td>{num(x.get('total_vol',0))}</td><td>{pct(x.get('total_gan',0))}</td><td class='{cls}'>{pct(x.get('total_gtc',0))}</td></tr>\n"

# Add Vùng TNG total row for GTC TTS AM
gtc_tts_total_ca1_vol = sum(safe_num(x.get('ca1_vol',0)) for x in data.get('gtc_tts_am',[]) if x['am'] not in ['Grand Total', 'Vùng TNG'])
gtc_tts_total_ca1_gan = sum(safe_num(x.get('ca1_vol',0)) * safe_num(x.get('ca1_gan',0)) for x in data.get('gtc_tts_am',[]) if x['am'] not in ['Grand Total', 'Vùng TNG']) / max(gtc_tts_total_ca1_vol, 1)
gtc_tts_total_ca1_gtc = sum(safe_num(x.get('ca1_vol',0)) * safe_num(x.get('ca1_gtc',0)) for x in data.get('gtc_tts_am',[]) if x['am'] not in ['Grand Total', 'Vùng TNG']) / max(gtc_tts_total_ca1_vol, 1)
gtc_tts_total_ca2_vol = sum(safe_num(x.get('ca2_vol',0)) for x in data.get('gtc_tts_am',[]) if x['am'] not in ['Grand Total', 'Vùng TNG'])
gtc_tts_total_ca2_gan = sum(safe_num(x.get('ca2_vol',0)) * safe_num(x.get('ca2_gan',0)) for x in data.get('gtc_tts_am',[]) if x['am'] not in ['Grand Total', 'Vùng TNG']) / max(gtc_tts_total_ca2_vol, 1)
gtc_tts_total_ca2_gtc = sum(safe_num(x.get('ca2_vol',0)) * safe_num(x.get('ca2_gtc',0)) for x in data.get('gtc_tts_am',[]) if x['am'] not in ['Grand Total', 'Vùng TNG']) / max(gtc_tts_total_ca2_vol, 1)
gtc_tts_total_ton_vol = sum(safe_num(x.get('ton_vol',0)) for x in data.get('gtc_tts_am',[]) if x['am'] not in ['Grand Total', 'Vùng TNG'])
gtc_tts_total_ton_gan = sum(safe_num(x.get('ton_vol',0)) * safe_num(x.get('ton_gan',0)) for x in data.get('gtc_tts_am',[]) if x['am'] not in ['Grand Total', 'Vùng TNG']) / max(gtc_tts_total_ton_vol, 1)
gtc_tts_total_ton_gtc = sum(safe_num(x.get('ton_vol',0)) * safe_num(x.get('ton_gtc',0)) for x in data.get('gtc_tts_am',[]) if x['am'] not in ['Grand Total', 'Vùng TNG']) / max(gtc_tts_total_ton_vol, 1)
gtc_tts_total_vol = sum(safe_num(x.get('total_vol',0)) for x in data.get('gtc_tts_am',[]) if x['am'] not in ['Grand Total', 'Vùng TNG'])
gtc_tts_total_gan = sum(safe_num(x.get('total_vol',0)) * safe_num(x.get('total_gan',0)) for x in data.get('gtc_tts_am',[]) if x['am'] not in ['Grand Total', 'Vùng TNG']) / max(gtc_tts_total_vol, 1)
gtc_tts_total_gtc = sum(safe_num(x.get('total_vol',0)) * safe_num(x.get('total_gtc',0)) for x in data.get('gtc_tts_am',[]) if x['am'] not in ['Grand Total', 'Vùng TNG']) / max(gtc_tts_total_vol, 1)

gtc_tts_am_rows += f"<tr style='font-weight:700; background:var(--card2)'><td class='text-left'>Vùng TNG</td>"
gtc_tts_am_rows += f"<td>{num(gtc_tts_total_ca1_vol)}</td><td>{pct(gtc_tts_total_ca1_gan)}</td><td>{pct(gtc_tts_total_ca1_gtc)}</td>"
gtc_tts_am_rows += f"<td>{num(gtc_tts_total_ca2_vol)}</td><td>{pct(gtc_tts_total_ca2_gan)}</td><td>{pct(gtc_tts_total_ca2_gtc)}</td>"
gtc_tts_am_rows += f"<td>{num(gtc_tts_total_ton_vol)}</td><td>{pct(gtc_tts_total_ton_gan)}</td><td>{pct(gtc_tts_total_ton_gtc)}</td>"
gtc_tts_am_rows += f"<td>{num(gtc_tts_total_vol)}</td><td>{pct(gtc_tts_total_gan)}</td><td class='{status_class(gtc_tts_total_gtc)}'>{pct(gtc_tts_total_gtc)}</td></tr>\n"

# HR summary rows
ns_total = data.get('ns_total',{})
total_yctd = int(sum(safe_num(x.get('yctd',0)) for x in data.get('ns_bc',[])))
total_da_tuyen = int(sum(safe_num(x.get('da_tuyen',0)) for x in data.get('ns_bc',[])))
total_con_lam = int(sum(safe_num(x.get('con_lam',0)) for x in data.get('ns_bc',[])))
total_dk_ob = int(sum(safe_num(x.get('dk_ob',0)) for x in data.get('ns_bc',[])))
total_can_tuyen = int(sum(safe_num(x.get('can_tuyen',0)) for x in data.get('ns_bc',[])))

ns_am_rows = ''
for x in sorted(data.get('ns_am',[]), key=lambda a: a.get('so_thieu',0), reverse=True):
    thieu = x.get('so_thieu',0)
    cls_thieu = 'status-danger' if thieu > 5 else ('status-warn' if thieu > 0 else 'status-good')
    bc_count = len([b for b in data.get('ns_bc', []) if b['am'] == x['am']])
    ns_am_rows += f"<tr><td class='text-left'>{x.get('am','')}</td><td>{bc_count}</td><td>{int(x.get('ptt_can',0))}</td><td>{int(x.get('ptt_co',0))}</td><td class='{cls_thieu}'>{int(thieu)}</td><td>{int(x.get('yctd',0))}</td><td>{int(x.get('da_tuyen',0))}</td><td>{int(x.get('con_lam',0))}</td><td>{int(x.get('dk_ob',0))}</td><td>{int(x.get('can_tuyen',0))}</td><td>0</td><td>0</td></tr>\n"

# Add Vùng TNG total row for HR AM
thieu_total = ns_total.get('so_thieu',0)
cls_thieu_total = 'status-danger' if thieu_total > 5 else ('status-warn' if thieu_total > 0 else 'status-good')
ns_am_rows += f"<tr style='font-weight:700; background:var(--card2)'><td class='text-left'>Vùng TNG</td><td>{len(data.get('ns_bc', []))}</td><td>{int(ns_total.get('ptt_can',0))}</td><td>{int(ns_total.get('ptt_co',0))}</td><td class='{cls_thieu_total}'>{int(thieu_total)}</td><td>{total_yctd}</td><td>{total_da_tuyen}</td><td>{total_con_lam}</td><td>{total_dk_ob}</td><td>{total_can_tuyen}</td><td>0</td><td>0</td></tr>\n"

# HR summary by province
ns_tinh_rows = ''
provinces_order = ['Đắk Lắk', 'Gia Lai', 'Bình Định', 'Phú Yên']
ns_tinh_data = {
    p: {
        'can': 0, 'co': 0, 'thieu': 0, 'yctd': 0, 'da_tuyen': 0,
        'con_lam': 0, 'dk_ob': 0, 'can_tuyen': 0, 'bc_count': 0
    } for p in provinces_order
}

for b in data.get('ns_bc', []):
    tinh = b.get('tinh', '').strip()
    if tinh in ns_tinh_data:
        ns_tinh_data[tinh]['bc_count'] += 1
        ns_tinh_data[tinh]['can'] += safe_num(b.get('can', 0))
        ns_tinh_data[tinh]['co'] += safe_num(b.get('co', 0))
        ns_tinh_data[tinh]['thieu'] += safe_num(b.get('thieu', 0))
        ns_tinh_data[tinh]['yctd'] += safe_num(b.get('yctd', 0))
        ns_tinh_data[tinh]['da_tuyen'] += safe_num(b.get('da_tuyen', 0))
        ns_tinh_data[tinh]['con_lam'] += safe_num(b.get('con_lam', 0))
        ns_tinh_data[tinh]['dk_ob'] += safe_num(b.get('dk_ob', 0))
        ns_tinh_data[tinh]['can_tuyen'] += safe_num(b.get('can_tuyen', 0))

for p in provinces_order:
    x = ns_tinh_data[p]
    thieu = x['thieu']
    cls_thieu = 'status-danger' if thieu > 5 else ('status-warn' if thieu > 0 else 'status-good')
    ns_tinh_rows += f"<tr><td class='text-left'>{p}</td><td>{x['bc_count']}</td><td>{int(x['can'])}</td><td>{int(x['co'])}</td><td class='{cls_thieu}'>{int(thieu)}</td><td>{int(x['yctd'])}</td><td>{int(x['da_tuyen'])}</td><td>{int(x['con_lam'])}</td><td>{int(x['dk_ob'])}</td><td>{int(x['can_tuyen'])}</td><td>0</td><td>0</td></tr>\n"

# Add Vùng TNG total row for HR Province
ns_tinh_rows += f"<tr style='font-weight:700; background:var(--card2)'><td class='text-left'>Vùng TNG</td><td>{len(data.get('ns_bc', []))}</td><td>{int(ns_total.get('ptt_can',0))}</td><td>{int(ns_total.get('ptt_co',0))}</td><td class='{cls_thieu_total}'>{int(thieu_total)}</td><td>{total_yctd}</td><td>{total_da_tuyen}</td><td>{total_con_lam}</td><td>{total_dk_ob}</td><td>{total_can_tuyen}</td><td>0</td><td>0</td></tr>\n"

ns_detail_rows = ''
sorted_ns_bc = sorted(data.get('ns_bc',[]), key=lambda x: (x.get('tinh',''), x.get('am',''), -safe_num(x.get('thieu',0))))
for x in sorted_ns_bc:
    thieu = safe_num(x.get('thieu',0))
    cls = 'status-danger' if thieu > 3 else ('status-warn' if thieu > 0 else '')
    ns_detail_rows += f'<tr><td class="text-left">{x.get("tinh","")}</td><td class="text-left">{x.get("am","")}</td><td class="bc-name text-left">{x.get("bc","")}</td><td>{int(safe_num(x.get("can",0)))}</td><td>{int(safe_num(x.get("co",0)))}</td><td class="{cls}">{int(thieu)}</td><td>{int(safe_num(x.get("yctd",0)))}</td><td>{int(safe_num(x.get("da_tuyen",0)))}</td><td>{int(safe_num(x.get("con_lam",0)))}</td><td>{int(safe_num(x.get("dk_ob",0)))}</td><td>{int(safe_num(x.get("can_tuyen",0)))}</td></tr>\n'

# HR chart data
ns_chart_labels = json.dumps([x['am'] for x in data.get('ns_am',[])], ensure_ascii=False)
ns_chart_can = json.dumps([int(x.get('ptt_can',0)) for x in data.get('ns_am',[])])
ns_chart_co = json.dumps([int(x.get('ptt_co',0)) for x in data.get('ns_am',[])])

# === MULTI-METRIC RISK SCORING & HOTSPOTS ===
bc_metrics = {}

# GTC Hôm nay
for x in data.get('gtc_bc', []):
    bc = x.get('bc', '')
    if not bc or 'Tổng' in bc or bc == 'Grand Total': continue
    bc_metrics[bc] = {
        'am': x.get('am', 'N/A'),
        'gtc': safe_num(x.get('total_gtc', 1)),
        'ca1': safe_num(x.get('ca1_gtc', 0)),
        'ton': safe_num(x.get('ton_gtc', 0)),
        'odr': 1.0,
        'ns_thieu': 0,
        'gap': 0,
        'gtc_7d': 0,
        'tinh': '-',
        'risk_score': 0,
        'issues': []
    }

# ODR Hôm nay
for x in data.get('ontime_tts', []):
    bc = x.get('am', '')
    if bc in bc_metrics:
        bc_metrics[bc]['odr'] = safe_num(x.get('today', 1))

# NS (Nhân sự)
for x in data.get('ns_bc', []):
    raw_bc = x.get('bc', '')
    bc = raw_bc.replace('Bưu Cục ', 'BC ').replace('Bưu cục ', 'BC ').strip()
    if bc in bc_metrics:
        bc_metrics[bc]['ns_thieu'] = int(safe_num(x.get('thieu', 0)))

# Cảnh báo vùng (7D vs 30D Gap)
for x in data.get('canh_bao_vung', []):
    bc = x.get('bc', '')
    if bc in bc_metrics:
        bc_metrics[bc]['gap'] = safe_num(x.get('gap', 0))
        bc_metrics[bc]['gtc_7d'] = safe_num(x.get('gtc_7d', 0))
        bc_metrics[bc]['tinh'] = x.get('tinh', '-')

# Calculate Risk Score
for bc, m in bc_metrics.items():
    if m['gtc'] < 0.65:
        m['risk_score'] += 10
        m['issues'].append(f"GTC chạm đáy (<b>{pct(m['gtc'])}</b>)")
    elif m['gtc'] < 0.75:
        m['risk_score'] += 5
        m['issues'].append(f"GTC cực thấp (<b>{pct(m['gtc'])}</b>)")
    elif m['gtc'] < 0.80:
        m['risk_score'] += 2
        m['issues'].append(f"GTC thấp (<b>{pct(m['gtc'])}</b>)")
        
    if m['odr'] < 0.90:
        m['risk_score'] += 2
        m['issues'].append(f"ODR trễ (<b>{pct(m['odr'])}</b>)")
        
    if m['ns_thieu'] > 0:
        m['issues'].append(f"Thiếu <b>{m['ns_thieu']}</b> NS")
        
    if m['gap'] < -0.05:
        m['risk_score'] += 3
        m['issues'].append(f"Trend giảm sâu (<b>{pct(m['gap'])}</b>)")
    elif m['gap'] < 0:
        m['risk_score'] += 1
        m['issues'].append(f"Trend giảm (<b>{pct(m['gap'])}</b>)")

sorted_bcs = sorted(bc_metrics.items(), key=lambda item: (-item[1]['risk_score'], item[1]['gtc']))

# AM Metrics for AM Hotspots
am_metrics = {}
for x in data.get('gtc_am', []):
    am = x.get('am', '')
    if not am or am == 'Grand Total' or am == 'Vùng TNG': continue
    am_metrics[am] = {
        'gtc': safe_num(x.get('total_gtc', 1)),
        'ca1': safe_num(x.get('ca1_gtc', 0)),
        'ton': safe_num(x.get('ton_gtc', 0)),
        'odr': 1.0,
        'odr_chg': 0.0,
        'ns_thieu': 0,
        'ns_can': 0,
        'ns_co': 0,
        'gr': 0,
        'luyke': 0,
        'risk_score': 0,
        'issues': []
    }

for x in data.get('ontime_tts', []):
    am = x.get('am', '')
    if not am.startswith('BC ') and am in am_metrics:
        am_metrics[am]['odr'] = safe_num(x.get('today', 1))
        am_metrics[am]['odr_chg'] = safe_num(x.get('n_change', 0))

for x in data.get('ns_am', []):
    am = x.get('am', '')
    if am in am_metrics:
        am_metrics[am]['ns_thieu'] = int(safe_num(x.get('so_thieu', 0)))
        am_metrics[am]['ns_can'] = int(safe_num(x.get('ptt_can', 0)))
        am_metrics[am]['ns_co'] = int(safe_num(x.get('ptt_co', 0)))

for x in data.get('bc_kd_lay', []):
    am_full = x.get('am', '')
    am_name = am_full.split('-')[-1].strip() if '-' in am_full else am_full
    if am_name in am_metrics:
        am_metrics[am_name]['gr'] = safe_num(x.get('gr', 0))
        am_metrics[am_name]['luyke'] = safe_num(x.get('luyke', 0))

for am, m in am_metrics.items():
    if m['gtc'] < 0.65:
        m['risk_score'] += 10
        m['issues'].append(f"GTC chạm đáy <b>{pct(m['gtc'])}</b> (Ca1: {pct(m['ca1'])}, Tồn: {pct(m['ton'])})")
    elif m['gtc'] < 0.75:
        m['risk_score'] += 5
        m['issues'].append(f"GTC cực thấp <b>{pct(m['gtc'])}</b> (Ca1: {pct(m['ca1'])}, Tồn: {pct(m['ton'])})")
    elif m['gtc'] < 0.80:
        m['risk_score'] += 2
        m['issues'].append(f"GTC thấp <b>{pct(m['gtc'])}</b> (Ca1: {pct(m['ca1'])})")
        
    if m['odr'] < 0.90:
        chg_str = f"giảm {abs(m['odr_chg'])*100:.1f}%" if m['odr_chg'] < 0 else f"tăng {m['odr_chg']*100:.1f}%"
        m['risk_score'] += 2
        m['issues'].append(f"ODR trễ <b>{pct(m['odr'])}</b> ({chg_str})")
        
    if m['ns_thieu'] >= 2: # Reduce threshold to 2 to show more HR issues
        m['risk_score'] += 3
        active_thieu = max(0, m['ns_can'] - m['ns_co'])
        m['issues'].append(f"Thiếu <b>{active_thieu} NS</b> (Cần {m['ns_can']}, Có {m['ns_co']}) | Cần tuyển: <b>{m['ns_thieu']} NS</b>")
        
    if m['gr'] < -5:
        m['risk_score'] += 2
        m['issues'].append(f"KD Tăng trưởng âm <b>{m['gr']:.1f}%</b> (Đạt {m['luyke']/1e6:.1f}M)")

sorted_ams = sorted(am_metrics.items(), key=lambda item: (-item[1]['risk_score'], item[1]['gtc']))

# 1. Điểm Nóng Hôm Nay HTML
def render_hs_list(sorted_list, is_am=False, limit=5):
    html = '<div style="display:flex; flex-direction:column; gap:8px;">'
    has_hotspots = False
    for name, m in sorted_list[:limit]:
        if m['risk_score'] > 0:
            has_hotspots = True
            issues_str = " | ".join(m['issues'])
            color = "#ef4444" if m['risk_score'] >= 5 else "#f59e0b"
            html += f'<div style="padding:10px 12px;background:var(--card2);border-radius:8px;font-size:13px;line-height:1.4;border-left:4px solid {color}">'
            if is_am:
                html += f'<div style="font-weight:700; color:var(--text); margin-bottom:4px">👤 AM {name}</div>'
            else:
                html += f'<div style="font-weight:700; color:var(--text); margin-bottom:4px">📍 {name} <span style="font-weight:500; color:var(--dim)">(AM: {m.get("am", "N/A")})</span></div>'
            html += f'<div style="color:var(--text); font-size:12px">⚠️ Vấn đề: {issues_str}</div>'
            html += f'</div>'
    if not has_hotspots:
        html += '<div style="color:var(--green); font-size:13px; font-weight:600; padding:10px">✅ Hoạt động ổn định</div>'
    html += '</div>'
    return html

am_hs_html = render_hs_list(sorted_ams, is_am=True, limit=3)
bc_hs_html = render_hs_list(sorted_bcs, is_am=False, limit=5)

# Build OPR Map by Province for Risk Forecast
prov_opr_map = {}
rep = data.get('opr_report', {})
rep_dates = rep.get('dates', [])
last_date = rep_dates[-1] if rep_dates else None
for p in rep.get('procs', []):
    p_name = p.get('name')
    for f in p.get('frames', []):
        if f.get('name') == 'Total' and last_date:
            prov_opr_map[p_name] = safe_num(f.get('vals', {}).get(last_date, {}).get('opr', 1.0))

# 2. Dự Báo Rủi Ro Rows
risk_forecast_list = sorted(data.get('canh_bao_vung', []), key=lambda x: safe_num(x.get('gap', 0)))[:5]
risk_rows = ''
for x in risk_forecast_list:
    bc_name = x.get("bc","")
    gap = safe_num(x.get('gap', 0))
    trend = '▼ Giảm' if gap < 0 else '▲ Cách'
    trend_cls = 'trend-down' if gap < 0 else 'trend-up'
    risk_level = '🔴 Nguy cấp' if gap < -0.05 else ('🔴 Cảnh báo' if gap < 0 else '🟡 Theo dõi')
    
    m = bc_metrics.get(bc_name, {})
    am_name = m.get('am', bc_to_am.get(bc_name.strip(), "-"))
    tinh = x.get('tinh', '-')
    
    # Other issues
    other_issues = []
    if m.get('odr', 1.0) < 0.9: other_issues.append(f"ODR {pct(m['odr'])}")
    opr_val = prov_opr_map.get(tinh, 1.0)
    if opr_val < 0.85: other_issues.append(f"OPR {pct(opr_val)}")
    if m.get('ns_thieu', 0) > 0: other_issues.append(f"Thiếu {m['ns_thieu']} NS")
    other_issues_str = ", ".join(other_issues) if other_issues else "Không"
    
    risk_rows += f'<tr><td class="text-left" style="font-weight:500">{am_name}</td><td class="text-left" style="font-weight:500">{bc_name}</td><td>{x.get("tinh","")}</td><td style="font-weight:700">{pct(x.get("gtc_7d",0))}</td><td>{pct(safe_num(x.get("target",0)))}</td><td class="{trend_cls}">{trend} ({abs(gap)*100:.1f}%)</td><td style="font-size:12px; color:var(--dim); font-weight:500">{other_issues_str}</td><td style="font-weight:600">{risk_level}</td></tr>'

# 3. Đề Xuất Hành Động
proposals = []
used_bcs = set()
used_ams = set()

worst_bc_tuple = sorted_bcs[0] if sorted_bcs and sorted_bcs[0][1]['risk_score'] > 0 else None

if worst_bc_tuple:
    bc_name, m = worst_bc_tuple
    am_name = m['am']
    used_bcs.add(bc_name)
    used_ams.add(am_name)
    
    actions = []
    if m['gtc'] < 0.75: actions.append(f"1. Giải quyết triệt để đơn tồn (hiện đạt {pct(m['ton'])}) để cứu vãn tỷ lệ GTC trong ca tiếp theo.")
    if m['odr'] < 0.90: actions.append(f"2. Giám sát gắt gao lộ trình của shipper để chống trễ hẹn ODR (hiện tại {pct(m['odr'])}).")
    if m['ns_thieu'] >= 2: actions.append(f"3. Bổ sung ngay {m['ns_thieu']} nhân sự part-time hoặc điều chuyển từ tuyến khác sang chi viện.")
    
    if len(actions) < 1: actions.append("1. Rà soát ngay quy trình phân tuyến tại Bưu cục để tối ưu hóa năng suất.")
    if len(actions) < 2: actions.append(f"{len(actions)+1}. Họp nhanh (stand-up meeting) đầu ca với 100% shipper để quán triệt chỉ tiêu.")
    if len(actions) < 3: actions.append("3. Phân công nhân sự theo dõi sát sao bảng tổng sắp đơn hàng, xử lý ngay đơn có nguy cơ rớt.")
    
    p1 = {
        'icon': '🔴', 'title': 'ƯU TIÊN 1: CHỮA CHÁY ĐIỂM NÓNG',
        'target': f"AM {am_name} ({bc_name})",
        'how': "<br>".join(actions),
        'when': 'Hoàn thành xử lý trong ngày, báo cáo kết quả trước 20:00.',
        'resource': 'Giám Đốc Vùng đôn đốc trực tiếp, BP Tuyển Dụng hỗ trợ NS gấp.'
    }
else:
    p1 = {'icon': '🟢', 'title': 'ƯU TIÊN 1: DUY TRÌ ỔN ĐỊNH', 'target': 'Toàn vùng', 'how': '1. Duy trì phong độ GTC > 80%.<br>2. Đảm bảo ODR > 95%.<br>3. Rà soát sức khỏe nhân sự.', 'when': 'Hàng ngày', 'resource': 'Đội ngũ hiện tại'}
proposals.append(p1)

if risk_forecast_list:
    top_risk = None
    for r in risk_forecast_list:
        bc = r.get('bc', '-')
        m = bc_metrics.get(bc, {})
        am = m.get('am', bc_to_am.get(bc.strip(), "-"))
        if bc not in used_bcs and am not in used_ams:
            top_risk = r
            break
            
    if not top_risk:
        top_risk = risk_forecast_list[0]
        
    tr_bc = top_risk.get('bc','-')
    tr_gap = safe_num(top_risk.get('gap',0))
    m = bc_metrics.get(tr_bc, {})
    tr_am = m.get('am', bc_to_am.get(tr_bc.strip(), "-"))
    
    used_bcs.add(tr_bc)
    used_ams.add(tr_am)
    
    p2 = {
        'icon': '📉', 'title': 'ƯU TIÊN 2: NGĂN CHẶN RỦI RO PHÁT SINH',
        'target': f"AM {tr_am} ({tr_bc})",
        'how': f"Cảnh báo: Bưu cục đang có xu hướng giảm sút <b>{abs(tr_gap)*100:.1f}%</b> so với mục tiêu tháng.<br>1. AM xuống trực tiếp Bưu cục để rà soát năng suất thực tế của từng shipper.<br>2. Phân tích dữ liệu 7 ngày qua để tìm ra tuyến đường giao hàng kém hiệu quả nhất.<br>3. Điều chỉnh lại định mức đơn hàng cho các tuyến bị quá tải.",
        'when': 'Báo cáo nguyên nhân và phương án khắc phục chi tiết trong 24h.',
        'resource': 'AM khu vực phối hợp cùng BP. Vận hành Vùng.'
    }
else:
    p2 = {'icon': '🔵', 'title': 'ƯU TIÊN 2: TỐI ƯU GIAO HÀNG', 'target': 'Toàn vùng', 'how': '1. Duy trì kỷ luật giao hàng đúng hẹn.<br>2. Kiểm soát tồn kho.<br>3. Giám sát lộ trình.', 'when': 'Hàng ngày', 'resource': 'Đội ngũ Shipper'}
proposals.append(p2)

# Find Systemic Issue for Priority 3
sys_odr_low = sum(1 for _, m in bc_metrics.items() if m['odr'] < 0.90)
sys_ns_thieu = sum(m['ns_thieu'] for _, m in bc_metrics.items())

if sys_ns_thieu >= 15:
    sorted_ns_am = sorted(data.get('ns_am', []), key=lambda a: safe_num(a.get('so_thieu', 0)), reverse=True)
    top_am_shortages = []
    for am_row in sorted_ns_am:
        am_name = am_row.get('am')
        if am_name in used_ams:
            continue
        thieu = int(safe_num(am_row.get('so_thieu', 0)))
        if thieu > 0:
            top_am_shortages.append(f"AM <b>{am_name}</b> (thiếu <b>{thieu}</b> NS)")
            used_ams.add(am_name)
        if len(top_am_shortages) == 2:
            break
            
    sorted_ns_bc = sorted(data.get('ns_bc', []), key=lambda a: safe_num(a.get('thieu', 0)), reverse=True)
    top_bc_shortages = []
    for bc_row in sorted_ns_bc:
        bc_name = bc_row.get('bc')
        am_name = bc_row.get('am')
        if bc_name in used_bcs or am_name in used_ams:
            continue
        thieu = int(safe_num(bc_row.get('thieu', 0)))
        if thieu > 0:
            short_bc = bc_name.split('-')[0]
            top_bc_shortages.append(f"<b>{short_bc}</b> (AM <b>{am_name}</b>, thiếu <b>{thieu}</b> NS)")
            used_bcs.add(bc_name)
            used_ams.add(am_name)
        if len(top_bc_shortages) == 2:
            break
            
    am_str = " và ".join(top_am_shortages)
    bc_str = " và ".join(top_bc_shortages)
    
    how_text = (
        f"1. <b>Tập trung tuyển dụng bổ sung cho toàn vùng TNG:</b> Đẩy mạnh chiến dịch qua các kênh Local và chạy quảng cáo khu vực, trong đó ưu tiên hàng đầu phân bổ cho {am_str} đang thiếu hụt lớn nhất.<br>"
        f"2. <b>Chi viện nhân sự khẩn cấp:</b> BP. Vận hành lên phương án điều chuyển tạm thời shipper từ các bưu cục ổn định sang chi viện cho {bc_str}.<br>"
        f"3. <b>Liên hệ ứng viên cũ:</b> BP Tuyển dụng vùng rà soát danh sách ứng viên cũ tại địa bàn để phỏng vấn gấp và Onboard trong vòng 3 ngày."
    )

    p3 = {
        'icon': '🟡', 'title': 'ƯU TIÊN 3: GIẢI QUYẾT BÀI TOÁN NHÂN SỰ VÙNG',
        'target': f"Toàn vùng TNG (Đang thiếu tổng cộng {sys_ns_thieu} NS)",
        'how': how_text,
        'when': 'Hoàn tất phỏng vấn và Onboarding trong 3 ngày tới.',
        'resource': 'BP. Tuyển dụng Vùng phối hợp cùng GĐV.'
    }
elif sys_odr_low >= 5:
    p3 = {
        'icon': '⏱️', 'title': 'ƯU TIÊN 3: CẢI THIỆN ODR TOÀN VÙNG',
        'target': f"{sys_odr_low} Bưu cục có ODR < 90%",
        'how': "1. Chấn chỉnh kỷ luật lấy/giao hàng đúng khung giờ tại các bưu cục vi phạm.<br>2. Rà soát lại hệ thống cảnh báo đơn sắp trễ giờ (Near-miss) để xử lý ngay.<br>3. Tổ chức training nhanh lại quy trình giao hàng chuẩn cho nhóm shipper mới.",
        'when': 'Áp dụng ngay cho các ca tiếp theo.',
        'resource': 'Quản lý Bưu cục và Đội ngũ Shipper.'
    }
else:
    p3 = {
        'icon': '🚀', 'title': 'ƯU TIÊN 3: CẢI THIỆN OPR',
        'target': "Các Tỉnh/BC trọng điểm",
        'how': "1. Yêu cầu các BC có lượng đơn LTC lớn thực hiện quét lấy hàng ngay khi tiếp nhận.<br>2. Đội ngũ Điều phối phải theo dõi sát sao lộ trình lấy hàng của xe tải.<br>3. Tuyệt đối không để rớt đơn đã có tín hiệu lấy trên hệ thống.",
        'when': 'Trong ca vận hành tiếp theo.',
        'resource': 'Đội ngũ Điều phối (Fleet).'
    }
proposals.append(p3)

action_proposals_html = '<div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap:15px; margin-top:5px;">'
for p in proposals:
    color = "#3b82f6"
    if "1" in p['title']: color = "#ef4444"
    elif "2" in p['title']: color = "#f59e0b"
    if "🟢" in p['icon']: color = "#22c55e"
    if "🟡" in p['icon']: color = "#eab308"
    
    action_proposals_html += f'''
    <div style="background:#fff; border:1px solid #e2e8f0; border-radius:12px; padding:16px; position:relative; overflow:hidden; box-shadow:0 4px 6px -1px rgba(0,0,0,0.1); display:flex; flex-direction:column; justify-content:space-between;">
        <div style="position:absolute; top:0; left:0; width:4px; height:100%; background:{color}"></div>
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:12px;">
            <span style="font-size:24px;">{p['icon']}</span>
            <span style="font-weight:800; font-size:14px; color:{color}; letter-spacing:0.5px;">{p['title']}</span>
        </div>
        <div style="display:flex; flex-direction:column; gap:10px; flex:1;">
            <div style="font-size:13px;"><span style="font-weight:700; color:var(--text);">👤 Trọng tâm:</span> <span style="color:var(--dim); font-weight:600;">{p['target']}</span></div>
            <div style="font-size:13px;"><span style="font-weight:700; color:var(--text);">🛠️ Triển khai:</span> <span style="color:var(--dim); line-height:1.6;">{p['how']}</span></div>
            <div style="font-size:13px;"><span style="font-weight:700; color:var(--text);">⏱️ Thời gian:</span> <span style="color:var(--dim);">{p['when']}</span></div>
            <div style="font-size:13px;"><span style="font-weight:700; color:var(--text);">🔋 Nguồn lực:</span> <span style="color:var(--dim);">{p['resource']}</span></div>
        </div>
    </div>'''
action_proposals_html += '</div>'


# Volume Share by Province (Internal ring)
prov_vol = {}
def normalize_prov(p):
    p = p.replace('Đăk Lắk', 'Đắk Lắk').replace('Đăk Nông', 'Đắk Nông')
    return p

for x in data.get('gtc_bc', []):
    bc_name = x.get('bc','')
    if '-' in bc_name:
        prov = normalize_prov(bc_name.split('-')[-1].strip())
        prov_vol[prov] = prov_vol.get(prov, 0) + safe_num(x.get('total_vol', 0))

sorted_prov = sorted(prov_vol.items(), key=lambda x: x[1], reverse=True)
prov_labels = json.dumps([x[0] for x in sorted_prov], ensure_ascii=False)
prov_data = json.dumps([x[1] for x in sorted_prov])

# Map AM to Province for color coding
am_to_prov = {}
for x in data.get('gtc_bc', []):
    am = x.get('am')
    if am and '-' in x.get('bc',''):
        am_to_prov[am] = normalize_prov(x['bc'].split('-')[-1].strip())

prov_color_map = {
    'Đắk Lắk': '#3b82f6',
    'Bình Định': '#10b981',
    'Gia Lai': '#f59e0b',
    'Phú Yên': '#ef4444',
    'Đắk Nông': '#8b5cf6',
    'Kon Tum': '#06b6d4'
}

# Filter out Province totals and Grand Total from AM chart
am_only_list = [x for x in data['gtc_am'] if x['am'] not in prov_vol and x['am'] not in ['Grand Total', 'Vùng TNG']]

# FINAL SORTING: By Province (desc volume) then by AM Volume (desc)
prov_order = {p[0]: i for i, p in enumerate(sorted_prov)}
sorted_vol = sorted(am_only_list, 
                   key=lambda x: (prov_order.get(am_to_prov.get(x['am'], ''), 99), -safe_num(x.get('total_vol', 0))))

vol_labels = json.dumps([x['am'] for x in sorted_vol], ensure_ascii=False)
vol_data = json.dumps([safe_num(x.get('total_vol',0)) for x in sorted_vol])

def lighten_color(hex_color, factor):
    hex_color = hex_color.lstrip('#')
    rgb = [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]
    # Mix with white (255, 255, 255)
    new_rgb = [int(c + (255 - c) * factor) for c in rgb]
    return '#{:02x}{:02x}{:02x}'.format(*new_rgb)

am_colors = []
prov_counts = {}
for x in sorted_vol:
    p = am_to_prov.get(x['am'], 'Other')
    rank = prov_counts.get(p, 0)
    base_color = prov_color_map.get(p, '#cbd5e1')
    
    # Increase factor per rank to lighten
    factor = min(rank * 0.25, 0.75) 
    am_colors.append(lighten_color(base_color, factor))
    
    prov_counts[p] = rank + 1

vol_colors_js = json.dumps(am_colors)
prov_colors_js = json.dumps([prov_color_map.get(x[0], '#cbd5e1') for x in sorted_prov])

# Business Trend Data (7 Days)
kd_trend_dates = [datetime.strptime(d, '%Y-%m-%d').strftime('%d/%m') for d in data.get('opr_report', {}).get('dates', [])]
kd_trend_data = [safe_num(v) for v in data.get('total_lay', {}).get('dt_days', [])]
kd_trend_dates_js = json.dumps(kd_trend_dates[-7:])
kd_trend_data_js = json.dumps(kd_trend_data[-7:])

# KD bar chart - lũy kế vs cùng kỳ
kd_am_labels = json.dumps([x['am'].split('-')[-1].strip() if '-' in x['am'] else x['am'] for x in filtered_kd], ensure_ascii=False)
kd_luyke = json.dumps([round(safe_num(x.get('luyke',0))/1e6,1) for x in filtered_kd])
kd_cungky = json.dumps([round(safe_num(x.get('cungky',0))/1e6,1) for x in filtered_kd])


# OPR MATRIX
rep_tinh = data.get('opr_tinh_report', {})
rep_am = data.get('opr_report', {})
dates = rep_tinh.get('dates', [])
if not dates and rep_am:
    dates = rep_am.get('dates', [])

# Calculate Vùng TNG for OPR Tỉnh Matrix
vung_tinhs = [p for p in rep_tinh.get('procs', []) if p['name'] not in ['Grand Total', 'Vùng TNG']]
if vung_tinhs:
    vung_total = {'name': 'Vùng TNG', 'frames': []}
    f_vals = {}
    for d in dates:
        # Only sum the 'Total' frame from each province
        vol = sum(safe_num(p_f['vals'].get(d, {}).get('vol_ltc', 0)) 
                  for p in vung_tinhs 
                  for p_f in p['frames'] if p_f['name'] == 'Total')
        opr_vol = sum(safe_num(p_f['vals'].get(d, {}).get('opr', 0)) * safe_num(p_f['vals'].get(d, {}).get('vol_ltc', 0))
                      for p in vung_tinhs 
                      for p_f in p['frames'] if p_f['name'] == 'Total')
        f_vals[d] = {'vol_ltc': vol, 'opr': opr_vol / max(vol, 1)}
    
    vung_total['frames'].append({'name': 'Total', 'vals': f_vals})
    rep_tinh['procs'] = vung_tinhs + [vung_total]

# Calculate Vùng TNG for OPR AM Matrix just in case
vung_procs_am = [p for p in rep_am.get('procs', []) if p['name'] not in ['Grand Total', 'Vùng TNG']]
if vung_procs_am:
    vung_total_am = {'name': 'Vùng TNG', 'frames': []}
    f_vals = {}
    for d in dates:
        vol = sum(safe_num(p_f['vals'].get(d, {}).get('vol_ltc', 0)) 
                  for p in vung_procs_am 
                  for p_f in p['frames'] if p_f['name'] == 'Total')
        opr_vol = sum(safe_num(p_f['vals'].get(d, {}).get('opr', 0)) * safe_num(p_f['vals'].get(d, {}).get('vol_ltc', 0))
                      for p in vung_procs_am 
                      for p_f in p['frames'] if p_f['name'] == 'Total')
        f_vals[d] = {'vol_ltc': vol, 'opr': opr_vol / max(vol, 1)}
    
    vung_total_am['frames'].append({'name': 'Total', 'vals': f_vals})
    rep_am['procs'] = vung_procs_am + [vung_total_am]

opr_trend_data = {}
for p in rep_tinh.get('procs', []):
    p_name = p['name']
    if p_name == 'Grand Total': continue
    opr_trend_data[p_name] = []
    total_frame = next((f for f in p['frames'] if f['name'] == 'Total'), None)
    for d in dates:
        if total_frame:
            val = safe_num(total_frame['vals'].get(d, {}).get('opr', 0)) * 100
            opr_trend_data[p_name].append(round(val, 1))
        else:
            opr_trend_data[p_name].append(0)

opr_trend_labels_js = json.dumps([datetime.strptime(d, '%Y-%m-%d').strftime('%d/%m') for d in dates])

# Helper to build OPR table rows and headers
def build_opr_table(rep_data, name_label):
    tbl_dates = rep_data.get('dates', [])
    if not tbl_dates:
        tbl_dates = dates
    
    header_1 = f'<tr><th rowspan="2" class="sticky-col-1" style="z-index:20; border:none !important; top:0">{name_label}</th><th rowspan="2" class="sticky-col-2" style="z-index:20; border:none !important; top:0">Khung giờ tạo đơn</th>'
    header_2 = '<tr>'
    for d in tbl_dates:
        header_1 += f'<th colspan="2" style="text-align:center; border:none !important; top:0">{d}</th>'
        header_2 += '<th style="position:sticky; top:31px; z-index:20; border:none !important">Vol LTC</th><th style="position:sticky; top:31px; z-index:20; border:none !important">%OPR</th>'
    header_1 += '</tr>'
    header_2 += '</tr>'
    
    matrix_rows = ''
    for p in rep_data.get('procs', []):
        p_name = p['name']
        is_grand = p_name == 'Vùng TNG'
        n_frames = len(p['frames'])
        for i, f in enumerate(p['frames']):
            is_total = 'Total' in f['name'] or is_grand
            row_bg = 'background:#e0f2fe;' if is_total and not is_grand else ('background:#fee2e2;' if is_grand else '')
            row_fw = 'font-weight:bold;' if is_total else ''
            row = f'<tr style="{row_bg} {row_fw}">'
            
            if i == 0:
                if is_grand:
                    row += f'<td class="sticky-col-1 text-left" colspan="2" style="color:#ef4444; background:inherit">{p_name}</td>'
                else:
                    row += f'<td class="sticky-col-1 text-left" rowspan="{n_frames}" style="vertical-align:middle; background:inherit">{p_name}</td>'
            
            if not is_grand:
                if 'Total' in f['name']:
                    row += f'<td class="sticky-col-2 text-left" style="background:inherit">{p_name} Total</td>'
                else:
                    row += f'<td class="sticky-col-2 text-left" style="background:inherit">{f["name"]}</td>'
            
            for d in tbl_dates:
                v = f['vals'].get(d, {'vol_ltc': 0, 'opr': 0})
                c = "color:#ef4444" if v['opr'] < 0.95 and v['vol_ltc'] > 0 else ("color:#22c55e" if v['vol_ltc'] > 0 else "")
                if is_grand: c = "color:#ef4444"
                row += f'<td style="text-align:center">{num(v["vol_ltc"])}</td>'
                row += f'<td style="{c}; text-align:center">{pct(v["opr"]) if v["vol_ltc"] > 0 else "-"}</td>'
            row += '</tr>'
            matrix_rows += row
            
    return header_1, header_2, matrix_rows

# Build tables
opr_tinh_header_1, opr_tinh_header_2, opr_tinh_matrix_rows = build_opr_table(rep_tinh, 'Tỉnh')
opr_am_header_1, opr_am_header_2, opr_am_matrix_rows = build_opr_table(rep_am, 'Quản lý')

opr_total_val = safe_num(data.get('opr_total', 0))
now = datetime.now().strftime('%d/%m/%Y')
delta_vol = render_delta(get_delta('vol', vol_giao))
delta_gtc_v = render_delta(get_delta('gtc_vung', avg_gtc))
delta_gtc_t = render_delta(get_delta('gtc_tts', avg_gtc_tts))
delta_ontime = render_delta(get_delta('ontime', avg_ontime))
delta_opr = render_delta(get_delta('opr', opr_total_val))
# Revenue Delta compared to Cùng kỳ (Last Month)
diff_rev = safe_num(total_rev_lay) - safe_num(total_cungky)
if total_cungky > 0:
    color = "#10b981" if diff_rev > 0 else "#ef4444"
    icon = "▲" if diff_rev > 0 else "▼"
    rev_str = f"{int(abs(diff_rev)):,}".replace(",", ".")
    delta_rev = f'<div class="kpi-delta" style="color:{color}">{icon} {rev_str}</div>'
else:
    delta_rev = ""

delta_ns = render_delta(get_delta('ns_thieu', safe_num(ns_total.get('so_thieu',0))), invert=True)
delta_warn = render_delta(get_delta('n_warn', n_warn), invert=True)

# Format display date for header (e.g., 10/05/2026)
display_date = datetime.strptime(today_str, '%Y-%m-%d').strftime('%d/%m/%Y')

# Dynamic Trend Data from History
hist_file = 'gtc_prov_history.json'
try:
    with open(hist_file, 'r', encoding='utf-8') as f:
        full_hist = json.load(f)
except:
    full_hist = {}

# Sort dates and take last 8
sorted_dates = sorted(full_hist.keys())[-8:]
trend_labels = [datetime.strptime(d, '%Y-%m-%d').strftime('%d/%m') for d in sorted_dates]

provinces = ['Bình Định', 'Đắk Lắk', 'Gia Lai', 'Phú Yên', 'Vùng TNG']
trend_data = {p: [] for p in provinces}

for d in sorted_dates:
    day_data = full_hist.get(d, {})
    for p in provinces:
        trend_data[p].append(day_data.get(p, 0))

trend_rows = ''
for province in provinces:
    is_total = province == 'Vùng TNG'
    style = "font-weight:700; background:#f0f9ff" if is_total else ""
    trend_rows += f"<tr style='{style}'><td>{province}</td>"
    for v in trend_data[province]:
        trend_rows += f"<td>{v}%</td>"
    trend_rows += "</tr>"

    # Map of province keys to Vietnamese province names
    prov_map = {
        'gialai': 'Gia Lai',
        'daklak': 'Đắk Lắk',
        'binhdinh': 'Bình Định',
        'phuyen': 'Phú Yên'
    }

    am_tinh = {}
    for x in data.get('ns_bc', []):
        am = x.get('am')
        tinh = x.get('tinh')
        if am and tinh:
            am_tinh.setdefault(tinh, set()).add(am)

    # Number of AMs per province
    gialai_am = f"{len(am_tinh.get('Gia Lai', []))} AM"
    daklak_am = f"{len(am_tinh.get('Đắk Lắk', []))} AM"
    binhdinh_am = f"{len(am_tinh.get('Bình Định', []))} AM"
    phuyen_am = f"{len(am_tinh.get('Phú Yên', []))} AM"

    # Fallback to default counts if list is empty
    if len(am_tinh.get('Gia Lai', [])) == 0: gialai_am = "4 AM"
    if len(am_tinh.get('Đắk Lắk', [])) == 0: daklak_am = "6 AM"
    if len(am_tinh.get('Bình Định', [])) == 0: binhdinh_am = "3 AM"
    if len(am_tinh.get('Phú Yên', [])) == 0: phuyen_am = "2 AM"

    # Calculate average weekly GTC for each province
    def get_weekly_gtc_avg(prov_name):
        if not sorted_dates:
            return 0.0
        vals = []
        for d in sorted_dates:
            val = full_hist.get(d, {}).get(prov_name)
            if val is not None:
                vals.append(val)
        if not vals:
            return 0.0
        return sum(vals) / len(vals)

    gialai_gtc_avg = f"{get_weekly_gtc_avg('Gia Lai'):.1f}%"
    daklak_gtc_avg = f"{get_weekly_gtc_avg('Đắk Lắk'):.1f}%"
    binhdinh_gtc_avg = f"{get_weekly_gtc_avg('Bình Định'):.1f}%"
    phuyen_gtc_avg = f"{get_weekly_gtc_avg('Phú Yên'):.1f}%"

    # Fallback to defaults in case of 0.0%
    if gialai_gtc_avg == "0.0%": gialai_gtc_avg = "75.8%"
    if daklak_gtc_avg == "0.0%": daklak_gtc_avg = "63.7%"
    if binhdinh_gtc_avg == "0.0%": binhdinh_gtc_avg = "78.8%"
    if phuyen_gtc_avg == "0.0%": phuyen_gtc_avg = "78.9%"

    # Calculate staffing (active personnel 'co')
    gialai_ns = int(sum(safe_num(x.get('co', 0)) for x in data.get('ns_bc', []) if x.get('tinh') == 'Gia Lai'))
    daklak_ns = int(sum(safe_num(x.get('co', 0)) for x in data.get('ns_bc', []) if x.get('tinh') == 'Đắk Lắk'))
    binhdinh_ns = int(sum(safe_num(x.get('co', 0)) for x in data.get('ns_bc', []) if x.get('tinh') == 'Bình Định'))
    phuyen_ns = int(sum(safe_num(x.get('co', 0)) for x in data.get('ns_bc', []) if x.get('tinh') == 'Phú Yên'))

    # Fallbacks if sum is 0
    if gialai_ns == 0: gialai_ns = 168
    if daklak_ns == 0: daklak_ns = 240
    if binhdinh_ns == 0: binhdinh_ns = 173
    if phuyen_ns == 0: phuyen_ns = 112

    # Calculate total volume of the 4 provinces
    total_region_vol = sum(safe_num(x.get('total_vol', 0)) for x in data.get('gtc_tinh', []) if x.get('tinh') in ['Gia Lai', 'Đắk Lắk', 'Bình Định', 'Phú Yên'])

    def get_vol_pct(prov_name):
        if total_region_vol == 0:
            return 0.0
        prov_vol = sum(safe_num(x.get('total_vol', 0)) for x in data.get('gtc_tinh', []) if x.get('tinh') == prov_name)
        return (prov_vol / total_region_vol) * 100.0

    gialai_vol_pct = f"{get_vol_pct('Gia Lai'):.1f}%"
    daklak_vol_pct = f"{get_vol_pct('Đắk Lắk'):.1f}%"
    binhdinh_vol_pct = f"{get_vol_pct('Bình Định'):.1f}%"
    phuyen_vol_pct = f"{get_vol_pct('Phú Yên'):.1f}%"

    # Fallbacks in case total volume is 0 or calculation returns 0%
    if gialai_vol_pct == "0.0%": gialai_vol_pct = "22.5%"
    if daklak_vol_pct == "0.0%": daklak_vol_pct = "36.1%"
    if binhdinh_vol_pct == "0.0%": binhdinh_vol_pct = "26.5%"
    if phuyen_vol_pct == "0.0%": phuyen_vol_pct = "14.9%"

    html = f'''<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TNG - Dashboard Vận Hành</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0"></script>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<script src="https://unpkg.com/lucide@latest"></script>
<script src="bot_url.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
:root{{--bg:linear-gradient(135deg, #7dd3fc 0%, #0284c7 100%);--card:#ffffff;--card2:#f1f5f9;--border:#cbd5e1;--text:#0f172a;--dim:#475569;--accent:#0284c7;--green:#10b981;--yellow:#f59e0b;--red:#ef4444;--purple:#8b5cf6;--cyan:#0ea5e9}}
body{{font-family:'Plus Jakarta Sans',sans-serif;background:var(--bg);background-attachment:fixed;color:var(--text);min-height:100vh; -webkit-font-smoothing: antialiased;}}
.header{{background:linear-gradient(135deg,#0284c7 0%,#0369a1 100%);padding:15px 25px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border);box-shadow:0 4px 6px -1px rgba(0,0,0,0.1);flex-wrap:wrap;gap:15px; position: sticky; top: 0; z-index: 1000;}}
.header h1{{font-size:23px;font-weight:800;color:#ffffff}}
.header .date{{color:#ffffff;font-size:13px;font-weight:500;opacity:0.9}}
.btn-quick {{ padding:6px 14px; color:#fff; border-radius:8px; text-decoration:none; font-size:12px; font-weight:600; white-space:nowrap; transition:all 0.2s ease; box-shadow: 0 2px 4px rgba(0,0,0,0.1); display: inline-flex; align-items: center; gap: 4px; }}
.btn-quick:hover {{ transform: translateY(-2px); box-shadow: 0 4px 6px rgba(0,0,0,0.15); filter: brightness(1.1); }}
.kpi-grid{{display:grid;grid-template-columns:repeat(auto-fit, minmax(145px, 1fr));gap:10px;padding:16px 20px}}
.kpi-card{{background:linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);border:1px solid #cbd5e1;border-radius:12px;padding:12px 8px;text-align:center;position:relative;overflow:hidden;box-shadow:0 4px 6px -1px rgba(0,0,0,0.1), inset 0 1px 0 #fff;display:flex;flex-direction:column;justify-content:center;min-height:90px; transition: all 0.2s ease; cursor: pointer;}}
.kpi-card:hover {{ transform: translateY(-3px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05); border-color: #0ea5e9; }}
.kpi-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:4px;border-radius:12px 12px 0 0}}
.kpi-card:nth-child(1)::before{{background:var(--accent)}}
.kpi-card:nth-child(2)::before{{background:var(--cyan)}}
.kpi-card:nth-child(3)::before{{background:var(--green)}}
.kpi-card:nth-child(4)::before{{background:var(--cyan)}}
.kpi-card:nth-child(5)::before{{background:var(--purple)}}
.kpi-card:nth-child(6)::before{{background:var(--yellow)}}
.kpi-card:nth-child(7)::before{{background:var(--red)}}
.kpi-card:nth-child(8)::before{{background:var(--red)}}
.kpi-label{{font-size:12px;font-weight:700;color:var(--dim);letter-spacing:0.3px;margin-bottom:6px;white-space:nowrap;overflow:visible}}
.kpi-value{{font-size:19px;font-weight:800;white-space:nowrap;margin-bottom:2px}}
.kpi-delta{{font-size:12px;font-weight:700;display:flex;align-items:center;justify-content:center;gap:2px}}
.tbl-opr td{{border:1px solid #cbd5e1}}
.tbl-opr .sticky-col-1{{position:sticky; left:0; z-index:10; background:inherit; width:120px; min-width:120px}}
.tbl-opr .sticky-col-2{{position:sticky; left:120px; z-index:10; background:inherit; width:150px; min-width:150px}}
.tbl-opr th.sticky-col-1, .tbl-opr th.sticky-col-2{{background:#0ea5e9 !important; color:#ffffff !important; border-bottom:1px solid #0284c7 !important; border-right:1px solid rgba(255,255,255,0.1) !important}}
.tbl-opr th{{border:none !important}}
.tbl-opr{{border-collapse:collapse; border:none}}
.tbl-opr tr:hover .sticky-col-1, .tbl-opr tr:hover .sticky-col-2{{background:var(--card2)}}
.kpi-card:nth-child(1) .kpi-value{{color:var(--accent)}}
.kpi-card:nth-child(2) .kpi-value{{color:var(--cyan)}}
.kpi-card:nth-child(3) .kpi-value{{color:var(--green)}}
.kpi-card:nth-child(4) .kpi-value{{color:var(--cyan)}}
.kpi-card:nth-child(5) .kpi-value{{color:var(--purple)}}
.kpi-card:nth-child(6) .kpi-value{{color:var(--yellow)}}
.kpi-card:nth-child(7) .kpi-value{{color:var(--red)}}
.kpi-card:nth-child(8) .kpi-value{{color:var(--red)}}
.tabs{{display:flex;gap:8px;padding:8px 16px;background:var(--card);border-bottom:1px solid var(--border);overflow-x:auto; position: sticky; top: 62px; z-index: 999; align-items: center; width: 100%;}}
.tab{{padding:6px 12px;border-radius:8px;cursor:pointer;font-size:14.5px;font-weight:700;color:var(--dim);transition:all .2s;white-space:nowrap;border:1px solid transparent; position: relative; display: flex; align-items: center; gap: 6px; background: transparent; box-shadow: none;}}
.tab svg{{width:16px;height:16px}}
.tab:nth-child(1) svg{{color:#3b82f6}}
.tab:nth-child(2) svg{{color:#06b6d4}}
.tab:nth-child(3) svg{{color:#10b981}}
.tab:nth-child(4) svg{{color:#f59e0b}}
.tab:nth-child(5) svg{{color:#8b5cf6}}
.tab:nth-child(6) svg{{color:#d97706}}
.tab:nth-child(7) svg{{color:#db2777}}
.tab:nth-child(8) svg{{color:#6366f1}}
.tab:nth-child(9) svg{{color:#ef4444}}
.tab:nth-child(10) svg{{color:#8b5cf6}}
.tab:hover{{background:var(--card2); color:var(--accent);}}
.tab:not(:last-child)::after{{content:''; position:absolute; right:-5px; height:16px; width:2px; background:#cbd5e1; box-shadow:1px 0 0 #fff;}}
.tab.active{{background:var(--accent);color:#fff;border-color:#0369a1; box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);}}
.tab.active svg{{color:#fff !important}}
.tab.active::after{{display:none}}
.content{{padding:20px 24px}}
.panel{{display:none}}
.panel.active{{display:block}}
.map-province {{ transition: all 0.3s ease; cursor: pointer; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.15)); }}
.map-province:hover {{ filter: brightness(1.1) drop-shadow(0 4px 12px rgba(2, 132, 199, 0.4)); transform: translateY(-2px); }}
.map-province.active-province {{ stroke: #ffffff; stroke-width: 4; filter: brightness(1.2) drop-shadow(0 4px 16px rgba(2, 132, 199, 0.6)); }}
.map-container {{
  position: relative;
  width: 100%;
  height: 450px;
  border-radius: 14px;
  border: 1.5px solid #cbd5e1;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0,0,0,0.10), inset 0 1px 0 rgba(255,255,255,0.9);
  background: #ffffff;
}}
/* === Province Glow Pins (center of each province) === */
.map-pin {{
  position: absolute;
  width: 44px;
  height: 44px;
  transform: translate(-50%, -50%);
  cursor: pointer;
  z-index: 10;
}}
.pin-dot {{
  width: 18px;
  height: 18px;
  background: #0ea5e9;
  border: 3px solid #fff;
  border-radius: 50%;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  box-shadow: 0 0 14px rgba(14, 165, 233, 0.9), 0 2px 6px rgba(0,0,0,0.25);
  transition: all 0.3s ease;
}}
.map-pin[data-id="daklak"] .pin-dot {{
  background: #ea580c;
  box-shadow: 0 0 14px rgba(234, 88, 12, 0.9), 0 2px 6px rgba(0,0,0,0.25);
}}
.map-pin[data-id="binhdinh"] .pin-dot {{
  background: #10b981;
  box-shadow: 0 0 14px rgba(16, 185, 129, 0.9), 0 2px 6px rgba(0,0,0,0.25);
}}
.map-pin[data-id="phuyen"] .pin-dot {{
  background: #c026d3;
  box-shadow: 0 0 14px rgba(192, 38, 211, 0.9), 0 2px 6px rgba(0,0,0,0.25);
}}
.pin-pulse {{
  width: 44px;
  height: 44px;
  background: rgba(14, 165, 233, 0.3);
  border-radius: 50%;
  position: absolute;
  top: 0;
  left: 0;
  animation: map-pulse 2.2s infinite ease-out;
  pointer-events: none;
}}
.pin-pulse2 {{
  width: 44px;
  height: 44px;
  background: rgba(14, 165, 233, 0.18);
  border-radius: 50%;
  position: absolute;
  top: 0;
  left: 0;
  animation: map-pulse 2.2s infinite ease-out 0.7s;
  pointer-events: none;
}}
.map-pin[data-id="daklak"] .pin-pulse,
.map-pin[data-id="daklak"] .pin-pulse2 {{
  background: rgba(234, 88, 12, 0.28);
}}
.map-pin[data-id="binhdinh"] .pin-pulse,
.map-pin[data-id="binhdinh"] .pin-pulse2 {{
  background: rgba(16, 185, 129, 0.28);
}}
.map-pin[data-id="phuyen"] .pin-pulse,
.map-pin[data-id="phuyen"] .pin-pulse2 {{
  background: rgba(192, 38, 211, 0.28);
}}
@keyframes map-pulse {{
  0% {{
    transform: scale(0.4);
    opacity: 1;
  }}
  100% {{
    transform: scale(2.8);
    opacity: 0;
  }}
}}
@keyframes label-blink {{
  0%, 100% {{
    opacity: 0.95;
    box-shadow: 0 3px 10px rgba(0,0,0,0.2);
  }}
  50% {{
    opacity: 0.55;
    box-shadow: 0 1px 5px rgba(0,0,0,0.1);
  }}
}}
.pin-label {{
  position: absolute;
  top: -32px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(2, 132, 199, 0.9);
  backdrop-filter: blur(6px);
  color: #fff;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 10px;
  font-weight: 800;
  white-space: nowrap;
  border: 1.5px solid rgba(255,255,255,0.4);
  opacity: 1;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 3px 10px rgba(0,0,0,0.2);
  letter-spacing: 0.6px;
  pointer-events: auto;
  animation: label-blink 2s infinite ease-in-out;
}}
.map-pin[data-id="daklak"] .pin-label {{
  background: rgba(234, 88, 12, 0.9);
}}
.map-pin[data-id="binhdinh"] .pin-label {{
  background: rgba(5, 150, 105, 0.9);
}}
.map-pin[data-id="phuyen"] .pin-label {{
  background: rgba(192, 38, 211, 0.9);
}}
.map-pin:hover .pin-label, .map-pin.active-pin .pin-label {{
  animation: none;
  background: #0284c7;
  opacity: 1;
  transform: translateX(-50%) translateY(-2px) scale(1.05);
  box-shadow: 0 8px 20px rgba(2, 132, 199, 0.4);
}}
.map-pin[data-id="daklak"]:hover .pin-label, .map-pin[data-id="daklak"].active-pin .pin-label {{
  animation: none;
  background: #ea580c;
  box-shadow: 0 8px 20px rgba(234, 88, 12, 0.4);
}}
.map-pin[data-id="binhdinh"]:hover .pin-label, .map-pin[data-id="binhdinh"].active-pin .pin-label {{
  animation: none;
  background: #047857;
  box-shadow: 0 8px 20px rgba(16, 185, 129, 0.4);
}}
.map-pin[data-id="phuyen"]:hover .pin-label, .map-pin[data-id="phuyen"].active-pin .pin-label {{
  animation: none;
  background: #c026d3;
  box-shadow: 0 8px 20px rgba(192, 38, 211, 0.4);
}}
.map-pin.active-pin .pin-dot {{
  transform: translate(-50%, -50%) scale(1.4);
  border-color: #fff;
  box-shadow: 0 0 22px rgba(14, 165, 233, 1), 0 4px 8px rgba(0,0,0,0.3);
}}
.map-pin[data-id="daklak"].active-pin .pin-dot {{
  box-shadow: 0 0 22px rgba(234, 88, 12, 1), 0 4px 8px rgba(0,0,0,0.3);
}}
.map-pin[data-id="binhdinh"].active-pin .pin-dot {{
  box-shadow: 0 0 22px rgba(16, 185, 129, 1), 0 4px 8px rgba(0,0,0,0.3);
}}
.map-pin[data-id="phuyen"].active-pin .pin-dot {{
  box-shadow: 0 0 22px rgba(192, 38, 211, 1), 0 4px 8px rgba(0,0,0,0.3);
}}
/* === City Star Markers (red 3D) === */
.city-star {{
  position: absolute;
  transform: translate(-50%, -50%);
  z-index: 20;
  pointer-events: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}}
.city-star-icon {{
  font-size: 14px;
  line-height: 1;
  filter: drop-shadow(0 2px 2px rgba(0,0,0,0.5)) drop-shadow(0 4px 6px rgba(200,0,0,0.5));
  animation: star-float 3s ease-in-out infinite;
}}
.city-star-name {{
  font-size: 9px;
  font-weight: 700;
  color: #7f1d1d;
  background: rgba(255,255,255,0.88);
  padding: 1px 5px;
  border-radius: 3px;
  white-space: nowrap;
  box-shadow: 0 1px 4px rgba(0,0,0,0.2);
  border: 1px solid rgba(239,68,68,0.3);
  letter-spacing: 0.3px;
}}
@keyframes star-float {{
  0%, 100% {{ transform: translateY(0px); }}
  50% {{ transform: translateY(-2px); }}
}}

.section-title{{font-size:21px;font-weight:700;margin-bottom:14px;display:flex;align-items:center;gap:8px}}
.section-title span{{width:4px;height:24px;border-radius:2px;background:var(--accent)}}
.grid-2{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.card{{background:linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);border:1px solid #cbd5e1;border-radius:12px;padding:16px;margin-bottom:16px; box-shadow:0 4px 6px -1px rgba(0,0,0,0.1), inset 0 1px 0 #fff;}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
/* Common header base is now handled by the updated th style below */
thead tr:nth-child(1) th {{ top: 0; z-index: 11; }}
thead tr:nth-child(2) th {{ top: 31px; z-index: 10; }}
td{{padding:7px 10px;border-bottom:1px solid #1e293b30;text-align:center}}
.text-left{{text-align:left !important}}
tr:hover{{background:var(--card2)}}
.status-good{{color:var(--green);font-weight:700}}
.status-warn{{color:var(--yellow);font-weight:700}}
.status-danger{{color:var(--red);font-weight:700}}
.trend-up{{color:var(--green)}}
.trend-down{{color:var(--red)}}
.bc-name{{max-width:220px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.table-scroll{{max-height:500px;overflow:auto;border-radius:8px;border:1px solid var(--border)}}
.chart-container{{height:300px;position:relative}}
.badge{{display:inline-block;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:600}}
.badge-danger{{background:#ef444420;color:var(--red)}}
.badge-warn{{background:#f59e0b20;color:var(--yellow)}}
.badge-ok{{background:#10b98120;color:var(--green)}}
.search{{background:var(--card2);border:1px solid var(--border);color:var(--text);padding:8px 14px;border-radius:8px;font-size:14px;width:250px;margin-bottom:12px}}
.search:focus{{outline:none;border-color:var(--accent)}}
@media(max-width:900px){{.kpi-grid{{grid-template-columns:repeat(3,1fr)}}.grid-2{{grid-template-columns:1fr}}}}
@media(max-width:600px){{.kpi-grid{{grid-template-columns:repeat(2,1fr)}}}}
th{{cursor:pointer;user-select:none;position:sticky;top:0;z-index:10;padding:10px 25px 10px 10px !important;color:#fff;background:#0ea5e9;font-weight:700;text-transform:uppercase;font-size:11px;letter-spacing:0.5px;border-bottom:1px solid #0284c7; border-right:1px solid rgba(255,255,255,0.1); box-shadow: none;}}
th .th-content{{display:flex;align-items:center;justify-content:center;gap:4px}}
th .sort-icon{{position:absolute;right:8px;top:50%;transform:translateY(-50%);opacity:0.3;font-size:10px}}
th.sort-asc .sort-icon::after{{content:'↑';opacity:1}}
th.sort-desc .sort-icon::after{{content:'↓';opacity:1}}
th:not(.sort-asc):not(.sort-desc) .sort-icon::after{{content:'↕'}}
th .filter-icon{{opacity:0.5;cursor:pointer;font-size:11px;padding:2px;margin-left:4px}}
th .filter-icon:hover{{opacity:1;background:rgba(255,255,255,0.2);border-radius:3px}}

/* Premium Filter Dropdown */
.filter-dropdown {{
  position: fixed; min-width: 200px; max-height: 400px;
  background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px;
  box-shadow: 0 10px 25px -5px rgba(0,0,0,0.2), 0 8px 10px -6px rgba(0,0,0,0.1);
  z-index: 10000; display: none; flex-direction: column;
  color: #1e293b; text-align: left; text-transform: none; font-size: 14px;
  font-weight: 500;
  animation: slideDown 0.2s ease-out;
}}
@keyframes slideDown {{ from {{ opacity: 0; transform: translateY(-10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
.filter-dropdown.active {{ display: flex; }}
.filter-search-box {{ padding: 8px; border-bottom: 1px solid #f1f5f9; }}
.filter-search-box input {{ 
  width: 100%; padding: 6px 10px; border: 1px solid #e2e8f0; border-radius: 4px;
  font-size: 13px; outline: none; background: #f8fafc;
}}
.filter-list {{ overflow-y: auto; flex: 1; padding: 4px 0; }}
.filter-item {{ 
  display: flex; align-items: center; gap: 10px; padding: 8px 12px; cursor: pointer;
  transition: all 0.2s ease; border-left: 3px solid transparent;
}}
.filter-item:hover {{ background: #f8fafc; border-left-color: #0284c7; }}
.filter-item input[type="checkbox"] {{ width: 15px; height: 15px; cursor: pointer; accent-color: #0284c7; }}
.filter-footer {{ 
  display: flex; gap: 8px; padding: 10px; border-top: 1px solid #f1f5f9;
  background: #f8fafc; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px;
}}
.filter-btn {{
  flex: 1; padding: 6px 0; border-radius: 6px; font-size: 13px; font-weight: 600;
  cursor: pointer; text-align: center; border: 1px solid #e2e8f0; transition: all 0.2s;
}}
.filter-btn.cancel {{ background: #fff; color: #64748b; }}
.filter-btn.apply {{ background: #0284c7; color: #fff; border-color: #0284c7; }}
.filter-btn:hover {{ filter: brightness(0.95); }}


/* --- EXECUTIVE AI CHATBOT V10.0: ELITE PRO --- */
:root {{
  --trinh-primary: #e11d48;
  --trinh-accent: #fb7185;
  --trinh-glass: rgba(255, 255, 255, 0.85);
  --trinh-text: #0f172a;
}}

.trinh-launcher {{
  position: fixed; bottom: 30px; right: 30px; width: 65px; height: 65px;
  background: url('trinh_avatar.png');
  background-size: cover; border-radius: 50%; cursor: pointer; z-index: 9999;
  box-shadow: 0 10px 25px rgba(225, 29, 72, 0.4); border: 3px solid #fff;
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}}
.trinh-launcher:hover {{ transform: scale(1.1) rotate(5deg); }}
.trinh-launcher::after {{
  content: ''; position: absolute; inset: -5px; border-radius: 50%;
  border: 2px solid var(--trinh-primary); animation: trinh-pulse 2s infinite;
}}
@keyframes trinh-pulse {{ 0% {{ transform: scale(1); opacity: 1; }} 100% {{ transform: scale(1.4); opacity: 0; }} }}

.trinh-window {{
  position: fixed; bottom: 100px; right: 30px; width: 380px; height: 580px;
  background: #fff; border-radius: 20px; border: 1px solid #fecdd3; z-index: 9998;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  display: none; flex-direction: column; overflow: hidden;
  font-family: 'Plus Jakarta Sans', sans-serif; transition: all 0.3s ease;
}}

.trinh-header {{
  padding: 15px 20px; background: #fff; border-bottom: 1px solid #fce7f3;
  display: flex; align-items: center; gap: 12px; position: relative;
}}
.trinh-avatar-small {{ width: 48px; height: 48px; border-radius: 50%; border: 2px solid #fce7f3; background: url('trinh_avatar.png') center/cover; }}
.trinh-header-info h3 {{ font-size: 18px; font-weight: 800; margin: 0; color: #db2777; }}
.trinh-header-info p {{ font-size: 13px; color: #64748b; margin: 2px 0 0; display: flex; align-items: center; gap: 6px; }}
.trinh-status-dot {{ width: 10px; height: 10px; background: #22c55e; border-radius: 50%; }}
.trinh-msg div[style*="color:#db2777"] {{ margin-top: 10px !important; margin-bottom: 2.5px !important; padding: 0 !important; }}

.trinh-messages {{ flex: 1; overflow-y: auto; padding: 12px; display: flex; flex-direction: column; gap: 10px; background: #fff; }}
.trinh-msg {{ max-width: 90%; padding: 10px 14px; border-radius: 12px; font-size: 13.5px; line-height: 1.6; position: relative; color: #000; }}
.trinh-msg br {{ content: ""; margin: 4px 0; display: block; }}
.trinh-msg b {{ color: #000; font-weight: 700; }}
.trinh-msg.bot {{ align-self: flex-start; background: #fff1f2; color: #000; border-bottom-left-radius: 4px; border: 1px solid #ffe4e6; }}
.trinh-msg.user {{ align-self: flex-end; background: #db2777; color: #fff; border-bottom-right-radius: 4px; box-shadow: 0 4px 10px rgba(219, 39, 119, 0.2); }}

.trinh-input-area {{ padding: 15px; background: #fff; display: flex; gap: 10px; align-items: center; border-top: 1px solid #f1f5f9; }}
.trinh-input {{ flex: 1; padding: 12px 18px; border-radius: 25px; border: 1px solid #f1f5f9; background: #f8fafc; font-size: 14px; outline: none; }}
.trinh-send {{ width: 42px; height: 42px; border-radius: 50%; background: #db2777; color: #fff; border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 10px rgba(219, 39, 119, 0.3); }}
.trinh-send:hover {{ transform: scale(1.05); filter: brightness(1.1); }}

.trinh-typing {{ font-style: italic; font-size: 12px; color: #64748b; margin: 0 0 10px 20px; display: none; }}

.trinh-suggestions {{
  display: flex; gap: 8px; padding: 0 15px 10px; overflow-x: auto;
  scrollbar-width: none;
}}
.trinh-suggestions::-webkit-scrollbar {{ display: none; }}
.trinh-suggestions button {{
  padding: 6px 14px; background: #fff; border: 1px solid #fee2e2; border-radius: 20px;
  font-size: 12px; color: #be123c; cursor: pointer; white-space: nowrap;
  transition: all 0.2s; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}}
.trinh-suggestions button:hover {{ background: #fff1f2; border-color: #fda4af; transform: translateY(-1px); }}

.trinh-attach-btn {{
  display: flex; align-items: center; justify-content: center;
  min-width: 40px; height: 40px; border-radius: 50%;
  background: #f1f5f9; color: #64748b; cursor: pointer;
  transition: all 0.2s; border: 1px solid #e2e8f0; font-size: 18px;
}}
.trinh-attach-btn:hover {{ background: #e2e8f0; color: #db2777; }}
.trinh-file-preview {{
  padding: 5px 15px; display: flex; gap: 8px; flex-wrap: wrap;
  background: #fff; border-top: 1px solid #f1f5f9;
}}
.preview-item {{
  position: relative; width: 50px; height: 50px; border-radius: 8px;
  overflow: hidden; border: 1px solid #fecdd3; background: #fff;
}}
.preview-item img {{ width: 100%; height: 100%; object-fit: cover; }}
.preview-item .remove-file {{
  position: absolute; top: -2px; right: -2px; background: rgba(0,0,0,0.6);
  color: #fff; border-radius: 50%; width: 16px; height: 16px;
  font-size: 12px; display: flex; align-items: center; justify-content: center;
  cursor: pointer; line-height: 1;
}}

.trinh-key-card {{
  background: rgba(255, 241, 242, 0.95);
  border: 1px dashed #f43f5e;
  border-radius: 12px;
  padding: 14px;
  margin: 10px 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  box-shadow: 0 4px 15px rgba(225, 29, 72, 0.1);
}}
.trinh-key-title {{
  color: #db2777;
  font-weight: 700;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 6px;
}}
.trinh-key-input-container {{
  display: flex;
  gap: 8px;
}}
.trinh-key-input {{
  flex: 1;
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid #fda4af;
  font-size: 13px;
  outline: none;
  background: #fff;
  transition: all 0.2s;
}}
.trinh-key-input:focus {{
  border-color: #db2777;
  box-shadow: 0 0 0 2px rgba(219, 39, 119, 0.2);
}}
.trinh-key-save-btn {{
  background: #db2777;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}}
.trinh-key-save-btn:hover {{
  background: #be123c;
  transform: translateY(-1px);
}}
</style>
</head>
<body>
<div class="header">
<div><h1>GHN • VÙNG TÂY NGUYÊN</h1><div class="date">Cập nhật: {datetime.now().strftime('%H:%M %d/%m/%Y')} • <b>TNG - Kỷ Luật Là Sức Mạnh</b></div></div>
<div style="display:flex;gap:10px;align-items:center">
<a href="https://noibo.ghn.vn/eform/form" target="_blank" class="btn-quick" style="background:linear-gradient(135deg,#3b82f6,#2563eb)">📋 Duyệt EF</a>
<a href="https://noibo.ghn.vn/qlns/form?tab=list-form" target="_blank" class="btn-quick" style="background:linear-gradient(135deg,#10b981,#059669)">👥 QLNS</a>
<a href="https://noibo.ghn.vn/crm/policy-form" target="_blank" class="btn-quick" style="background:linear-gradient(135deg,#f59e0b,#d97706)">💰 Duyệt Giá</a>
<a href="tg://" class="btn-quick" style="background:linear-gradient(135deg,#0088cc,#006699)">✈️ Telegram</a>
<a href="https://ic.haraworks.vn/internal_mail/inbox" target="_blank" class="btn-quick" style="background:linear-gradient(135deg,#8b5cf6,#7c3aed)">📧 Email</a>
</div>
</div>

<div class="kpi-grid">
<div class="kpi-card" onclick="showTab(1, true)"><div class="kpi-label">VOLUME GIAO</div><div class="kpi-value">{num(vol_giao)}</div>{delta_vol}</div>
<div class="kpi-card" onclick="showTab(1, true)"><div class="kpi-label">GTC Tổng</div><div class="kpi-value">{pct(avg_gtc)}</div>{delta_gtc_v}</div>
<div class="kpi-card" onclick="showTab(2, true)"><div class="kpi-label">% GTC TTS</div><div class="kpi-value">{pct(avg_gtc_tts)}</div>{delta_gtc_t}</div>
<div class="kpi-card" onclick="showTab(3, true)"><div class="kpi-label">% ODR TTS</div><div class="kpi-value">{pct(avg_ontime)}</div>{delta_ontime}</div>
<div class="kpi-card" onclick="showTab(4, true)"><div class="kpi-label">% OPR TTS</div><div class="kpi-value" style="color:{'#ef4444' if opr_total_val < 0.95 else '#22c55e'}">{pct(opr_total_val)}</div>{delta_opr}</div>
<div class="kpi-card" onclick="showTab(6, true)"><div class="kpi-label">DT LẤY LŨY KẾ</div><div class="kpi-value">{money(total_rev_lay)}</div>{delta_rev}</div>
<div class="kpi-card" onclick="showTab(7, true)"><div class="kpi-label">NS THIẾU / ĐỊNH BIÊN</div><div class="kpi-value" style="color:#ef4444">{int(safe_num(ns_total.get('so_thieu',0)))} / {int(safe_num(ns_total.get('ptt_can',0)))}</div>{delta_ns}</div>
<div class="kpi-card" onclick="showTab(8, true)"><div class="kpi-label">BC CẢNH BÁO</div><div class="kpi-value">{n_warn}</div>{delta_warn}</div>
</div>

<div class="tabs">
<div class="tab active" onclick="showTab(0)"><i data-lucide="layout-dashboard"></i> Tổng quan Vùng</div>
<div class="tab" onclick="showTab(1)"><i data-lucide="bar-chart-3"></i> GTC Tổng</div>
<div class="tab" onclick="showTab(2)"><i data-lucide="target"></i> GTC TTS</div>
<div class="tab" onclick="showTab(3)"><i data-lucide="clock"></i> % ODR TTS</div>
<div class="tab" onclick="showTab(4)"><i data-lucide="zap"></i> % OPR TTS</div>
<div class="tab" onclick="showTab(5)"><i data-lucide="package"></i> Lấy hàng</div>
<div class="tab" onclick="showTab(6)"><i data-lucide="briefcase"></i> Kinh doanh</div>
<div class="tab" onclick="showTab(7)"><i data-lucide="users"></i> Nhân sự</div>
<div class="tab" onclick="showTab(8)"><i data-lucide="alert-triangle"></i> BC Cảnh Báo</div>
<div class="tab" onclick="showTab(9)"><i data-lucide="info"></i> Giới thiệu</div>
</div>

<div class="content">
<!-- TAB 1: GTC Tổng -->
<div class="panel active" id="p0">
<div class="grid-2">
  <div class="card"><div class="section-title"><span></span>Xu Hướng % GTC 7 Ngày Gần Nhất</div><div class="chart-container" style="height:550px"><canvas id="chartTrend"></canvas></div></div>
  <div class="card"><div class="section-title"><span></span>Tỷ Trọng Volume Theo AM</div><div class="chart-container" style="height:550px"><canvas id="chartGtc"></canvas></div></div>
</div>

<div class="card" style="margin-top:16px"><div class="section-title"><span></span>% GTC Vùng TNG</div>
<div class="table-scroll"><table>
<thead>
  <tr><th>Tỉnh</th>{''.join([f'<th>{l}</th>' for l in trend_labels])}</tr>
</thead>
<tbody>{trend_rows}</tbody>
</table></div></div>

<div class="card" style="margin-top:16px">
  <div class="section-title"><span></span>🔥 Điểm Nóng Hôm Nay</div>
  <div style="font-size:13px; color:var(--dim); margin-bottom:12px">Được cảnh báo tự động dựa trên mức độ rủi ro tổng hợp đa chiều (GTC, ODR, Nhân sự, Cảnh báo 7 ngày).</div>
  <div class="grid-2">
    <div>
      <div style="font-size:13px; font-weight:700; color:var(--dim); margin-bottom:8px; display:flex; align-items:center; gap:6px">👤 CẢNH BÁO THEO AM</div>
      {am_hs_html}
    </div>
    <div>
      <div style="font-size:13px; font-weight:700; color:var(--dim); margin-bottom:8px; display:flex; align-items:center; gap:6px">🏤 CẢNH BÁO THEO BƯU CỤC</div>
      {bc_hs_html}
    </div>
  </div>
</div>

<div class="card" style="margin-top:16px">
  <div class="section-title"><span></span>📉 Dự Báo Rủi Ro (7 Ngày vs 30 Ngày)</div>
  <div style="font-size:13px; color:var(--dim); margin-bottom:12px">Danh sách 5 bưu cục có xu hướng giảm sút hoặc cách biệt mục tiêu lớn nhất, cần can thiệp sớm.</div>
  <div class="table-scroll">
    <table class="table-compact">
      <thead>
        <tr>
          <th class="text-left">AM</th>
          <th class="text-left">Bưu cục</th>
          <th>Tỉnh</th>
          <th>% GTC 7 Ngày</th>
          <th>Mức cảnh báo</th>
          <th>Khoảng cách</th>
          <th>Các chỉ số khác</th>
          <th>Mức độ rủi ro</th>
        </tr>
      </thead>
      <tbody>
        {risk_rows}
      </tbody>
    </table>
  </div>
</div>

<div class="card" style="margin-top:16px; background: linear-gradient(to bottom, #f8fafc, #ffffff);">
  <div class="section-title"><span></span>📢 Đề Xuất Hành Động</div>
  {action_proposals_html}
</div></div>

<!-- TAB 1: GTC BC -->
<div class="panel" id="p1">
<div class="card"><div class="section-title"><span></span>% GTC Tổng Theo Tỉnh</div>
<div class="table-scroll"><table id="tblGtcTinh">
<thead>
  <tr>
    <th rowspan="2">Tỉnh</th>
    <th colspan="3" style="background:#fef08a; color:#854d0e">Hàng mới ca 1</th>
    <th colspan="3" style="background:#4ade80; color:#064e3b">Hàng mới ca 2</th>
    <th colspan="3" style="background:#e9d5ff; color:#581c87">Hàng tồn</th>
    <th colspan="3" style="background:#67e8f9; color:#0e7490">Tổng ngày</th>
    <th colspan="2" style="background:#cbd5e1; color:#1e293b">So sánh N-1</th>
  </tr>
  <tr>
    <th style="top:31px">Volume</th><th style="top:31px">% Gán</th><th style="top:31px">% GTC</th>
    <th style="top:31px">Volume</th><th style="top:31px">% Gán</th><th style="top:31px">% GTC</th>
    <th style="top:31px">Volume</th><th style="top:31px">% Gán</th><th style="top:31px">% GTC</th>
    <th style="top:31px">Volume</th><th style="top:31px">% Gán</th><th style="top:31px">% GTC</th>
    <th style="top:31px">GTC N-1</th><th style="top:31px">Biến động</th>
  </tr>
</thead>
<tbody>{gtc_tinh_rows}</tbody></table></div></div>

<div class="card"><div class="section-title"><span></span>% GTC Tổng Theo AM</div>
<div class="table-scroll"><table id="tblGtcAM">
<thead>
  <tr>
    <th rowspan="2">AM</th>
    <th colspan="3" style="background:#fef08a; color:#854d0e">Hàng mới ca 1</th>
    <th colspan="3" style="background:#4ade80; color:#064e3b">Hàng mới ca 2</th>
    <th colspan="3" style="background:#e9d5ff; color:#581c87">Hàng tồn</th>
    <th colspan="3" style="background:#67e8f9; color:#0e7490">Tổng ngày</th>
  </tr>
  <tr>
    <th style="top:31px">Volume</th><th style="top:31px">% Gán</th><th style="top:31px">% GTC</th>
    <th style="top:31px">Volume</th><th style="top:31px">% Gán</th><th style="top:31px">% GTC</th>
    <th style="top:31px">Volume</th><th style="top:31px">% Gán</th><th style="top:31px">% GTC</th>
    <th style="top:31px">Volume</th><th style="top:31px">% Gán</th><th style="top:31px">% GTC</th>
  </tr>
</thead>
<tbody>{gtc_rows}</tbody></table></div></div>

<div class="card"><div class="section-title"><span></span>% GTC Chi Tiết Theo Bưu Cục</div>
<input class="search" placeholder="🔍 Tìm bưu cục..." oninput="filterTable(this,'tblBC')">
<div class="table-scroll"><table id="tblBC"><thead><tr><th>#</th><th class="text-left">AM</th><th class="text-left">Bưu Cục</th><th>Volume</th><th>GTC Ca1</th><th>GTC Tồn</th><th>%Gán</th><th>%GTC</th><th>Leadtime</th></tr></thead><tbody>{bc_rows}</tbody></table></div></div>
</div>

<!-- TAB 2: GTC TTS -->
<div class="panel" id="p2">
<div class="card"><div class="section-title"><span></span>% GTC TTS Theo Tỉnh</div>
<div class="table-scroll"><table id="tblGtcTtsTinh">
<thead>
  <tr>
    <th rowspan="2">Tỉnh</th>
    <th colspan="3" style="background:#fef08a; color:#854d0e">Hàng mới ca 1</th>
    <th colspan="3" style="background:#4ade80; color:#064e3b">Hàng mới ca 2</th>
    <th colspan="3" style="background:#e9d5ff; color:#581c87">Hàng tồn</th>
    <th colspan="3" style="background:#67e8f9; color:#0e7490">Tổng ngày</th>
    <th colspan="2" style="background:#cbd5e1; color:#1e293b">So sánh N-1</th>
  </tr>
  <tr>
    <th style="top:31px">Volume</th><th style="top:31px">% Gán</th><th style="top:31px">% GTC</th>
    <th style="top:31px">Volume</th><th style="top:31px">% Gán</th><th style="top:31px">% GTC</th>
    <th style="top:31px">Volume</th><th style="top:31px">% Gán</th><th style="top:31px">% GTC</th>
    <th style="top:31px">Volume</th><th style="top:31px">% Gán</th><th style="top:31px">% GTC</th>
    <th style="top:31px">GTC N-1</th><th style="top:31px">Biến động</th>
  </tr>
</thead>
<tbody>{gtc_tts_tinh_rows}</tbody></table></div></div>

<div class="card"><div class="section-title"><span></span>% GTC TTS Theo AM</div>
<div class="table-scroll"><table id="tblGtcTtsAM">
<thead>
  <tr>
    <th rowspan="2">AM</th>
    <th colspan="3" style="background:#fef08a; color:#854d0e">Hàng mới ca 1</th>
    <th colspan="3" style="background:#4ade80; color:#064e3b">Hàng mới ca 2</th>
    <th colspan="3" style="background:#e9d5ff; color:#581c87">Hàng tồn</th>
    <th colspan="3" style="background:#67e8f9; color:#0e7490">Tổng ngày</th>
  </tr>
  <tr>
    <th style="top:31px">Volume</th><th style="top:31px">% Gán</th><th style="top:31px">% GTC</th>
    <th style="top:31px">Volume</th><th style="top:31px">% Gán</th><th style="top:31px">% GTC</th>
    <th style="top:31px">Volume</th><th style="top:31px">% Gán</th><th style="top:31px">% GTC</th>
    <th style="top:31px">Volume</th><th style="top:31px">% Gán</th><th style="top:31px">% GTC</th>
  </tr>
</thead>
<tbody>{gtc_tts_am_rows}</tbody></table></div></div>

<div class="card"><div class="section-title"><span></span>% GTC Đơn TTS Theo Bưu Cục</div>
<input class="search" placeholder="🔍 Tìm bưu cục..." oninput="filterTable(this,'tblGtcTts')">
<div class="table-scroll"><table id="tblGtcTts"><thead><tr><th>#</th><th class="text-left">AM</th><th class="text-left">Bưu Cục</th><th>Volume</th><th>GTC Ca1</th><th>GTC Tồn</th><th>%Gán</th><th>%GTC</th></tr></thead><tbody>{tts_rows}</tbody></table></div></div>
</div>

<!-- TAB 3: ODR TTS -->
<div class="panel" id="p3">
<div class="card"><div class="section-title"><span></span>⏱️ % ODR TTS Theo AM (7 ngày gần nhất)</div>
<div class="table-scroll"><table id="tblOntimeAM"><thead><tr><th class="text-left">AM</th>{ontime_header_html}<th>So N-1</th></tr></thead><tbody>{ontime_am_rows}</tbody></table></div></div>

<div class="card" style="margin-top:16px"><div class="section-title"><span></span>⏱️ % ODR TTS Theo Bưu Cục (7 ngày gần nhất)</div>
<input class="search" placeholder="🔍 Tìm Bưu Cục..." oninput="filterTable(this,'tblOntimeBC')">
<div class="table-scroll"><table id="tblOntimeBC"><thead><tr><th class="text-left">AM</th><th class="text-left">Bưu Cục</th>{ontime_header_html}<th>So N-1</th></tr></thead><tbody>{ontime_bc_rows}</tbody></table></div></div>
</div>

<!-- TAB 4: OPR Tỉnh -->
<div class="panel" id="p4">
<div class="card" style="margin-bottom:16px"><div class="section-title"><span></span>Xu Hướng % OPR TTS 7 Ngày Gần Nhất</div>
<div class="chart-container" style="height:350px"><canvas id="chartOPRTrend"></canvas></div></div>

<div class="card" style="margin-bottom:16px"><div class="section-title"><span></span>🚀 % OPR TTS Theo Tỉnh</div>
<div class="table-scroll"><table id="tblOPRTinh" class="tbl-opr no-interactive"><thead>{opr_tinh_header_1}{opr_tinh_header_2}</thead><tbody>{opr_tinh_matrix_rows}</tbody></table></div></div>

<div class="card"><div class="section-title"><span></span>🚀 % OPR TTS Theo AM</div>
<div class="table-scroll"><table id="tblOPRAM" class="tbl-opr no-interactive"><thead>{opr_am_header_1}{opr_am_header_2}</thead><tbody>{opr_am_matrix_rows}</tbody></table></div></div>
</div>

<!-- TAB 5: LTC -->
<div class="panel" id="p5">
<div class="card" style="margin-bottom:16px"><div class="section-title"><span></span>% Lấy Thành Công Tổng Theo AM</div>
<div class="table-scroll"><table id="tblLtcAM"><thead>
  <tr>
    <th rowspan="2">#</th>
    <th rowspan="2" class="text-left">AM</th>
    <th colspan="3" style="background:#fef08a; color:#854d0e">HÀNG MỚI</th>
    <th colspan="3" style="background:#e9d5ff; color:#581c87">Hàng tồn</th>
    <th colspan="3" style="background:#67e8f9; color:#0e7490">Tổng ngày</th>
  </tr>
  <tr>
    <th style="top:31px">Volume</th><th style="top:31px">% Gán</th><th style="top:31px">% LTC</th>
    <th style="top:31px">Volume</th><th style="top:31px">% Gán</th><th style="top:31px">% LTC</th>
    <th style="top:31px">Volume</th><th style="top:31px">% Gán</th><th style="top:31px">% LTC</th>
  </tr>
</thead><tbody>{ltc_rows}</tbody></table></div></div>
<div class="card"><div class="section-title"><span></span>% Lấy Thành Công TTS Theo AM</div>
<div class="table-scroll"><table id="tblLtcTts"><thead>
  <tr>
    <th rowspan="2">#</th>
    <th rowspan="2" class="text-left">AM</th>
    <th colspan="3" style="background:#fef08a; color:#854d0e">HÀNG MỚI</th>
    <th colspan="3" style="background:#e9d5ff; color:#581c87">Hàng tồn</th>
    <th colspan="3" style="background:#67e8f9; color:#0e7490">Tổng ngày</th>
  </tr>
  <tr>
    <th style="top:31px">Volume</th><th style="top:31px">% Gán</th><th style="top:31px">% LTC</th>
    <th style="top:31px">Volume</th><th style="top:31px">% Gán</th><th style="top:31px">% LTC</th>
    <th style="top:31px">Volume</th><th style="top:31px">% Gán</th><th style="top:31px">% LTC</th>
  </tr>
</thead><tbody>{ltc_tts_rows}</tbody></table></div></div>
</div>

<!-- TAB 6: KINH DOANH - DT LẤY TC -->
<div class="panel" id="p6">
<div class="card" style="margin-bottom:16px"><div class="section-title"><span></span>Xu Hướng Doanh Thu 7 Ngày Gần Nhất (triệu đồng)</div>
<div class="chart-container" style="height:250px"><canvas id="chartKDTrend"></canvas></div></div>
<div class="card" style="margin-bottom:16px"><div class="section-title"><span></span>Lũy Kế T5 vs Cùng Kỳ T4 (triệu đồng)</div>
<div class="chart-container" style="height:350px"><canvas id="chartKD"></canvas></div></div>
<div class="card"><div class="section-title"><span></span>DT Lấy Thành Công Theo SO (Lũy kế: {money(total_rev_lay)} | Cùng kỳ T4: {money(total_cungky)})</div>
<div class="table-scroll"><table id="tblKD"><thead>
<tr><th class="text-left" rowspan="2">AM</th>{kd_header_cells}<th rowspan="2">So N-1</th><th rowspan="2">Cùng Kỳ T4</th><th rowspan="2">Lũy Kế T5</th><th rowspan="2">So CK</th></tr>
<tr><th>DT</th><th>Vol</th><th>DT</th><th>Vol</th><th>DT</th><th>Vol</th><th>DT</th><th>Vol</th><th>DT</th><th>Vol</th><th>DT</th><th>Vol</th><th>DT</th><th>Vol</th></tr>
</thead><tbody>{kd_rows}{kd_total_row}</tbody></table></div></div>
</div>

<!-- TAB 7: Nhân Sự -->
<div class="panel" id="p7">
<div class="card" style="margin-bottom:16px"><div class="section-title"><span></span>Tình Hình Nhân Sự Toàn Vùng (NVPTTT: Định biên {int(safe_num(ns_total.get('ptt_can',0)))} | Có {int(safe_num(ns_total.get('ptt_co',0)))} | Thiếu {int(safe_num(ns_total.get('so_thieu',0)))})</div>
<div class="chart-container" style="height:300px"><canvas id="chartNS"></canvas></div></div>
<div class="card" style="margin-bottom:16px"><div class="section-title"><span></span>Tổng Hợp Theo Tỉnh</div>
<div class="table-scroll"><table id="tblNSTinh"><thead>
<tr><th class="text-left" rowspan="2">Tỉnh</th><th rowspan="2">SL BC</th><th colspan="8">NVPTTT</th><th colspan="2">NVXL</th></tr>
<tr><th>Định biên</th><th>Có</th><th>Thiếu</th><th>YCTD</th><th>Đã Tuyển</th><th>Còn Làm</th><th>DK OB</th><th>Cần Tuyển</th><th>Định biên</th><th>Có</th></tr>
</thead><tbody>{ns_tinh_rows}</tbody></table></div></div>
<div class="card" style="margin-bottom:16px"><div class="section-title"><span></span>Tổng Hợp Theo AM</div>
<div class="table-scroll"><table id="tblNSAM"><thead>
<tr><th class="text-left" rowspan="2">AM</th><th rowspan="2">SL BC</th><th colspan="8">NVPTTT</th><th colspan="2">NVXL</th></tr>
<tr><th>Định biên</th><th>Có</th><th>Thiếu</th><th>YCTD</th><th>Đã Tuyển</th><th>Còn Làm</th><th>DK OB</th><th>Cần Tuyển</th><th>Định biên</th><th>Có</th></tr>
</thead><tbody>{ns_am_rows}</tbody></table></div></div>
<div class="card"><div class="section-title"><span></span>Chi Tiết Theo Bưu Cục</div>
<div class="table-scroll"><table id="tblNS"><thead><tr><th class="text-left">Tỉnh</th><th class="text-left">AM</th><th class="text-left">Bưu Cục</th><th>Định biên</th><th>Có</th><th>Thiếu</th><th>YCTD</th><th>Đã Tuyển</th><th>Còn Làm</th><th>DK OB</th><th>Cần Tuyển</th></tr></thead><tbody>{ns_detail_rows}</tbody></table></div></div>
</div>

<!-- TAB 8: BC Cảnh Báo -->
<div class="panel" id="p8">
<div class="card"><div class="section-title"><span></span>⚠️ Bưu Cục Cảnh Báo</div>
<div class="table-scroll"><table id="tblCB"><thead><tr><th class="text-left">Tỉnh</th><th class="text-left">AM</th><th class="text-left">Bưu Cục</th><th>% GTC 7 NGÀY</th><th>GTC LỊCH SỬ</th><th>CẦN ĐẠT</th><th>GTC NGÀY N-1</th><th>GTC NGÀY N-2</th><th>GTC NGÀY N-3</th></tr></thead><tbody>{cb_rows}</tbody></table></div></div>

<div class="card" style="margin-top:16px"><div class="section-title"><span></span>⚠️ Bưu Cục Cảnh Báo Vùng</div>
<div class="table-scroll"><table id="tblCBVung"><thead><tr><th class="text-left">Tỉnh</th><th class="text-left">AM</th><th class="text-left">Bưu Cục</th><th>% GTC 7 NGÀY</th><th>GTC TỐT NHẤT</th><th>CẦN ĐẠT</th><th>CHÊNH LỆCH</th><th>NHÓM</th></tr></thead><tbody>{cb_vung_rows}</tbody></table></div></div>
</div>

<!-- TAB 9: Giới Thiệu -->
<div class="panel" id="p9">
  <div class="card" style="background: linear-gradient(135deg, #0284c7 0%, #0ea5e9 100%); color: white; padding: 28px 24px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1)">
    <div style="display: flex; align-items: center; gap: 16px;">
      <div style="background: rgba(255,255,255,0.15); padding: 12px; border-radius: 12px; backdrop-filter: blur(4px)">
        <i data-lucide="info" style="width: 32px; height: 32px; color: white"></i>
      </div>
      <div>
        <h2 style="font-size: 26px; font-weight: 800; margin-bottom: 4px; letter-spacing: 0.5px">TNG OPERATIONAL INTELLIGENCE DASHBOARD</h2>
        <p style="font-size: 14px; opacity: 0.9; font-weight: 500">Hệ thống Giám Sát và Quản Trị Vận Hành Vùng Tây Nguyên - Giao Hàng Nhanh (GHN)</p>
      </div>
    </div>
  </div>

  <div class="grid-2" style="margin-bottom: 20px">
    <!-- Purpose & Idea -->
    <div class="card" style="display: flex; flex-direction: column; justify-content: space-between">
      <div>
        <div class="section-title"><span></span>🎯 Giới Thiệu</div>
        <p style="font-size: 14px; line-height: 1.6; color: var(--dim); margin-bottom: 12px">
          Dashboard Vận Hành Vùng Tây Nguyên (TNG) ra đời với mục tiêu <strong>chuẩn hóa, tự động hóa và thông minh hóa</strong> toàn bộ dữ liệu báo cáo vận hành hàng ngày của khu vực. 
        </p>
        <p style="font-size: 14px; line-height: 1.6; color: var(--dim); margin-bottom: 12px">
          Thay vì xử lý thủ công các tệp Excel phân mảnh từ nhiều nguồn, hệ thống tự động đồng bộ hóa và trích xuất dữ liệu vận hành từ các báo cáo cốt lõi. Từ đó, đưa ra các phân tích trực quan về tỷ lệ <strong>Giao Thành Công (%GTC)</strong>, <strong>OnTime giao hàng (%ODR)</strong>, <strong>OnTime lấy hàng (%OPR)</strong>, tình hình kinh doanh và định biên nhân sự...
        </p>
        <p style="font-size: 14px; line-height: 1.6; color: var(--dim)">
          Ý tưởng cốt lõi là kết hợp <strong>Analytics trực quan</strong> với <strong>Trí Tuệ Nhân Tạo (Trợ lý AI)</strong> giúp: GĐV, AM và quản lý bưu cục đưa ra quyết định tối ưu hóa vận hành, cân đối nguồn lực và hành động ngăn ngừa rủi ro vận hành ngay lập tức.
        </p>
      </div>
    </div>

    <!-- Key Features -->
    <div class="card">
      <div class="section-title"><span></span>⚡ Tính Năng Nổi Bật</div>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px">
        <div style="padding: 12px; background: var(--card2); border-radius: 8px; border: 1px solid var(--border)">
          <div style="display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 14px; margin-bottom: 6px; color: var(--accent)">
            <i data-lucide="refresh-cw" style="width:16px; height:16px"></i> Tự Động Cập Nhật
          </div>
          <p style="font-size: 12px; color: var(--dim); line-height: 1.4">Đồng bộ tự động từ Google Sheets mỗi giờ, cơ chế tự phát hiện và sửa lỗi dữ liệu hiển thị.</p>
        </div>
        <div style="padding: 12px; background: var(--card2); border-radius: 8px; border: 1px solid var(--border)">
          <div style="display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 14px; margin-bottom: 6px; color: var(--cyan)">
            <i data-lucide="alert-triangle" style="width:16px; height:16px"></i> Cảnh Báo Rủi Ro
          </div>
          <p style="font-size: 12px; color: var(--dim); line-height: 1.4">Tự động phát hiện bưu cục có rủi ro về tỷ lệ GTC, nhân sự và cảnh báo sớm.</p>
        </div>
        <div style="padding: 12px; background: var(--card2); border-radius: 8px; border: 1px solid var(--border)">
          <div style="display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 14px; margin-bottom: 6px; color: var(--green)">
            <i data-lucide="lightbulb" style="width:16px; height:16px"></i> Đề Xuất Hành Động
          </div>
          <p style="font-size: 12px; color: var(--dim); line-height: 1.4">Đưa ra khuyến nghị & đề xuất hành động cụ thể dựa trên số liệu tổng hợp các điểm nóng và dự báo rủi ro.</p>
        </div>
        <div style="padding: 12px; background: var(--card2); border-radius: 8px; border: 1px solid var(--border)">
          <div style="display: flex; align-items: center; gap: 8px; font-weight: 700; font-size: 14px; margin-bottom: 6px; color: var(--purple)">
            <i data-lucide="message-square" style="width:16px; height:16px"></i> Trợ Lý AI
          </div>
          <p style="font-size: 12px; color: var(--dim); line-height: 1.4">Tích hợp Chatbot vận hành AI chuyên sâu, trả lời phân tích dữ liệu tức thì.</p>
        </div>
      </div>
    </div>
  </div>

  <!-- Central Highlands Region section -->
  <div class="card" style="margin-bottom: 0">
    <div class="section-title"><span></span>🗺️ Bản Đồ Vận Hành Vùng Tây Nguyên</div>
    <div class="grid-2">
      <!-- Description -->
      <div style="display: flex; flex-direction: column; justify-content: space-between">
        <div>
          <div style="font-size: 16px; font-weight: 700; color: var(--accent); margin-bottom: 12px; display: flex; align-items: center; gap: 6px">
            <span style="width:3px; height:16px; background:var(--accent); border-radius:1.5px"></span>Đặc Thù Địa Bàn
          </div>
          <p style="font-size: 14px; line-height: 1.6; color: var(--dim); margin-bottom: 12px">
            Vùng Tây Nguyên (TNG) trong bản đồ vận hành của Giao Hàng Nhanh bao gồm 4 tỉnh chiến lược: <strong>Đắk Lắk, Gia Lai, Phú Yên và Bình Định</strong> với tổng <strong>65 bưu cục</strong>. Đây là khu vực có đặc thù địa lý vô cùng độc đáo, kết hợp giữa núi cao hiểm trở, cao nguyên đất đỏ trập trùng và dải duyên hải Nam Trung Bộ.
          </p>
          <p style="font-size: 14px; line-height: 1.6; color: var(--dim); margin-bottom: 12px">
            Vận hành tại Tây Nguyên đòi hỏi sự linh hoạt tối đa do khoảng cách giữa các bưu cục huyện thị rất lớn, hạ tầng giao thông chịu ảnh hưởng nặng nề vào mùa mưa kéo dài, cùng sự biến động nhân sự lớn theo mùa vụ nông sản (sầu riêng, cà phê, hồ tiêu).
          </p>
          <p style="font-size: 13px; font-weight: 600; color: var(--accent); margin-bottom: 12px; background: #e0f2fe; padding: 8px 12px; border-radius: 6px; display: inline-block">
            👉 Nhấp chuột vào từng tỉnh trên bản đồ để xem chi tiết thông tin vận hành khu vực!
          </p>
        </div>
        
        <!-- Info Card of selected province -->
        <div id="prov-info-card" style="padding: 16px; background: var(--card2); border: 1px solid var(--border); border-radius: 8px; transition: all 0.3s ease">
          <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid var(--border); padding-bottom: 8px; margin-bottom: 12px">
            <h4 id="prov-name" style="font-size: 18px; font-weight: 800; color: var(--accent)">ĐẮK LẮK</h4>
            <span style="font-size: 11px; font-weight: 700; color:#fff; background: var(--accent); padding: 2px 8px; border-radius: 12px">Active</span>
          </div>
          
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 13px; margin-bottom: 10px">
            <div><span style="color: var(--dim)">Thủ phủ hành chính:</span> <strong id="prov-capital">Buôn Ma Thuột</strong></div>
            <div><span style="color: var(--dim)">Quy mô mạng lưới:</span> <strong id="prov-hubs">24 Bưu cục</strong></div>
            <div><span style="color: var(--dim)">AM phụ trách:</span> <strong id="prov-am">{daklak_am}</strong></div>
            <div><span style="color: var(--dim)">GTC bình quân:</span> <strong id="prov-target" style="color: var(--green)">{daklak_gtc_avg}</strong></div>
            <div><span style="color: var(--dim)">Số lượng nhân sự:</span> <strong id="prov-staff">{daklak_ns} nhân sự</strong></div>
            <div><span style="color: var(--dim)">Tỷ trọng volume:</span> <strong id="prov-vol-pct">{daklak_vol_pct}</strong></div>
          </div>
          <div style="font-size: 13px; margin-bottom: 8px">
            <span style="color: var(--dim)">Thách thức lớn nhất:</span> <p id="prov-challenges" style="margin-top: 2px; font-weight: 500">Volume đơn hàng cao, đặc thù mùa vụ nông sản lớn: cà phê, sầu riêng, tiêu...</p>
          </div>
          <div style="font-size: 13px">
            <span style="color: var(--dim)">Trọng tâm vận hành:</span> <p id="prov-focus" style="margin-top: 2px; font-weight: 600; color: var(--accent)">Ổn định định biên nhân sự giao hàng và xử lý hàng ca 2 đối với các bưu cục trung tâm</p>
          </div>
        </div>
      </div>
      
      <!-- 3D Interactive Map Container -->
      <div style="width: 100%; margin-top: 8px;">
        <div class="map-container">
          <div class="map-zoom-wrapper" style="position: relative; width: 100%; height: 100%; transform: scale(1.28) translateY(3.5%); transform-origin: center center;">
            <img src="./tay_nguyen_3d_map.png" alt="Bản đồ 3D Vùng Tây Nguyên" style="width: 100%; height: 100%; object-fit: contain; object-position: center center; display: block; pointer-events: none;">
            
            <!-- === Province Glow Pins (center of each province) === -->
            
            <!-- Gia Lai - center of blue province -->
            <div class="map-pin" style="top: 33%; left: 47%;" data-id="gialai" onclick="selectProvince('gialai')">
              <div class="pin-pulse"></div>
              <div class="pin-pulse2"></div>
              <div class="pin-dot"></div>
              <div class="pin-label">GIA LAI</div>
            </div>
            
            <!-- Đắk Lắk - center of orange province (Default Active) -->
            <div class="map-pin active-pin" style="top: 57%; left: 45%;" data-id="daklak" onclick="selectProvince('daklak')">
              <div class="pin-pulse"></div>
              <div class="pin-pulse2"></div>
              <div class="pin-dot"></div>
              <div class="pin-label">ĐẮK LẮK</div>
            </div>
            
            <!-- Bình Định - center of green province -->
            <div class="map-pin" style="top: 29%; left: 62%;" data-id="binhdinh" onclick="selectProvince('binhdinh')">
              <div class="pin-pulse"></div>
              <div class="pin-pulse2"></div>
              <div class="pin-dot"></div>
              <div class="pin-label">BÌNH ĐỊNH</div>
            </div>
            
            <!-- Phú Yên - center of purple province -->
            <div class="map-pin" style="top: 56%; left: 65%;" data-id="phuyen" onclick="selectProvince('phuyen')">
              <div class="pin-pulse"></div>
              <div class="pin-pulse2"></div>
              <div class="pin-dot"></div>
              <div class="pin-label">PHÚ YÊN</div>
            </div>
            <!-- === Capital City Stars and Labels Removed === -->
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
</div>

<script>
Chart.defaults.font.family = "'Plus Jakarta Sans', sans-serif";
function showTab(i, scroll=false){{
  document.querySelectorAll('.tab').forEach((t,idx)=>t.classList.toggle('active',idx===i));
  document.querySelectorAll('.panel').forEach((p,idx)=>p.classList.toggle('active',idx===i));
  if(i===0&&!window._c1){{window._c1=true;initGtcChart()}}
  if(i===4&&!window._c4){{window._c4=true;initOPRTrendChart()}}
  if(i===6&&!window._c3){{window._c3=true;initKDChart();initKDTrendChart()}}
  if(i===7&&!window._c7){{window._c7=true;initNSChart()}}
  if(scroll){{
    const tabsEl = document.querySelector('.tabs');
    if(tabsEl){{
      const y = tabsEl.getBoundingClientRect().top + window.scrollY - 65;
      window.scrollTo({{top: y, behavior: 'smooth'}});
    }}
  }}
}}

function sortTable(th){{
  if(event.target.classList.contains('filter-icon')) return;
  const table = th.closest('table');
  const tbody = table.tBodies[0];
  const rows = Array.from(tbody.rows);
  const colIdx = Array.from(th.parentNode.cells).indexOf(th);
  const isAsc = th.classList.contains('sort-asc');
  
  table.querySelectorAll('th').forEach(h=>h.classList.remove('sort-asc','sort-desc'));
  const dir = isAsc ? -1 : 1;
  th.classList.add(isAsc ? 'sort-desc' : 'sort-asc');

  rows.sort((a,b)=>{{
    let valA = a.cells[colIdx].innerText.replace(/[%]/g,'').replace(/,/g,'').trim();
    let valB = b.cells[colIdx].innerText.replace(/[%]/g,'').replace(/,/g,'').trim();
    const numA = parseFloat(valA); const numB = parseFloat(valB);
    if(!isNaN(numA) && !isNaN(numB)) return (numA - numB) * dir;
    return valA.localeCompare(valB, 'vi', {{sensitivity: 'base'}}) * dir;
  }});
  rows.forEach(r=>tbody.appendChild(r));
}}

const _filters = {{}};

function toggleFilter(e, thIcon){{
  e.stopPropagation();
  const th = thIcon.closest('th');
  const table = th.closest('table');
  const colIdx = Array.from(th.parentNode.cells).indexOf(th);
  
  document.querySelectorAll('.filter-dropdown').forEach(d => d.remove());
  
  const dd = document.createElement('div');
  dd.className = 'filter-dropdown';
  dd.dataset.table = table.id;
  dd.dataset.col = colIdx;
  document.body.appendChild(dd);
  
  const rows = Array.from(table.tBodies[0].rows);
  const vals = [...new Set(rows.map(r => r.cells[colIdx].textContent.trim()))].sort();
  const activeFilters = _filters[table.id]?.[colIdx];

  dd.innerHTML = `
    <div class="filter-search-box">
      <input type="text" placeholder="Tìm kiếm giá trị..." oninput="filterDropdownItems(this)">
    </div>
    <div class="filter-list">
      <div class="filter-item" onclick="toggleAllFilters(this, event)">
        <input type="checkbox" ${{!activeFilters ? 'checked' : ''}}>
        <span>(Tất cả)</span>
      </div>
      ${{vals.map(v => {{
        const isChecked = !activeFilters || activeFilters.includes(v);
        return `
          <div class="filter-item" onclick="toggleFilterItem(this, event)">
            <input type="checkbox" value="${{v}}" ${{isChecked ? 'checked' : ''}}>
            <span>${{v}}</span>
          </div>
        `;
      }}).join('')}}
    </div>
    <div class="filter-footer">
      <div class="filter-btn cancel" onclick="closeFilter(this, event)">Hủy</div>
      <div class="filter-btn apply" onclick="applyExcelFilter(this, event)">Lọc</div>
    </div>
  `;
  
  // Add active class first so we can measure the layout size
  dd.classList.add('active');
  
  const rect = thIcon.getBoundingClientRect();
  dd.style.position = 'fixed';
  
  // Calculate dynamic top positioning to prevent screen overflow
  const ddHeight = dd.offsetHeight || 300;
  let topPos = rect.bottom + 5;
  if (topPos + ddHeight > window.innerHeight) {{
    topPos = rect.top - 5 - ddHeight;
    // Fallback if placing it above also overflows the top of the viewport
    if (topPos < 10) {{
      topPos = window.innerHeight - ddHeight - 10;
    }}
  }}
  if (topPos < 10) topPos = 10;
  dd.style.top = topPos + 'px';
  
  let leftPos = rect.left;
  if (leftPos + 220 > window.innerWidth) {{
    leftPos = window.innerWidth - 230;
  }}
  dd.style.left = leftPos + 'px';
}}

function filterDropdownItems(input){{
  const v = input.value.toLowerCase();
  const items = input.closest('.filter-dropdown').querySelectorAll('.filter-item:not(:first-child)');
  items.forEach(item => {{
    item.style.display = item.innerText.toLowerCase().includes(v) ? 'flex' : 'none';
  }});
  
  const dd = input.closest('.filter-dropdown');
  const allCb = dd.querySelector('.filter-list input:not([value])');
  const visibleItems = Array.from(dd.querySelectorAll('.filter-item:not(:first-child)')).filter(i => i.style.display !== 'none');
  const visibleChecked = visibleItems.every(item => item.querySelector('input').checked);
  if (visibleItems.length > 0) {{
    allCb.checked = visibleChecked;
  }}
}}

function toggleAllFilters(div, e){{
  const cb = div.querySelector('input');
  if(e.target !== cb) cb.checked = !cb.checked;
  const list = div.closest('.filter-dropdown').querySelectorAll('.filter-item');
  list.forEach(item => {{
    if (item.style.display !== 'none') {{
      const i = item.querySelector('input');
      if (i) i.checked = cb.checked;
    }}
  }});
}}

function toggleFilterItem(div, e){{
  const cb = div.querySelector('input');
  if(e.target !== cb) cb.checked = !cb.checked;
  
  const list = div.closest('.filter-list');
  const allCb = list.querySelector('input:not([value])');
  const items = Array.from(list.querySelectorAll('input[value]'));
  const allChecked = items.every(i => i.checked);
  allCb.checked = allChecked;
}}

function closeFilter(btn, e){{
  if(e) e.stopPropagation();
  document.querySelectorAll('.filter-dropdown').forEach(d => d.remove());
}}

function applyExcelFilter(btn, e){{
  if(e) e.stopPropagation();
  const dd = btn.closest('.filter-dropdown');
  const tableId = dd.dataset.table;
  const colIdx = parseInt(dd.dataset.col);
  const table = document.getElementById(tableId);
  if(!table) return dd.remove();

  const checkedInputs = Array.from(dd.querySelectorAll('.filter-list input[value]:checked'));
  const allChecked = dd.querySelector('.filter-list input:not([value])').checked;
  const values = checkedInputs.map(i => i.value);
  
  if(!_filters[tableId]) _filters[tableId] = {{}};
  _filters[tableId][colIdx] = allChecked ? null : values;
  
  execGlobalTableFilter(table);
  dd.remove();
}}

function execGlobalTableFilter(table){{
  if(!table || !table.tBodies[0]) return;
  const rows = Array.from(table.tBodies[0].rows);
  const tableFilters = _filters[table.id] || {{}};
  
  rows.forEach(r => {{
    let show = true;
    for(let colIdx in tableFilters){{
      const allowed = tableFilters[colIdx];
      if(allowed && !allowed.includes(r.cells[colIdx].textContent.trim())) show = false;
    }}
    r.style.display = show ? '' : 'none';
  }});
}}

document.addEventListener('DOMContentLoaded', ()=>{{
  document.querySelectorAll('th').forEach(th => {{
    const table = th.closest('table');
    if(!table.tBodies[0] || table.classList.contains('no-interactive')) return;
    const colIdx = Array.from(th.parentNode.cells).indexOf(th);
    const content = th.innerHTML;
    const headerText = th.innerText.toLowerCase();
    
    // Explicitly check for text columns that should have filters
    const isTextCol = headerText.includes('am') || headerText.includes('bưu cục') || headerText.includes('tỉnh') || headerText.includes('quản lý') || headerText.includes('bc');
    
    // Heuristic for numeric columns
    const firstRow = table.tBodies[0].rows[0];
    const sampleVal = firstRow ? firstRow.cells[colIdx].innerText.replace(/[%.,]/g,'').trim() : '';
    const isNumeric = sampleVal !== '' && !isNaN(parseFloat(sampleVal));

    let inner = `<div class="th-content"><span>${{content}}</span>`;
    
    // Skip all icons and listeners for index column (#)
    if(headerText === '#') {{
        th.innerHTML = `<div class="th-content"><span>${{content}}</span></div>`;
        th.style.cursor = 'default';
        return;
    }}

    // Only show filter for text columns that are NOT purely numeric
    if(isTextCol && !isNumeric) {{
      inner += `<span class="filter-icon" style="color:white; margin-left:4px" onclick="toggleFilter(event, this)">▼</span>`;
    }}
    inner += `<span class="sort-icon"></span></div>`;
    th.innerHTML = inner;
    th.addEventListener('click', ()=>sortTable(th));
  }});
  
  window.onclick = (e) => {{
    if(!e.target.closest('.filter-dropdown') && !e.target.classList.contains('filter-icon')){{
      document.querySelectorAll('.filter-dropdown').forEach(d => d.remove());
    }}
  }};

  // Initial call to load first tab charts
  showTab(0);
}});

function initGtcChart(){{
  new Chart(document.getElementById('chartGtc'),{{
    type:'doughnut',
    plugins:[ChartDataLabels],
    data:{{
      labels:{vol_labels},
      datasets:[{{
          label:'Volume Theo AM',
          data:{vol_data},
          backgroundColor:{vol_colors_js},
          borderWidth:2,borderColor:'#fff',
          hoverOffset:15,
          datalabels: {{
            display:true, color:'#000', font:{{weight:'bold',size:11}},
            formatter:(v,ctx)=>{{
              const sum=ctx.dataset.data.reduce((a,b)=>a+b,0);
              return (v/sum*100).toFixed(1)+'%';
            }}
          }}
        }},{{
          label:'Volume Theo Tỉnh',
          data:{prov_data},
          backgroundColor:{prov_colors_js},
          borderWidth:2,borderColor:'#fff',
          weight: 0.6,
          datalabels: {{
            display:true, color:'#000', font:{{weight:'800',size:12}},
            textAlign: 'center',
            formatter:(v,ctx)=>{{
              const labels = {prov_labels};
              const sum=ctx.dataset.data.reduce((a,b)=>a+b,0);
              return labels[ctx.dataIndex] + '\\n' + (v/sum*100).toFixed(1)+'%';
            }}
          }}
        }}]
    }},
    options:{{ 
      responsive:true,maintainAspectRatio:false,
      cutout:'35%',
      plugins:{{
        legend:{{position:'bottom',labels:{{boxWidth:12,font:{{size:11}}}}}},
        datalabels: {{ display: true }}
      }}
    }}
  }});

  new Chart(document.getElementById('chartTrend'),{{
    type: 'line',
    plugins: [ChartDataLabels],
    data: {{ 
      labels: {json.dumps(trend_labels)},
      datasets: [
        {{ label: 'Bình Định', data: {trend_data['Bình Định']}, borderColor: '#3b82f6', backgroundColor: '#3b82f6', tension: 0.3, fill: false, datalabels: {{ align: 'top', offset: 2 }} }},
        {{ label: 'Đắk Lắk', data: {trend_data['Đắk Lắk']}, borderColor: '#f59e0b', backgroundColor: '#f59e0b', tension: 0.3, fill: false, datalabels: {{ align: 'top', offset: 2 }} }},
        {{ label: 'Gia Lai', data: {trend_data['Gia Lai']}, borderColor: '#10b981', backgroundColor: '#10b981', tension: 0.3, fill: false, datalabels: {{ align: 'top', offset: 2 }} }},
        {{ label: 'Phú Yên', data: {trend_data['Phú Yên']}, borderColor: '#8b5cf6', backgroundColor: '#8b5cf6', tension: 0.3, fill: false, datalabels: {{ align: 'top', offset: 2 }} }},
        {{ label: 'Vùng TNG', data: {trend_data['Vùng TNG']}, borderColor: '#ef4444', backgroundColor: '#ef4444', borderDash: [5, 5], tension: 0.3, fill: false, borderWidth: 3, datalabels: {{ align: 'bottom', offset: 4, font: {{ weight: 'bold' }} }} }}
      ]
    }},
    options: {{ 
      responsive: true, maintainAspectRatio: false, 
      plugins: {{ 
        legend: {{ position: 'bottom' }},
        datalabels: {{ 
          display: true,
          color: (ctx) => ctx.dataset.borderColor,
          font: {{ size: 10, weight: '700' }},
          formatter: v => v + '%'
        }}
      }},
      scales: {{ 
        y: {{ beginAtZero: false, ticks: {{ callback: v => v + '%' }} }},
        x: {{ ticks: {{ }} }}
      }}
    }}
  }});
}}

function initOPRTrendChart(){{
  new Chart(document.getElementById('chartOPRTrend'), {{
    type: 'line',
    plugins: [ChartDataLabels],
    data: {{ 
      labels: {opr_trend_labels_js},
      datasets: [
        {{ label: 'Bình Định', data: {opr_trend_data.get('Bình Định', [])}, borderColor: '#3b82f6', backgroundColor: '#3b82f6', tension: 0.3, fill: false, datalabels: {{ align: 'top', offset: 2 }} }},
        {{ label: 'Đắk Lắk', data: {opr_trend_data.get('Đắk Lắk', [])}, borderColor: '#f59e0b', backgroundColor: '#f59e0b', tension: 0.3, fill: false, datalabels: {{ align: 'top', offset: 2 }} }},
        {{ label: 'Gia Lai', data: {opr_trend_data.get('Gia Lai', [])}, borderColor: '#10b981', backgroundColor: '#10b981', tension: 0.3, fill: false, datalabels: {{ align: 'top', offset: 2 }} }},
        {{ label: 'Phú Yên', data: {opr_trend_data.get('Phú Yên', [])}, borderColor: '#8b5cf6', backgroundColor: '#8b5cf6', tension: 0.3, fill: false, datalabels: {{ align: 'top', offset: 2 }} }},
        {{ label: 'Vùng TNG', data: {opr_trend_data.get('Vùng TNG', [])}, borderColor: '#ef4444', backgroundColor: '#ef4444', borderDash: [5, 5], tension: 0.3, fill: false, borderWidth: 3, datalabels: {{ align: 'bottom', offset: 4, font: {{ weight: 'bold' }} }} }}
      ]
    }},
    options: {{ 
      responsive: true, maintainAspectRatio: false, 
      plugins: {{ 
        legend: {{ position: 'bottom' }},
        datalabels: {{ 
          display: true,
          color: (ctx) => ctx.dataset.borderColor,
          font: {{ size: 10, weight: '700' }},
          formatter: v => v + '%'
        }}
      }},
      scales: {{ 
        y: {{ beginAtZero: false, ticks: {{ callback: v => v + '%' }} }},
        x: {{ ticks: {{ }} }}
      }}
    }}
  }});
}}

function initKDChart(){{
  new Chart(document.getElementById('chartKD'),{{
    type:'bar',
    plugins: [ChartDataLabels],
    data:{{
      labels:{kd_am_labels},
      datasets:[
        {{label:'Cùng kỳ T4',data:{kd_cungky},backgroundColor:'#94a3b8',borderRadius:4}},
        {{label:'Lũy kế T5',data:{kd_luyke},backgroundColor:'#0284c7',borderRadius:4}}
      ]
    }},
    options:{{
      responsive:true,maintainAspectRatio:false,
      scales:{{
        y:{{beginAtZero:true,title:{{display:true,text:'Triệu VNĐ',font:{{weight:800}}}}}},
        x:{{ticks:{{}}}}
      }},
      plugins:{{
        legend:{{position:'top', labels: {{ font: {{ size: 12 }} }} }},
        datalabels: {{
          display: true,
          anchor: 'end',
          align: 'top',
          color: (ctx) => ctx.dataset.backgroundColor,
          font: {{ weight: 'bold', size: 10 }},
          formatter: (v) => Math.round(v) || ''
        }}
      }}
    }}
  }});
}}

function initKDTrendChart(){{
  new Chart(document.getElementById('chartKDTrend'), {{
    type: 'line',
    plugins: [ChartDataLabels],
    data: {{
      labels: {kd_trend_dates_js},
      datasets: [{{
        label: 'Doanh thu',
        data: {kd_trend_data_js}.map(v => parseFloat((v/1000000).toFixed(1))),
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        borderWidth: 3,
        fill: true,
        tension: 0.4,
        pointRadius: 4,
        pointBackgroundColor: '#10b981',
        datalabels: {{
          align: 'top',
          anchor: 'end',
          display: true,
          color: '#0f172a',
          font: {{ weight: '800', size: 11 }},
          formatter: (v) => v + 'M',
          offset: 8
        }}
      }}]
    }},
    options: {{
      responsive: true, maintainAspectRatio: false,
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{
          callbacks: {{
            label: (ctx) => 'Doanh thu: ' + ctx.parsed.y + ' triệu đ'
          }}
        }}
      }},
      scales: {{
        y: {{
          beginAtZero: true,
          grace: '15%',
          title: {{ display: true, text: 'Triệu VNĐ', font: {{ weight: 800 }} }}
        }},
        x: {{ ticks: {{ }} }}
      }}
    }}
  }});
}}

function initNSChart(){{
  new Chart(document.getElementById('chartNS'),{{
    type:'bar',
    plugins: [ChartDataLabels],
    data:{{
      labels:{ns_chart_labels},
      datasets:[
        {{label:'Định biên',data:{ns_chart_can},backgroundColor:'#cbd5e1',borderRadius:4}},
        {{label:'Có',data:{ns_chart_co},backgroundColor:'#0ea5e9',borderRadius:4}}
      ]
    }},
    options:{{
      responsive:true,maintainAspectRatio:false,
      scales:{{
        y:{{beginAtZero:true,stacked:false}},
        x:{{ticks:{{}}}}
      }},
      plugins:{{
        legend:{{position:'top', labels: {{ font: {{ size: 12 }} }} }},
        datalabels: {{
          display: true,
          anchor: 'end',
          align: 'top',
          color: '#475569',
          font: {{ weight: 'bold', size: 10 }},
          formatter: (v) => v || ''
        }}
      }}
    }}
  }});
}}

const _db = {json.dumps(data, ensure_ascii=False)};
</script>


<!-- ELITE AI CHATBOT V10.0 -->
<div class="trinh-launcher" onclick="toggleTrinh()"></div>
<div class="trinh-window" id="trinhWin">
    <div class="trinh-header">
        <div class="trinh-avatar-small"></div>
        <div class="trinh-header-info">
            <h3>Trợ Lý Ngọc Trinh</h3>
            <p><span class="trinh-status-dot"></span> Cố vấn vận hành cao cấp</p>
        </div>
        <div style="margin-left:auto; display:flex; align-items:center; gap:8px;">
            <button onclick="toggleTrinh()" style="background:none; border:none; color:#cbd5e1; font-size:28px; cursor:pointer; line-height:1;">&times;</button>
        </div>
    </div>
    <div class="trinh-messages" id="trinhMsgs">
        <div class="trinh-msg bot">Chào Sếp!<br>Em Ngọc Trinh- Trợ lý của Sếp đây ạ.<br>Sếp cần em phân tích các số liệu nào của Vùng Tây Nguyên thì cứ bảo em nhé! 💋</div>
    </div>
    <div class="trinh-typing" id="trinhTyping">Ngọc Trinh đang phân tích...</div>
    <div class="trinh-suggestions">
        <button onclick="sendSuggestion('💎 Tổng quan Vùng')">💎 Tổng quan Vùng</button>
        <button onclick="sendSuggestion('🔥 Top 5 BC tệ')">🔥 Top 5 BC tệ</button>
        <button onclick="sendSuggestion('👥 Phân tích NS')">👥 Phân tích NS</button>
        <button onclick="sendSuggestion('🚨 Điểm nóng')">🚨 Điểm nóng</button>
        <button onclick="sendSuggestion('📊 Báo cáo OPR')">📊 Báo cáo OPR</button>
        <button onclick="sendSuggestion('☀️ Tình hình thời tiết')">☀️ Tình hình thời tiết</button>
    </div>
    <div id="filePreview" class="trinh-file-preview" style="display:none"></div>
    <div class="trinh-input-area">
        <label for="trinhFile" class="trinh-attach-btn" title="Đính kèm hình ảnh/file">
            <span>📎</span>
        </label>
        <input type="file" id="trinhFile" style="display:none" onchange="handleFileSelect(this)" multiple accept="image/*,application/pdf,.doc,.docx,.xls,.xlsx,.txt,.csv">
        <input type="text" class="trinh-input" id="trinhInp" placeholder="Nhắn cho Ngọc Trinh trợ lý của sếp..." onkeypress="if(event.key==='Enter') sendToTrinh()">
        <button class="trinh-send" onclick="sendToTrinh()">
            <span>🚀</span>
        </button>
    </div>
</div>

<script>
let trinhHistory = [];
let selectedFiles = [];
let activeChatBaseUrl = '';
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' || window.location.protocol === 'file:' || !window.location.hostname) {{
    activeChatBaseUrl = 'http://127.0.0.1:5005';
}} else {{
    activeChatBaseUrl = (typeof BOT_URL !== 'undefined' && BOT_URL) ? BOT_URL : 'http://127.0.0.1:5005';
}}

// Tự động đánh thức Ngọc Trinh qua cổng 5001 khi mở dashboard/link online
async function wakeupNgocTrinh() {{
    try {{
        const response = await fetch('http://127.0.0.1:5001/wakeup', {{ method: 'GET', mode: 'cors' }});
        const data = await response.json();
        if (data.status === 'success' && data.bot_url) {{
            if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1' && window.location.protocol !== 'file:' && window.location.hostname !== '') {{
                activeChatBaseUrl = data.bot_url;
            }}
            console.log("🌸 Ngọc Trinh đã thức giấc và kết nối qua: " + activeChatBaseUrl);
        }}
    }} catch(e) {{
        console.warn("⚠️ Không thể đánh thức Ngọc Trinh qua cổng local 5001. Có thể remote_server.py chưa chạy.");
    }}
}}
wakeupNgocTrinh();


function showKeySetupCard() {{
    const box = document.getElementById('trinhMsgs');
    if (document.getElementById('trinhKeyCard')) return;
    
    const cardHtml = `
        <div class="trinh-key-card" id="trinhKeyCard">
            <div class="trinh-key-title">
                🔑 Cấu Hình API Key Ngọc Trinh
            </div>
            <div style="font-size:12px; color:#475569; line-height:1.4;">
                Sếp ơi, để em có thể hoạt động, Sếp vui lòng nhập mã <b>Gemini API Key</b> vào đây nhé. Key sẽ được lưu bảo mật trong file <code>GOOGLE_API_KEY.txt</code> trên máy của Sếp và tuyệt đối KHÔNG bị đẩy lên GitHub.
            </div>
            <div class="trinh-key-input-container">
                <input type="password" id="trinhKeyInput" class="trinh-key-input" placeholder="Dán Gemini API Key tại đây...">
                <button onclick="saveGeminiKey()" id="trinhKeySaveBtn" class="trinh-key-save-btn">Lưu Key</button>
            </div>
            <div id="trinhKeyStatus" style="font-size:11px; color:#be123c; display:none; margin-top: -4px;"></div>
        </div>
    `;
    box.innerHTML += cardHtml;
    box.scrollTop = box.scrollHeight;
}}

async function saveGeminiKey() {{
    const input = document.getElementById('trinhKeyInput');
    const status = document.getElementById('trinhKeyStatus');
    const btn = document.getElementById('trinhKeySaveBtn');
    const key = input.value.trim();
    
    if (!key) {{
        status.textContent = "Sếp chưa nhập Key kìa!";
        status.style.display = "block";
        return;
    }}
    
    btn.disabled = true;
    btn.textContent = "Đang lưu...";
    status.style.display = "none";
    
    let targetBaseUrl = activeChatBaseUrl;
    
    try {{
        const response = await fetch(`${{targetBaseUrl}}/save_key`, {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ key: key }})
        }});
        const data = await response.json();
        if (data.status === 'success') {{
            status.textContent = "Lưu Key thành công! Đang tải lại trợ lý...";
            status.style.color = "#22c55e";
            status.style.display = "block";
            
            setTimeout(() => {{
                const card = document.getElementById('trinhKeyCard');
                if (card) card.remove();
                
                const box = document.getElementById('trinhMsgs');
                box.innerHTML += `<div class="trinh-msg bot">✅ Em đã nhận được API Key và sẵn sàng phục vụ Sếp rồi ạ! Sếp có thể tiếp tục hỏi em nhé.</div>`;
                box.scrollTop = box.scrollHeight;
            }}, 1500);
        }} else {{
            status.textContent = "Lỗi: " + data.response;
            status.style.display = "block";
            btn.disabled = false;
            btn.textContent = "Lưu Key";
        }}
    }} catch(e) {{
        console.error("Error saving key to active url:", e);
        if (targetBaseUrl !== 'http://127.0.0.1:5005') {{
            try {{
                const response = await fetch('http://127.0.0.1:5005/save_key', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ key: key }})
                }});
                const data = await response.json();
                if (data.status === 'success') {{
                    activeChatBaseUrl = 'http://127.0.0.1:5005';
                    status.textContent = "Lưu Key thành công! Đang tải lại trợ lý...";
                    status.style.color = "#22c55e";
                    status.style.display = "block";
                    setTimeout(() => {{
                        const card = document.getElementById('trinhKeyCard');
                        if (card) card.remove();
                        const box = document.getElementById('trinhMsgs');
                        box.innerHTML += `<div class="trinh-msg bot">✅ Em đã nhận được API Key và sẵn sàng phục vụ Sếp rồi ạ! Sếp có thể tiếp tục hỏi em nhé.</div>`;
                        box.scrollTop = box.scrollHeight;
                    }}, 1500);
                    return;
                }}
            }} catch(localErr) {{
                console.error("Local save fallback failed:", localErr);
            }}
        }}
        status.textContent = "Không thể kết nối tới chat service để lưu key. Sếp hãy chắc chắn chat_service.py đã được chạy.";
        status.style.display = "block";
        btn.disabled = false;
        btn.textContent = "Lưu Key";
    }}
}}

function toggleTrinh() {{
    const win = document.getElementById('trinhWin');
    win.style.display = win.style.display === 'flex' ? 'none' : 'flex';
    if(win.style.display === 'flex') document.getElementById('trinhInp').focus();
}}

function handleFileSelect(input) {{
    const files = Array.from(input.files);
    const preview = document.getElementById('filePreview');
    
    files.forEach(file => {{
        if (selectedFiles.length >= 3) return;
        selectedFiles.push(file);
        
        const reader = new FileReader();
        reader.onload = (e) => {{
            preview.style.display = 'flex';
            const div = document.createElement('div');
            div.className = 'preview-item';
            const index = selectedFiles.length - 1;
            if (file.type.startsWith('image/')) {{
                div.innerHTML = `<img src="${{e.target.result}}"><div class="remove-file" onclick="removeFile(this, ${{index}})">&times;</div>`;
            }} else if (file.type === 'application/pdf') {{
                div.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;font-size:20px">📕</div><div class="remove-file" onclick="removeFile(this, ${{index}})">&times;</div>`;
            }} else if (file.name.endsWith('.doc') || file.name.endsWith('.docx')) {{
                div.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;font-size:20px">📘</div><div class="remove-file" onclick="removeFile(this, ${{index}})">&times;</div>`;
            }} else if (file.name.endsWith('.xls') || file.name.endsWith('.xlsx') || file.name.endsWith('.csv')) {{
                div.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;font-size:20px">📗</div><div class="remove-file" onclick="removeFile(this, ${{index}})">&times;</div>`;
            }} else {{
                div.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;height:100%;font-size:20px">📄</div><div class="remove-file" onclick="removeFile(this, ${{index}})">&times;</div>`;
            }}
            preview.appendChild(div);
        }};
        reader.readAsDataURL(file);
    }});
    input.value = '';
}}

function removeFile(el, index) {{
    selectedFiles.splice(index, 1);
    el.parentElement.remove();
    if (selectedFiles.length === 0) {{
        document.getElementById('filePreview').style.display = 'none';
    }}
}}

function sendSuggestion(text) {{
    document.getElementById('trinhInp').value = text;
    sendToTrinh();
}}

async function sendToTrinh() {{
    const inp = document.getElementById('trinhInp');
    const msg = inp.value.trim();
    if(!msg && selectedFiles.length === 0) return;

    const box = document.getElementById('trinhMsgs');
    const userMsgHtml = msg ? msg : (selectedFiles.length > 0 ? "<i>Đã gửi " + selectedFiles.length + " tệp đính kèm</i>" : "");
    box.innerHTML += `<div class="trinh-msg user">${{userMsgHtml}}</div>`;
    inp.value = '';
    box.scrollTop = box.scrollHeight;

    // Convert files to base64
    const filePromises = selectedFiles.map(file => {{
        return new Promise((resolve) => {{
            const reader = new FileReader();
            reader.onload = (e) => {{
                resolve({{
                    data: e.target.result.split(',')[1],
                    mime_type: file.type
                }});
            }};
            reader.readAsDataURL(file);
        }});
    }});
    
    const base64Files = await Promise.all(filePromises);
    
    // Clear selection
    selectedFiles = [];
    document.getElementById('filePreview').innerHTML = '';
    document.getElementById('filePreview').style.display = 'none';

    document.getElementById('trinhTyping').style.display = 'block';

    let response;
    let data;
    try {{
        response = await fetch(`${{activeChatBaseUrl}}/chat`, {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ 
                message: msg || "Phân tích file đính kèm này giúp Sếp", 
                history: trinhHistory,
                files: base64Files
            }})
        }});
        data = await response.json();
    }} catch(err) {{
        console.warn("Primary chat connection failed. Attempting fallback...", err);
        if (activeChatBaseUrl !== 'http://127.0.0.1:5005') {{
            try {{
                activeChatBaseUrl = 'http://127.0.0.1:5005';
                response = await fetch(`${{activeChatBaseUrl}}/chat`, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ 
                        message: msg || "Phân tích file đính kèm này giúp Sếp", 
                        history: trinhHistory,
                        files: base64Files
                    }})
                }});
                data = await response.json();
            }} catch(fallbackErr) {{
                console.error("Fallback chat connection failed as well.", fallbackErr);
                document.getElementById('trinhTyping').style.display = 'none';
                box.innerHTML += `<div class="trinh-msg bot" style="color:red">Không thể kết nối tới máy chủ (cả online và local). Sếp vui lòng khởi chạy <code>chat_service.py</code> và thử lại nhé!</div>`;
                box.scrollTop = box.scrollHeight;
                return;
            }}
        }} else {{
            document.getElementById('trinhTyping').style.display = 'none';
            box.innerHTML += `<div class="trinh-msg bot" style="color:red">Không thể kết nối tới local chat service (http://127.0.0.1:5005). Sếp vui lòng kiểm tra xem <code>chat_service.py</code> đã được khởi chạy chưa nhé!</div>`;
            box.scrollTop = box.scrollHeight;
            return;
        }}
    }}

    document.getElementById('trinhTyping').style.display = 'none';
    
    if(data.status === 'success') {{
        const botMsg = data.response;
        const formatted = botMsg
            .replace(/<\\/div>\\n/g, '</div>')
            .replace(/\\n\\n/g, '<br>')
            .replace(/\\n/g, '<br>')
            .replace(/\\*\\*(.*?)\\*\\*/g, '<b>$1</b>')
            .replace(/^- (.*)$/gm, '• $1');
        box.innerHTML += `<div class="trinh-msg bot">${{formatted}}</div>`;
        trinhHistory.push({{role: 'user', content: msg || "Phân tích file đính kèm"}});
        trinhHistory.push({{role: 'model', content: botMsg}});
    }} else {{
        box.innerHTML += `<div class="trinh-msg bot" style="color:red">Lỗi: ${{data.response}}</div>`;
        if (data.response && data.response.includes('GOOGLE_API_KEY.txt')) {{
            showKeySetupCard();
        }}
    }}
    box.scrollTop = box.scrollHeight;
    lucide.createIcons();
}}

const provinceData = {{
  gialai: {{
    name: "Gia Lai",
    capital: "Pleiku",
    hubs: 15,
    am: "{gialai_am}",
    target: "{gialai_gtc_avg}",
    staff: "{gialai_ns}",
    volPct: "{gialai_vol_pct}",
    challenges: "Địa hình đồi dốc, khoảng cách bưu cục xa nhau, ảnh hưởng bởi mùa mưa Tây Nguyên.",
    focus: "Tối ưu hóa lịch tải nội tỉnh và mở mạng lưới bưu cục tại các tuyến huyện chành"
  }},
  daklak: {{
    name: "Đắk Lắk",
    capital: "Buôn Ma Thuột",
    hubs: 24,
    am: "{daklak_am}",
    target: "{daklak_gtc_avg}",
    staff: "{daklak_ns}",
    volPct: "{daklak_vol_pct}",
    challenges: "Volume đơn hàng cao, đặc thù mùa vụ nông sản lớn: cà phê, sầu riêng, tiêu...",
    focus: "Ổn định định biên nhân sự giao hàng và xử lý hàng ca 2 đối với các bưu cục trung tâm"
  }},
  binhdinh: {{
    name: "Bình Định",
    capital: "Quy Nhơn",
    hubs: 16,
    am: "{binhdinh_am}",
    target: "{binhdinh_gtc_avg}",
    staff: "{binhdinh_ns}",
    volPct: "{binhdinh_vol_pct}",
    challenges: "Dải địa hình ven biển kéo dài, mật độ đơn hàng tập trung đông tại Quy Nhơn.",
    focus: "Đẩy nhanh thời gian giao hàng và tối ưu năng suất nhân sự xử lý (NVXL)."
  }},
  phuyen: {{
    name: "Phú Yên",
    capital: "Tuy Hòa",
    hubs: 10,
    am: "{phuyen_am}",
    target: "{phuyen_gtc_avg}",
    staff: "{phuyen_ns}",
    volPct: "{phuyen_vol_pct}",
    challenges: "Địa hình kết hợp núi-biển hiểm trở ở các huyện vùng sâu, mật độ đơn hàng thấp.",
    focus: "Tăng tỷ lệ GTC và cải thiện chỉ số thời gian giao hàng (ODR) khu vực ngoại vi."
  }}
}};

function selectProvince(id) {{
  document.querySelectorAll('.map-pin').forEach(el => {{
    el.classList.toggle('active-pin', el.getAttribute('data-id') === id);
  }});
  
  const data = provinceData[id];
  if (!data) return;
  
  document.getElementById('prov-name').innerText = data.name.toUpperCase();
  document.getElementById('prov-capital').innerText = data.capital;
  document.getElementById('prov-hubs').innerText = data.hubs + " Bưu cục";
  document.getElementById('prov-am').innerText = data.am;
  document.getElementById('prov-target').innerText = data.target;
  document.getElementById('prov-staff').innerText = data.staff + " nhân sự";
  document.getElementById('prov-vol-pct').innerText = data.volPct;
  document.getElementById('prov-challenges').innerText = data.challenges;
  document.getElementById('prov-focus').innerText = data.focus;
}}

lucide.createIcons();
</script>
</body>
</html>'''

    with open('dashboard.html', 'w', encoding='utf-8') as f:
        f.write(html)
    with open('app.html', 'w', encoding='utf-8') as f:
        f.write(html)
print(f"Dashboard created! Size: {len(html)} bytes")

# Tự động đồng bộ lên GitHub Pages ngay khi build xong
try:
    import sync_to_github
    sync_to_github.sync()
except Exception as e:
    print(f"⚠️ Không thể đồng bộ GitHub: {e}")
