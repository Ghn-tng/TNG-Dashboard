import google.generativeai as genai
import sys

try:
    with open('GOOGLE_API_KEY.txt', 'r') as f:
        key = f.readline().strip()
    genai.configure(api_key=key)
    # List models to see what's available
    print("Available models:")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error: {e}")
