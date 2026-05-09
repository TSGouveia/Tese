import os
import subprocess
import sys

def check_and_install_dependencies(venv_python):
    print("Checking for Nuitka...")
    try:
        # Check if nuitka is installed
        subprocess.run([venv_python, "-m", "nuitka", "--version"], 
                       check=True, capture_output=True)
        print("Nuitka is already installed.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Nuitka not found. Installing Nuitka and dependencies...")
        venv_pip = os.path.join(os.path.dirname(venv_python), "pip.exe")
        try:
            # Install nuitka, ordered-set and zstandard (for compression)
            subprocess.run([venv_pip, "install", "nuitka", "ordered-set", "zstandard"], check=True)
            print("Successfully installed dependencies.")
        except subprocess.CalledProcessError:
            print("Error: Failed to install Nuitka. Please try 'pip install nuitka' manually.")
            return False
    return True

def compile():
    # Use the CURRENT interpreter that is running this script
    venv_python = sys.executable
    
    print(f"Using Python: {venv_python}")

    if not check_and_install_dependencies(venv_python):
        return

    script_name = "create_robotic_arm.py"
    output_name = "AAS_Robot_Studio"

    print(f"\n--- Starting Compilation of {script_name} ---")
    print("This might take 10-20 minutes. Please wait...")

    # Final build: With console, onefile mode
    cmd = [
        venv_python, "-m", "nuitka",
        "--standalone",
        "--onefile",
        "--enable-plugin=pyqt6",
        "--windows-console-mode=force",
        f"--output-filename={output_name}",
        script_name
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"\nSUCCESS! Executable created: {output_name}.exe")
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: Compilation failed with exit code {e.returncode}")
    except Exception as e:
        print(f"\nERROR: {str(e)}")

if __name__ == "__main__":
    compile()
