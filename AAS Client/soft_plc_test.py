import time
import requests
import base64

# Configuration
AAS_SERVER = "http://localhost:8081"
KIT_NAME = "SortingStation"

def encode_id(id_str):
    return base64.urlsafe_b64encode(id_str.encode()).decode().rstrip('=')

# Submodel IDs (as defined in kit_studio_manager.py)
PINS_SM_ID = f"https://acplt.org/Submodels/Pins_{KIT_NAME}"
PINS_URL = f"{AAS_SERVER}/submodels/{encode_id(PINS_SM_ID)}/submodel-elements"

def get_pin(collection, pin_id):
    url = f"{PINS_URL}/{collection}.{pin_id}"
    res = requests.get(url, timeout=2)
    if res.status_code == 200:
        data = res.json()
        return data.get('value') == 'true'
    return None

def set_pin(collection, pin_id, value):
    url = f"{PINS_URL}/{collection}.{pin_id}"
    payload = {
        "idShort": pin_id,
        "modelType": "Property",
        "valueType": "xs:boolean",
        "value": str(value).lower()
    }
    res = requests.put(url, json=payload, timeout=2)
    return res.status_code in [200, 201, 204]

def run_logic():
    print(f"--- Soft-PLC started for {KIT_NAME} ---")
    print("Logic: If IN_Item_Detected is TRUE, then OUT_Conveyor_Run is FALSE (Stop)")
    print("       If IN_Item_Detected is FALSE, then OUT_Conveyor_Run is TRUE (Move)")
    
    try:
        while True:
            # 1. Read Sensor (Input)
            item_detected = get_pin("Inputs", "IN_Item_Detected")
            
            if item_detected is not None:
                # 2. Execute Logic
                conveyor_should_run = not item_detected
                
                # 3. Write Actuator (Output)
                success = set_pin("Outputs", "OUT_Conveyor_Run", conveyor_should_run)
                
                state_str = "DETECTED - STOPPING" if item_detected else "CLEAR - RUNNING"
                print(f"[{time.strftime('%H:%M:%S')}] Sensor: {item_detected} | Command: {conveyor_should_run} ({state_str})", end='\r')
            else:
                print(f"[{time.strftime('%H:%M:%S')}] Error: Could not read pins. Is BaSyx running?", end='\r')
            
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\nStopping Soft-PLC...")
        set_pin("Outputs", "OUT_Conveyor_Run", False)

if __name__ == "__main__":
    run_logic()