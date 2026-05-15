import google.generativeai as genai
import os

KEYS_FILE = 'GOOGLE_API_KEY.txt'
if os.path.exists(KEYS_FILE):
    with open(KEYS_FILE, 'r') as f:
        keys = [line.strip() for line in f if line.strip()]
        if keys:
            genai.configure(api_key=keys[0])
            try:
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        print(m.name)
            except Exception as e:
                print(f"Error: {e}")
else:
    print("No API key found.")
