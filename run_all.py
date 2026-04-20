import subprocess
import time
import sys
import os

def main():
    print("===================================")
    print("   AI STUDY PLANNER (VITE + API)   ")
    print("===================================")
    
    username = input("Enter your Username to track this session: ").strip()
    if not username:
        print("Username cannot be empty. Exiting.")
        return

    print("\nStarting FastAPI Backend Server...")
    # Start the backend API process
    api_process = subprocess.Popen([sys.executable, "-m", "uvicorn", "api:app", "--port", "8000"])
    
    time.sleep(2) # Give the API a second to start
    
    print("Starting Vite React Frontend...")
    # Start npm run dev for frontend (requires shell=True on Windows for npm)
    frontend_process = subprocess.Popen(["npm", "run", "dev"], cwd=os.path.join(os.getcwd(), "frontend"), shell=True)
    
    time.sleep(2)
    
    print(f"\nStarting AI Study Helper Camera for user: {username}...")
    # Start the OpenCV camera app
    app_process = subprocess.Popen([sys.executable, "app.py", "--username", username])
    
    try:
        # Keep the main process alive
        app_process.wait()
    except KeyboardInterrupt:
        print("\nStopping processes...")
    finally:
        print("Shutting down...")
        app_process.terminate()
        api_process.terminate()
        frontend_process.terminate()

if __name__ == "__main__":
    main()
