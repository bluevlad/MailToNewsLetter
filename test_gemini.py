import os
import yaml
import google.generativeai as genai

def load_config():
    with open('config/settings.yaml', 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def main():
    config = load_config()
    gemini_config = config.get('gemini', {})
    model_name = gemini_config.get('model', 'gemini-pro')
    
    api_key = os.getenv('GOOGLE_API_KEY')
    
    if not api_key:
        print("❌ Error: GOOGLE_API_KEY environment variable is not set.")
        print("Please set your Google API Key in the environment variables.")
        print("Example (PowerShell): $env:GOOGLE_API_KEY='your_api_key_here'")
        return

    print(f"✅ API Key found.")
    print(f"🔄 Configuring Gemini with model: {model_name}...")
    
    genai.configure(api_key=api_key)
    
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Hello! Are you working correctly?")
        print("\n🤖 Gemini Response:")
        print(response.text)
        print("\n✅ Integration Successful!")
    except Exception as e:
        print(f"\n❌ Error connecting to Gemini API:\n{e}")

if __name__ == "__main__":
    main()
