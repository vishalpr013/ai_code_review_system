#!/usr/bin/env python3
"""
AI Code Review Assistant - Smart Startup Script
Automatically handles React frontend and Python backend setup
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

def print_banner():
    """Print application banner"""
    print("""
🤖 AI Code Review Assistant
═══════════════════════════════════════════════
✨ Professional React + Python code analysis tool
📊 16 comprehensive quality criteria
🚀 Powered by Google Gemini AI
═══════════════════════════════════════════════
""")

def check_react_build():
    """Check if React build exists"""
    build_path = Path(__file__).parent / 'frontend' / 'build'
    return build_path.exists() and (build_path / 'index.html').exists()

def build_react():
    """Build React application"""
    print("🔧 Building React frontend...")
    frontend_path = Path(__file__).parent / 'frontend'
    
    if not frontend_path.exists():
        print("❌ Frontend directory not found!")
        return False
    
    if not (frontend_path / 'node_modules').exists():
        print("📦 Installing React dependencies...")
        result = subprocess.run(['npm', 'install'], cwd=frontend_path, shell=True)
        if result.returncode != 0:
            print("❌ Failed to install React dependencies")
            return False
    
    print("⚛️ Building React app...")
    result = subprocess.run(['npm', 'run', 'build'], cwd=frontend_path, shell=True)
    if result.returncode != 0:
        print("❌ Failed to build React app")
        return False
    
    print("✅ React build completed successfully")
    return True

def check_python_deps():
    """Check if Python dependencies are installed"""
    try:
        import flask
        import flask_cors
        return True
    except ImportError:
        return False

def install_python_deps():
    """Install Python dependencies"""
    print("🐍 Installing Python dependencies...")
    try:
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', 
            'flask', 'flask-cors', 'pydantic', 'pydantic-settings',
            'google-generativeai', 'python-dotenv', 'requests'
        ], check=True)
        print("✅ Python dependencies installed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install Python dependencies")
        return False

def start_combined_server():
    """Start the combined React + Python server"""
    print("🚀 Starting AI Code Review Assistant...")
    print("🌐 Application will be available at: http://localhost:3001")
    
    # Give server time to start, then open browser
    def open_browser():
        time.sleep(3)
        webbrowser.open('http://localhost:3001')
    
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    try:
        subprocess.run([sys.executable, 'react_app.py'])
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")

def start_dev_mode():
    """Start in development mode (React dev server + Python API)"""
    print("🚀 Starting in development mode...")
    print("⚛️ React dev server: http://localhost:3000")
    print("🐍 Python API server: http://localhost:3001")
    
    frontend_path = Path(__file__).parent / 'frontend'
    
    # Start Python API server
    python_env = {**os.environ, 'FLASK_ENV': 'development'}
    python_process = subprocess.Popen([
        sys.executable, 'react_app.py'
    ], env=python_env)
    
    # Give Python server time to start
    time.sleep(2)
    
    # Start React dev server
    react_env = {
        **os.environ, 
        'BROWSER': 'none',
        'REACT_APP_API_URL': 'http://localhost:3001'
    }
    react_process = subprocess.Popen([
        'npm', 'start'
    ], cwd=frontend_path, shell=True, env=react_env)
    
    # Open browser
    time.sleep(3)
    webbrowser.open('http://localhost:3000')
    
    try:
        # Wait for both processes
        python_process.wait()
        react_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down development servers...")
        python_process.terminate()
        react_process.terminate()

def main():
    """Main entry point with intelligent startup logic"""
    print_banner()
    
    # Parse command line arguments
    mode = 'auto'
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    
    # Check and install Python dependencies
    if not check_python_deps():
        if not install_python_deps():
            print("❌ Cannot proceed without Python dependencies")
            sys.exit(1)
    
    # Handle different startup modes
    if mode == 'dev' or mode == 'development':
        print("🔧 Development mode requested")
        start_dev_mode()
        
    elif mode == 'build':
        print("🔨 Build mode - building React app only")
        build_react()
        
    elif mode == 'prod' or mode == 'production':
        print("🚀 Production mode requested")
        if not check_react_build():
            if not build_react():
                print("❌ Cannot start without React build")
                sys.exit(1)
        start_combined_server()
        
    else:
        # Auto mode - intelligent decision
        print("🤔 Auto mode - choosing best startup method...")
        
        frontend_exists = (Path(__file__).parent / 'frontend').exists()
        has_react_build = check_react_build()
        
        if not frontend_exists:
            print("❌ Frontend directory not found!")
            print("💡 Please ensure the React frontend is properly set up")
            sys.exit(1)
        
        if has_react_build:
            print("📦 React build found - starting in production mode")
            start_combined_server()
        else:
            print("🔧 No React build found - building first...")
            if build_react():
                print("✅ Build successful - starting production server")
                start_combined_server()
            else:
                print("⚠️ Build failed - falling back to development mode")
                start_dev_mode()

if __name__ == '__main__':
    main()
