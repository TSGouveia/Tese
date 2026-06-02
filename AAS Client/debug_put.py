import requests, base64

def encode_id(id_str):
    return base64.urlsafe_b64encode(id_str.encode()).decode().rstrip('=')

REPO_URL = "http://localhost:8081"
pins_sm_id = "https://acplt.org/Submodels/Pins_ConveyorKit"
pin_id = "OUT_Conveyor_Run"
collection = "Outputs"

url = f"{REPO_URL}/submodels/{encode_id(pins_sm_id)}/submodel-elements/{collection}/{pin_id}/value"
print(f"Testing PUT at: {url}")

# Try different payload formats
payloads = [
    ("JSON string", '"true"', {"Content-Type": "application/json"}),
    ("Raw boolean string", "true", {"Content-Type": "application/json"}),
    ("JSON object", '{"value": true}', {"Content-Type": "application/json"})
]

for name, data, headers in payloads:
    print(f"\n--- Trying {name} ---")
    try:
        res = requests.put(url, data=data, headers=headers, timeout=5)
        print(f"Status: {res.status_code}")
        print(f"Response: {res.text}")
    except Exception as e:
        print(f"Error: {e}")

# Also check the current element structure
print("\n--- Current Element Details ---")
el_url = f"{REPO_URL}/submodels/{encode_id(pins_sm_id)}/submodel-elements/{collection}/{pin_id}"
res = requests.get(el_url)
print(f"GET Element Status: {res.status_code}")
if res.status_code == 200:
    print(res.json())
