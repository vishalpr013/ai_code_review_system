#!/usr/bin/env python3
"""
Quick script to list available Gemini models
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    import google.generativeai as genai
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment")
        sys.exit(1)
    
    print(f"🔑 Using API key: {api_key[:10]}...{api_key[-10:]}")
    
    # Configure Gemini
    genai.configure(api_key=api_key)
    
    print("📋 Available Gemini models:")
    print("-" * 50)
    
    models = genai.list_models()
    count = 0
    for model in models:
        if 'generateContent' in model.supported_generation_methods:
            print(f"✅ {model.name}")
            print(f"   Display Name: {model.display_name}")
            print(f"   Description: {model.description}")
            print()
            count += 1
    
    print(f"Found {count} models that support generateContent")
    
    if count > 0:
        print("\n💡 Try using one of these model names in your .env file:")
        models = genai.list_models()
        for model in models:
            if 'generateContent' in model.supported_generation_methods:
                model_name = model.name.replace('models/', '')
                print(f"   GEMINI_MODEL={model_name}")
                break

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
