import google.generativeai as genai
import os

def get_api_key():
    try:
        with open(".streamlit/secrets.toml", "r") as f:
            for line in f:
                if "GOOGLE_API_KEY" in line:
                    return line.split('"')[1]
    except:
        return None

api_key = get_api_key()
if api_key:
    genai.configure(api_key=api_key)
    print("Available models:")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(m.name)
    except Exception as e:
        print(f"Error listing models: {e}")
else:
    print("Could not find API key")
