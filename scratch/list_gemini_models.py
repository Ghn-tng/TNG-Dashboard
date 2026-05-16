import google.generativeai as genai
import os

with open('/Users/macbook/Downloads/GHN/GOOGLE_API_KEY.txt', 'r') as f:
    key = f.readline().strip()

genai.configure(api_key=key)

print(f"Checking models for key ending in ...{key[-4:]}")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error: {e}")
