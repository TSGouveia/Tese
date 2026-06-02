import requests
import base64

def encode_id(id_str):
    return base64.urlsafe_b64encode(id_str.encode()).decode().rstrip("=")

ids_to_delete = [
    "https://acplt.org/AAS_ConveyorKit",
    "https://acplt.org/Submodels/Visual_ConveyorKit",
    "https://acplt.org/Submodels/Pins_ConveyorKit",
    "https://acplt.org/Submodels/Behavior_ConveyorKit",
    "https://acplt.org/Submodels/Geometry_ConveyorKit"
]

print("Cleaning up existing IDs...")
for idx in ids_to_delete:
    encoded = encode_id(idx)
    r1 = requests.delete(f"http://localhost:8082/shell-descriptors/{encoded}")
    r2 = requests.delete(f"http://localhost:8083/submodel-descriptors/{encoded}")
    r3 = requests.delete(f"http://localhost:8081/shells/{encoded}")
    r4 = requests.delete(f"http://localhost:8081/submodels/{encoded}")
    print(f"Deleted {idx}: {r1.status_code}, {r2.status_code}, {r3.status_code}, {r4.status_code}")
