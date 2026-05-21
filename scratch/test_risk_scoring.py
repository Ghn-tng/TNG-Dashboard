import json

with open('data.json', 'r') as f:
    data = json.load(f)

def safe_num(v):
    try: return float(v) if v else 0
    except: return 0

def pct(v):
    return f"{v*100:.1f}%"

# 1. Data Consolidation & Risk Scoring
bc_metrics = {}

# GTC Hôm nay
for x in data.get('gtc_bc', []):
    bc = x.get('bc', '')
    if not bc or 'Tổng' in bc or bc == 'Grand Total': continue
    bc_metrics[bc] = {
        'am': x.get('am', 'N/A'),
        'gtc': safe_num(x.get('total_gtc', 1)),
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
    bc = x.get('am', '') # bc name is stored in 'am' field here
    if bc in bc_metrics:
        bc_metrics[bc]['odr'] = safe_num(x.get('today', 1))

# NS (Nhân sự)
for x in data.get('ns_bc', []):
    bc = x.get('bc', '')
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
    if m['gtc'] < 0.75:
        m['risk_score'] += 3
        m['issues'].append(f"GTC cực thấp ({pct(m['gtc'])})")
    elif m['gtc'] < 0.80:
        m['risk_score'] += 1
        m['issues'].append(f"GTC thấp ({pct(m['gtc'])})")
        
    if m['odr'] < 0.90:
        m['risk_score'] += 2
        m['issues'].append(f"ODR trễ ({pct(m['odr'])})")
        
    if m['ns_thieu'] >= 2:
        m['risk_score'] += 3
        m['issues'].append(f"Thiếu {m['ns_thieu']} NS")
        
    if m['gap'] < -0.05:
        m['risk_score'] += 3
        m['issues'].append(f"Trend giảm sâu ({pct(m['gap'])})")
    elif m['gap'] < 0:
        m['risk_score'] += 1
        m['issues'].append(f"Trend giảm ({pct(m['gap'])})")

# Sort by Risk Score desc, then GTC asc
sorted_bcs = sorted(bc_metrics.items(), key=lambda item: (-item[1]['risk_score'], item[1]['gtc']))

print("TOP 5 HOTSPOTS:")
for bc, m in sorted_bcs[:5]:
    if m['risk_score'] > 0:
        print(f"{bc} (AM {m['am']}) - Score: {m['risk_score']} - Issues: {', '.join(m['issues'])}")
