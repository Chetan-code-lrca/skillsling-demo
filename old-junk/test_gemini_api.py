#!/usr/bin/env python3
"""
Quick test to verify Gemini API works correctly
Run: python test_gemini_api.py
"""

import os
import google.generativeai as genai

# Get API key
GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY")

if not GEMINI_API_KEY:
    print("❌ GOOGLE_API_KEY environment variable not set!")
    exit(1)

print("✅ API Key found")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY, transport='rest')

# Test model availability
test_models = ["gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-pro"]

for model_name in test_models:
    print(f"\n📝 Testing {model_name}...")
    try:
        model = genai.GenerativeModel(
            model_name,
            system_instruction="You are a helpful tutor. Keep responses concise."
        )
        
        # Test with chat interface (like the app does)
        chat = model.start_chat(history=[])
        response = chat.send_message("What is 2+2?")
        
        print(f"✅ {model_name} works!")
        print(f"   Response: {response.text[:100]}...")
        break
        
    except Exception as e:
        print(f"❌ {model_name} failed: {str(e)[:100]}")
        continue

print("\n✅ Gemini API test complete!")
