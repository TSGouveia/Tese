import requests, base64

REGISTRY_URL = "http://localhost:8082/shell-descriptors"
REPO_URL = "http://localhost:8081"

def encode_id(id_str):
    return base64.urlsafe_b64encode(id_str.encode()).decode().rstrip('=')

aas_id = "https://acplt.org/AAS_ConveyorKit"
submodels = [
    ("VirtualPins", "https://acplt.org/Submodels/Pins_ConveyorKit"),
    ("VisualStructure", "https://acplt.org/Submodels/Visual_ConveyorKit"),
    ("BehaviorMapping", "https://acplt.org/Submodels/Behavior_ConveyorKit")
]

for id_short, sm_id in submodels:
    payload = {
        "idShort": id_short,
        "id": sm_id,
        "endpoints": [
            {
                "interface": "SUBMODEL-3.0",
                "protocolInformation": {
                    "href": f"{REPO_URL}/submodels/{encode_id(sm_id)}",
                    "endpointProtocol": "HTTP"
                }
            }
        ]
    }
    url = f"{REGISTRY_URL}/{encode_id(aas_id)}/submodel-descriptors"
    print(f"Linking {id_short}...")
    res = requests.post(url, json=payload)
    print(f"  Result: {res.status_code}")
