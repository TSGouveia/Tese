import requests, base64, json, os, sys

REGISTRY_URL = "http://localhost:8082/shell-descriptors"
REPO_URL = "http://localhost:8081"

def encode_id(id_str):
    return base64.urlsafe_b64encode(id_str.encode()).decode().rstrip('=')

def link_registries_for_config(config_path):
    with open(config_path, "r") as f:
        config = json.load(f)
    
    kit_name = config.get("kit_name")
    if not kit_name: return

    aas_id = f"https://acplt.org/AAS_{kit_name}"
    submodels = [
        ("VirtualPins", f"https://acplt.org/Submodels/Pins_{kit_name}"),
        ("VisualStructure", f"https://acplt.org/Submodels/Visual_{kit_name}"),
        ("BehaviorMapping", f"https://acplt.org/Submodels/Behavior_{kit_name}")
    ]

    print(f"Linking {kit_name}...")
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
        res = requests.post(url, json=payload)
        print(f"  {id_short}: {res.status_code}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            link_registries_for_config(arg)
