import sys
import subprocess
import os
from pathlib import Path

# Workspace base directory (d:/Railway_AI_Training)
BASE_DIR = Path(__file__).resolve().parent

def check_install_dependencies():
    """
    Checks if necessary python packages are installed, and installs them if not.
    """
    required_packages = {
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
        "jwt": "PyJWT",
        "multipart": "python-multipart",
        "PIL": "pillow",
        "torch": "torch",
        "torchvision": "torchvision"
    }
    
    missing_packages = []
    for module_name, pip_name in required_packages.items():
        try:
            __import__(module_name)
        except ImportError:
            missing_packages.append(pip_name)
            
    if missing_packages:
        print(f"[Launcher] Missing required packages: {', '.join(missing_packages)}")
        print("[Launcher] Attempting to install missing dependencies...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
            print("[Launcher] Dependencies installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"[Launcher] Error installing dependencies: {str(e)}")
            print("[Launcher] Please install them manually using: pip install " + " ".join(missing_packages))
            sys.exit(1)

def verify_model_presence():
    """
    Validates that the model weight checkpoint exists.
    """
    model_path = BASE_DIR / "models" / "best_model.pth"
    if not model_path.exists():
        print(f"\n[Launcher] [CRITICAL WARNING] Model file not found at: {model_path}")
        print("[Launcher] [CRITICAL WARNING] The API server will start, but predictions will fail.")
        print("[Launcher] Please make sure a trained ResNet18 model weight file is stored at models/best_model.pth\n")
    else:
        print(f"[Launcher] Model checkpoint verified at: {model_path} ({model_path.stat().st_size / (1024*1024):.2f} MB)")

def create_output_directories():
    """
    Ensures that logging and static outputs folders are present before startup.
    """
    folders = [
        BASE_DIR / "backend" / "logs",
        BASE_DIR / "backend" / "outputs" / "gradcam"
    ]
    for folder in folders:
        if not folder.exists():
            folder.mkdir(parents=True, exist_ok=True)
            print(f"[Launcher] Created folder: {folder}")

def main():
    print("==================================================")
    print("Railway Track Inspection AI Service Launcher")
    print("==================================================")
    
    # 1. Run environment sanity checks
    check_install_dependencies()
    create_output_directories()
    verify_model_presence()
    
    # 2. Add current directory to PYTHONPATH to ensure backend imports work
    os.environ["PYTHONPATH"] = str(BASE_DIR)
    
    # 3. Launch Uvicorn
    print("\n[Launcher] Starting FastAPI backend with hot-reloading at http://127.0.0.1:8000...")
    print("[Launcher] Swagger UI available at http://127.0.0.1:8000/docs\n")
    
    try:
        import uvicorn
        # Runs the backend/main.py FastAPI application
        uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
    except KeyboardInterrupt:
        print("\n[Launcher] Backend server stopped by user.")
    except Exception as e:
        print(f"\n[Launcher] Server crashed with error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
