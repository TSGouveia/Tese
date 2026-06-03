import subprocess
import sys
import os
import time

def run_cmd(cmd, cwd=None):
    print(f"Running: {cmd}")
    res = subprocess.run(cmd, shell=True, cwd=cwd)
    if res.returncode != 0:
        print(f"Command failed with code {res.returncode}")
        # sys.exit(res.returncode)

# Get the absolute path to the directory containing this script (AAS Client)
script_dir = os.path.dirname(os.path.abspath(__file__))

print("--- 1. Cleaning up AAS ---")
run_cmd(f'{sys.executable} "cleanup_kit.py"', cwd=script_dir)

print("\n--- 2. Generating and Deploying AAS ---")
run_cmd(f'{sys.executable} "kit_studio_manager.py" "3D_models/conveyor_kit_config.json"', cwd=script_dir)
run_cmd(f'{sys.executable} "kit_studio_manager.py" "3D_models/product_config.json"', cwd=script_dir)

print("\n--- 3. Fixing Registry Linkage ---")
time.sleep(1) # Give it a second to register
run_cmd(f'{sys.executable} "fix_registry.py"', cwd=script_dir)
run_cmd(f'{sys.executable} "fix_registry_product.py"', cwd=script_dir)

print("\n--- ALL DONE ---")
