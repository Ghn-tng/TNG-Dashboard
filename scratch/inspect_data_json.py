import json
import os

def inspect():
    if os.path.exists('data.json'):
        with open('data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        print("KEYS:")
        for k in data.keys():
            v = data[k]
            if isinstance(v, dict):
                print(f"- {k} (dict): keys = {list(v.keys())[:10]}")
            elif isinstance(v, list):
                print(f"- {k} (list): length = {len(v)}, sample = {v[0] if len(v) > 0 else 'empty'}")
            else:
                print(f"- {k} ({type(v).__name__}): {v}")
    else:
        print("data.json not found")

if __name__ == "__main__":
    inspect()
