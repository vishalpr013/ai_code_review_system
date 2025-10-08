#!/usr/bin/env python3
"""
Startup script for AI Code Review Assistant
Handles both development and production modes with React integration
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]} is compatible")

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import flask
        import requests
        import google.generativeai
        import pydantic
        print("✅ Core dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False

def install_dependencies():
    """Install dependencies from requirements.txt."""
    print("📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_env_file():
    """Check if .env file exists."""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  .env file not found")
        print("📝 Please copy .env.example to .env and configure your settings")
        return False
    print("✅ .env file found")
    return True

def validate_env_config():
    """Validate environment configuration."""
    from dotenv import load_dotenv
    
    load_dotenv()
    
    required_vars = [
        "GEMINI_API_KEY",
        "GERRIT_HOST",
        "GERRIT_USERNAME",
        "GERRIT_PASSWORD"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ Environment configuration is valid")
    return True

def create_directories():
    """Create necessary directories."""
    directories = ["logs"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    print("✅ Directories created")

def main():
    """Main setup and start function."""
    print("🤖 Automated Code Review System - Quick Start")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    
    # Install dependencies if needed
    if not check_dependencies():
        if not install_dependencies():
            sys.exit(1)
    
    # Check environment configuration
    if not check_env_file():
        sys.exit(1)
    
    # Validate configuration
    if not validate_env_config():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    print("\n🚀 Starting the automated code review system...")
    print("📋 Available endpoints:")
    print("   GET  /health       - Health check")
    print("   GET  /status       - System status")
    print("   POST /webhook      - Gerrit webhook")
    print("   POST /manual-review - Manual review trigger")
    print("\n🌐 Server will start on http://localhost:5000")
    print("📊 Check http://localhost:5000/health for system status")
    print("\n" + "=" * 50)
    
    # Start the main application
    try:
        from src.main import main as start_app
        start_app()
    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
