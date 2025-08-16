#!/usr/bin/env python3
"""
Development server with file watching for Pi Analytics Dashboard
Automatically builds React and starts Flask dev server
"""
import os
import sys
import subprocess
import signal
import time
import atexit
from pathlib import Path

# Store process references globally for cleanup
processes = []

def cleanup():
    """Clean up all child processes"""
    print("\n🛑 Cleaning up processes...")
    for process in processes:
        try:
            if process.poll() is None:
                # Try to terminate the entire process group
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        except ProcessLookupError:
            pass  # Process already terminated
        except Exception as e:
            print(f"Error terminating process: {e}")
    
    # Give processes time to terminate gracefully
    time.sleep(1)
    
    # Force kill any remaining processes
    for process in processes:
        try:
            if process.poll() is None:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass
        except Exception as e:
            print(f"Error killing process: {e}")
    
    print("✅ All servers stopped")

def signal_handler(signum, frame):
    """Handle interrupt signals"""
    cleanup()
    sys.exit(0)

def run_command(cmd, cwd=None, check=False, env=None):
    """Run a command and return the process"""
    print(f"Running: {' '.join(cmd)}")
    try:
        if check:
            result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
            return result
        else:
            # Start new process group to ensure all child processes can be terminated
            process = subprocess.Popen(
                cmd, 
                cwd=cwd,
                env=env,
                preexec_fn=os.setsid,  # Create new process group
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return process
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        if hasattr(e, 'stdout'):
            print(f"stdout: {e.stdout}")
        if hasattr(e, 'stderr'):
            print(f"stderr: {e.stderr}")
        return None
    except FileNotFoundError as e:
        print(f"❌ Command not found: {cmd[0]}")
        print(f"   Error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error starting process: {e}")
        return None

def main():
    global processes
    
    # Register cleanup handlers
    atexit.register(cleanup)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("🚀 Starting Pi Analytics Dashboard Development Server")
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
    
    try:
        # Check for npm
        npm_check = subprocess.run(["which", "npm"], capture_output=True, text=True)
        if npm_check.returncode != 0:
            print("❌ npm not found! Please install Node.js and npm.")
            sys.exit(1)
        
        # Start React development build with file watching
        print("🔨 Starting React file watcher...")
        react_process = run_command(["npm", "run", "dev"], cwd=frontend_dir)
        if react_process:
            processes.append(react_process)
            print("✅ React file watcher started (PID: {})".format(react_process.pid))
        else:
            print("❌ Failed to start React file watcher")
            return
        
        # Give React a moment to start
        time.sleep(3)
        
        # Start Flask development server
        print("🌶️  Starting Flask development server...")
        flask_env = os.environ.copy()
        flask_env["FLASK_DEBUG"] = "1"
        
        # Check if venv exists
        venv_python = backend_dir / "venv" / "bin" / "python"
        venv_python3 = backend_dir / "venv" / "bin" / "python3"
        
        if venv_python.exists():
            python_cmd = str(venv_python.absolute())
            print(f"   Using virtual environment: {python_cmd}")
        elif venv_python3.exists():
            python_cmd = str(venv_python3.absolute())
            print(f"   Using virtual environment: {python_cmd}")
        else:
            print("⚠️  Virtual environment not found at backend/venv")
            print("   Creating virtual environment...")
            venv_result = subprocess.run(
                ["python3", "-m", "venv", "venv"],
                cwd=backend_dir,
                capture_output=True,
                text=True
            )
            if venv_result.returncode != 0:
                print("❌ Failed to create virtual environment")
                print(f"   Error: {venv_result.stderr}")
                cleanup()
                return
            
            # Install requirements
            print("   Installing requirements...")
            pip_cmd = str(backend_dir / "venv" / "bin" / "pip")
            req_file = str(backend_dir / "requirements.txt")
            
            if Path(req_file).exists():
                pip_result = subprocess.run(
                    [pip_cmd, "install", "-r", "requirements.txt"],
                    cwd=backend_dir,
                    capture_output=True,
                    text=True
                )
                if pip_result.returncode != 0:
                    print("⚠️  Failed to install some requirements")
                    print(f"   Error: {pip_result.stderr[:500]}")
            
            python_cmd = str(venv_python.absolute())
            print(f"   Using newly created venv: {python_cmd}")
        
        # Check if app.py exists
        app_file = backend_dir / "app.py"
        if not app_file.exists():
            print(f"❌ app.py not found in {backend_dir}")
            cleanup()
            return
        
        # Start Flask
        flask_process = run_command(
            [python_cmd, "app.py"],
            cwd=backend_dir,
            env=flask_env
        )
        
        if flask_process:
            processes.append(flask_process)
            print("✅ Flask development server started (PID: {})".format(flask_process.pid))
            
            # Check for early errors
            time.sleep(2)
            if flask_process.poll() is not None:
                print("❌ Flask server exited immediately")
                stderr_output = flask_process.stderr.read().decode() if flask_process.stderr else ""
                if stderr_output:
                    print(f"   Error: {stderr_output[:500]}")
                cleanup()
                return
        else:
            print("❌ Failed to start Flask server")
            cleanup()
            return
        
        print("\n🎉 Development servers are running!")
        print("📱 Frontend: React file watcher active")
        print("🔧 Backend: Flask with auto-reload at http://localhost:5000")
        print("\n💡 Press Ctrl+C to stop all servers")
        
        # Wait for processes
        while True:
            # Check if any process has terminated
            for i, process in enumerate(processes):
                if process.poll() is not None:
                    process_name = "React" if i == 0 else "Flask"
                    print(f"\n❌ {process_name} process terminated unexpectedly")
                    
                    # Try to get error output
                    if process.stderr:
                        stderr_output = process.stderr.read().decode()
                        if stderr_output:
                            print(f"   Error output: {stderr_output[:500]}")
                    
                    cleanup()
                    return
            time.sleep(1)
            
    except KeyboardInterrupt:
        # Signal handler will take care of cleanup
        pass
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main()