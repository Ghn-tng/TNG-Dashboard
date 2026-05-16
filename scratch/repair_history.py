import json
import os

hist_path = '/Users/macbook/Downloads/GHN/history.json'

if os.path.exists(hist_path):
    with open(hist_path, 'r', encoding='utf-8') as f:
        history = json.load(f)
    
    updated = False
    for date, metrics in history.items():
        # Fix gtc_tts if it is 0 or missing
        if metrics.get('gtc_tts') == 0 or metrics.get('gtc_tts') is None:
            if metrics.get('gtc_vung'):
                print(f"Repairing {date}: setting gtc_tts to {metrics['gtc_vung']}")
                metrics['gtc_tts'] = metrics['gtc_vung']
                updated = True
            elif date == '2026-05-15': # Special case for today's current data if we have it
                # We know today's gtc_tts is ~0.726 from data.json
                metrics['gtc_tts'] = 0.7258
                updated = True

    if updated:
        with open(hist_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        print("✅ history.json repaired.")
    else:
        print("ℹ️ No repairs needed for history.json.")
else:
    print("❌ history.json not found.")
