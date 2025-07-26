#!/usr/bin/env python3
"""
Quick production runner for Pi Analytics Dashboard
Builds frontend and starts integrated Flask server
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and wait for completion"""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=cwd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        return False

def main():
    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("🚀 Pi Analytics Dashboard Quick Production Run")
    print("=" * 40)
    
    # Build frontend
    print("🔨 Building React frontend...")
    if not run_command(["npm", "run", "build"], cwd="frontend"):
        print("❌ Frontend build failed!")
        sys.exit(1)
    
    print("✅ Frontend built successfully!")
    
    # Check for virtual environment
    venv_path = Path("backend/venv")
    if not venv_path.exists():
        print("🔧 Creating virtual environment...")
        if not run_command(["python3", "-m", "venv", "venv"], cwd="backend"):
            print("❌ Failed to create virtual environment!")
            sys.exit(1)
    
    # Install dependencies
    print("📦 Installing dependencies...")
    pip_cmd = ["backend/venv/bin/pip", "install", "-r", "backend/requirements.txt"]
    if not run_command(pip_cmd):
        print("❌ Failed to install dependencies!")
        sys.exit(1)
    
    # Start the server
    print("🌶️  Starting integrated Flask server...")
    print("🌐 Server will be available at: http://localhost:5000")
    print("💡 Press Ctrl+C to stop")
    
    try:
        python_cmd = ["backend/venv/bin/python3", "backend/app.py"]
        subprocess.run(python_cmd, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except subprocess.CalledProcessError as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()