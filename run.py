import subprocess
import time
import os
import signal
import sys

def main():
    print("🚀 Launching AstroHighlight...")
    
    # 1. Start Backend
    print("Starting Backend (FastAPI)...")
    backend = subprocess.Popen([sys.executable, "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"],
                               cwd=os.getcwd())
    
    # 2. Start Frontend
    print("Starting Frontend (Next.js)...")
    frontend = subprocess.Popen(["npm.cmd", "run", "dev"],
                                cwd=os.path.join(os.getcwd(), "web"),
                                env={**os.environ, "PORT": "3000"})
    
    print("\n✅ Platform is ready!")
    print("🔗 Backend: http://localhost:8000")
    print("🔗 Frontend: http://localhost:3000")
    print("\nPress Ctrl+C to stop both servers.")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        backend.terminate()
        frontend.terminate()
        print("Goodbye!")

if __name__ == "__main__":
    main()
