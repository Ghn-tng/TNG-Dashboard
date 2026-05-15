import json
import os

def update_history_final():
    history = {}
    if os.path.exists('history.json'):
        with open('history.json', 'r', encoding='utf-8') as f:
            history = json.load(f)
            
    # Update 10/05 with user's verified screenshot numbers
    history['2026-05-10'] = {
        "vol": 56756,
        "gtc_vung": 0.6723,
        "gtc_tts": 0.682,
        "ontime": 0.948,
        "opr": 0.832,
        "dt_luyke": 1301941218.0,
        "ns_thieu": 30.0, # Kept from previous
        "n_warn": 1 # Kept from previous
    }
    
    # Save
    with open('history.json', 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    
    print("✅ History updated with 10/05 verified screenshot data.")

if __name__ == "__main__":
    update_history_final()
