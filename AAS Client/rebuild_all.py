import subprocess
import sys
import os
import time

def run_cmd(cmd):
    print(f"Running: {cmd}")
    res = subprocess.run(cmd, shell=True)
    if res.returncode != 0:
        print(f"Command failed with code {res.returncode}")
        # sys.exit(res.returncode)

print("--- 1. Cleaning up AAS ---")
run_cmd('python "AAS Client/cleanup_kit.py"')

print("\n--- 2. Generating and Deploying AAS ---")
run_cmd('python "AAS Client/kit_studio_manager.py" "AAS Client/3D_models/conveyor_kit_config.json"')

print("\n--- 3. Fixing Registry Linkage ---")
time.sleep(1) # Give it a second to register
run_cmd('python "AAS Client/fix_registry.py"')

print("\n--- ALL DONE ---")
