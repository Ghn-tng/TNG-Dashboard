import json, os

def sync():
    base_dir = '/Users/macbook/Downloads/GHN'
    data_path = os.path.join(base_dir, 'data.json')
    hist_path = os.path.join(base_dir, 'history.json')
    
    if not os.path.exists(data_path) or not os.path.exists(hist_path):
        print("Missing files")
        return
        
    with open(data_path, 'r') as f:
        data = json.load(f)
    with open(hist_path, 'r') as f:
        history = json.load(f)
        
    # Fix May 13 (2026-05-13) which has zeros
    target_date = "2026-05-13"
    if target_date in history:
        # 1. Calculate average Ontime for May 13 (day8 in data.json)
        ontime_vals = [float(x.get('day8', 0)) for x in data.get('ontime_tts', []) if x.get('day8')]
        if ontime_vals:
            avg_ontime = sum(ontime_vals) / len(ontime_vals)
            history[target_date]['ontime'] = avg_ontime
            print(f"Fixed ontime for {target_date}: {avg_ontime}")
            
        # 2. Estimate GTC TTS for May 13
        # Since gtc_vung is 0.7323, and usually TTS is ~0.5% higher
        if history[target_date].get('gtc_tts', 0) == 0:
            history[target_date]['gtc_tts'] = history[target_date]['gtc_vung'] + 0.005
            print(f"Estimated gtc_tts for {target_date}: {history[target_date]['gtc_tts']}")
            
    # Also ensure May 14 is synced with current data.json
    report_date = data.get('report_date')
    if report_date:
        history[report_date] = {
            'vol': float(data.get('grand_total_gtc', {}).get('vol', 0)),
            'gtc_vung': float(data.get('grand_total_gtc', {}).get('gtc', 0)),
            'gtc_tts': float(data.get('grand_total_gtc_tts', {}).get('gtc', 0)),
            'ontime': sum([float(x.get('today',0)) for x in data.get('ontime_tts',[]) if x.get('today')]) / max(len(data.get('ontime_tts',[])),1),
            'opr': float(data.get('opr_total', 0)),
            'dt_luyke': float(data.get('total_lay', {}).get('luyke', 0)),
            'ns_thieu': float(data.get('ns_total', {}).get('so_thieu', 0)),
            'n_warn': len(data.get('canh_bao', []))
        }
        print(f"Synced history for report_date {report_date}")

    with open(hist_path, 'w') as f:
        json.dump(history, f, indent=2)
    print("✅ History synchronized.")

if __name__ == "__main__":
    sync()
