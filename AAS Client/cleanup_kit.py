import requests
import base64

def encode_id(id_str):
    return base64.urlsafe_b64encode(id_str.encode()).decode().rstrip("=")

def nuke_basyx():
    print("🧹 Wiping BaSyx Server Clean...")
    
    # 1. Get and delete all Shells from Repo
    try:
        res = requests.get("http://localhost:8081/shells", timeout=10)
        if res.status_code == 200:
            for shell in res.json().get("result", []):
                s_id = shell.get("id")
                if s_id:
                    enc = encode_id(s_id)
                    requests.delete(f"http://localhost:8081/shells/{enc}", timeout=10)
                    requests.delete(f"http://localhost:8082/shell-descriptors/{enc}", timeout=10)
                    print(f"Deleted Shell: {s_id}")
    except Exception as e:
        print("Could not clear shells:", e)

    # 2. Get and delete all Submodels from Repo
    try:
        res = requests.get("http://localhost:8081/submodels", timeout=10)
        if res.status_code == 200:
            for sm in res.json().get("result", []):
                sm_id = sm.get("id")
                if sm_id:
                    enc = encode_id(sm_id)
                    requests.delete(f"http://localhost:8081/submodels/{enc}", timeout=10)
                    requests.delete(f"http://localhost:8083/submodel-descriptors/{enc}", timeout=10)
                    print(f"Deleted Submodel: {sm_id}")
    except Exception as e:
        print("Could not clear submodels:", e)

    print("✨ BaSyx is now completely empty.")

if __name__ == "__main__":
    nuke_basyx()
