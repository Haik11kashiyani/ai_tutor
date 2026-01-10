import os
import random
from youtube_automation import YouTubeAutomation

# Dummy data for testing
day_data = {
    "day": 1,
    "title": "Print Hello World",
    "language": "python",
    "code": "print('Hello, World!')",
    "explanation": "This is a test explanation."
}

def test_metadata():
    print(f"🔑 Checking API Key: {'FOUND' if os.getenv('GOOGLE_AI_API_KEY') else 'MISSING'}")
    
    automation = YouTubeAutomation()
    print("\n🔄 Generating Content Attributes...\n")
    
    # Test Theme
    theme = automation.generate_dynamic_theme(day_data['title'])
    print(f"🎨 THEME ({theme.get('name')}): BG1={theme.get('bg1')} ACCENT={theme.get('accent')}")

    # Test Script
    script = automation.generate_script(day_data)
    print(f"🎙️ SCRIPT (First 100 chars): {script[:100]}...")

    # Test Metadata
    metadata = automation.generate_youtube_metadata(day_data)
    
    print("-" * 50)
    print(f"TITLE: {metadata['title']}")
    print("-" * 50)
    print(f"DESCRIPTION:\n{metadata['description'][:200]}...")
    print("-" * 50)
    print(f"TAGS: {metadata['tags']}")
    print("-" * 50)
    
    if "#shorts" in metadata['title'].lower() and "#viral" in metadata['title'].lower():
        print("✅ SUCCESS: Title contains viral tags.")
    else:
        print("❌ FAILURE: Title missing viral tags.")

if __name__ == "__main__":
    # Ensure dependencies are available (simple check)
    try:
        import google.generativeai
        print("✅ google-generativeai installed")
    except ImportError:
        print("⚠️ google-generativeai NOT installed. Installing...")
        os.system("pip install google-generativeai")
        
    test_metadata()
