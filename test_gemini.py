import google.generativeai as genai
import os

# Try to get API Key from environment or secrets file
# Note: Streamlit secrets are not available here, so we check env var or ask user to set it.
api_key = os.environ.get("GOOGLE_API_KEY")

if not api_key:
    # Try to read from .streamlit/secrets.toml manually for testing
    try:
        with open(".streamlit/secrets.toml", "r") as f:
            for line in f:
                if "GOOGLE_API_KEY" in line:
                    api_key = line.split("=")[1].strip().strip('"').strip("'")
                    break
    except FileNotFoundError:
        pass

if not api_key or api_key == "YOUR_API_KEY_HERE":
    print("❌ API Key not found or not set. Please set GOOGLE_API_KEY in .streamlit/secrets.toml")
else:
    print(f"✅ API Key found: {api_key[:5]}...{api_key[-5:]}")
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Hello, are you working?")
        print(f"✅ Gemini Response: {response.text}")
    except Exception as e:
        print(f"❌ Error calling Gemini API: {e}")
