import google.generativeai as genai
import os

def test_all_keys():
    try:
        with open('GOOGLE_API_KEY.txt', 'r') as f:
            keys = [k.strip() for k in f.readlines() if k.strip()]
        
        models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro']
        
        for i, key in enumerate(keys):
            print(f"Testing key {i+1}: {key[:10]}...")
            genai.configure(api_key=key)
            success = False
            for model_name in models_to_try:
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content("Hi", generation_config={"max_output_tokens": 5})
                    print(f"  ✅ Key {i+1} OK with {model_name}: {response.text.strip()}")
                    success = True
                    break
                except Exception as e:
                    # print(f"  - {model_name} failed")
                    pass
            if not success:
                print(f"  ❌ Key {i+1} Failed on all models.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_all_keys()
