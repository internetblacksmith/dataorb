#!/usr/bin/env python3
"""
Development server with file watching for PostHog Pi
Automatically builds React and starts Flask dev server
"""
import os
import sys
import subprocess
import signal
import time
from pathlib import Path

def run_command(cmd, cwd=None, check=False):
    """Run a command and return the process"""
    print(f"Running: {' '.join(cmd)}")
    try:
        if check:
            result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
            return result
        else:
            return subprocess.Popen(cmd, cwd=cwd)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return None

def main():
    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("🚀 Starting PostHog Pi Development Server")
    print("=" * 50)
    
    # Check if frontend directory exists
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found!")
        sys.exit(1)
    
    # Check if backend directory exists
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("❌ Backend directory not found!")
        sys.exit(1)
    
    processes = []
    
    try:
        # Start React development build with file watching
        print("🔨 Starting React file watcher...")
        react_process = run_command(["npm", "run", "dev"], cwd=frontend_dir)
        if react_process:
            processes.append(react_process)
            print("✅ React file watcher started")
        
        # Give React a moment to start
        time.sleep(3)
        
        # Start Flask development server
        print("🌶️  Starting Flask development server...")
        flask_env = os.environ.copy()
        flask_env["FLASK_DEBUG"] = "1"
        flask_process = run_command(["python3", "app.py"], cwd=backend_dir)
        if flask_process:
            processes.append(flask_process)
            print("✅ Flask development server started")
        
        print("\n🎉 Development servers are running!")
        print("📱 Frontend: React file watcher active")
        print("🔧 Backend: Flask with auto-reload at http://localhost:5000")
        print("\n💡 Press Ctrl+C to stop all servers")
        
        # Wait for processes
        while True:
            # Check if any process has terminated
            for i, process in enumerate(processes):
                if process.poll() is not None:
                    print(f"❌ Process {i} terminated unexpectedly")
                    return
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping development servers...")
        
        # Terminate all processes
        for process in processes:
            if process.poll() is None:
                process.terminate()
                
        # Wait a bit for graceful shutdown
        time.sleep(2)
        
        # Kill any remaining processes
        for process in processes:
            if process.poll() is None:
                process.kill()
                
        print("✅ All servers stopped")

if __name__ == "__main__":
    main()