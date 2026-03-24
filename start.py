#!/usr/bin/env python3
"""
IntelliKnow KMS - Quick Start Script
"""
import os
import sys
import subprocess
import time

# Get project directory
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_DIR)

def print_banner():
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   🧠 IntelliKnow KMS - Quick Start                        ║
║   Gen AI-powered Knowledge Management System              ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)

def check_dependencies():
    """Check if required packages are installed"""
    try:
        import fastapi
        import streamlit
        import sqlalchemy
        print("✅ Dependencies installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("\nPlease install dependencies:")
        print("  pip install -r requirements.txt")
        return False

def start_backend():
    """Start FastAPI backend"""
    print("\n🚀 Starting FastAPI backend...")
    print("   URL: http://localhost:8000")
    print("   API Docs: http://localhost:8000/docs")
    print("\n   Press Ctrl+C to stop\n")

    subprocess.run([
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--reload",
        "--port", "8000"
    ])

def start_frontend():
    """Start Streamlit frontend"""
    print("\n🚀 Starting Streamlit frontend...")
    print("   URL: http://localhost:8501")
    print("\n   Press Ctrl+C to stop\n")

    subprocess.run([
        sys.executable, "-m", "streamlit",
        "run", "frontend/app.py",
        "--server.port", "8501",
        "--server.address", "localhost"
    ])

def main():
    print_banner()

    if not check_dependencies():
        sys.exit(1)

    print("\n" + "="*50)
    print("Starting services...")
    print("="*50 + "\n")

    # Start backend in background
    import multiprocessing

    backend_proc = multiprocessing.Process(target=start_backend)
    backend_proc.start()

    # Wait a bit for backend to start
    time.sleep(3)

    # Start frontend
    try:
        start_frontend()
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
        backend_proc.terminate()
        backend_proc.join()

if __name__ == "__main__":
    main()