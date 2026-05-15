import google.generativeai as genai
import sys

try:
    key = "***REMOVED***"
    genai.configure(api_key=key)
    # List models to see what's available
    print("Available models:")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error: {e}")
