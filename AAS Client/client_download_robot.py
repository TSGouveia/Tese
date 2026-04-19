import os
import requests
import base64
import json

# --- CONFIGURAÇÃO ---
AAS_REGISTRY_URL = "http://localhost:8082/shell-descriptors"
BASE_URL = "http://localhost:8081"

def encode_id(id_str): return base64.urlsafe_b64encode(id_str.encode()).decode().rstrip("=")

def list_available_shells():
    print(f"\n[0] A consultar shells...")
    try:
        res = requests.get(AAS_REGISTRY_URL)
        if res.status_code != 200: return None
        data = res.json()
        raw = data.get("result", data) if isinstance(data, dict) else data
        shells = []
        print("\n# | ID Curto | ID da AAS")
        print("-" * 75)
        for item in raw:
            if isinstance(item, str):
                shell_desc = requests.get(f"{AAS_REGISTRY_URL}/{encode_id(item)}").json()
            else: shell_desc = item
            if not shell_desc.get("id") or shell_desc.get("id") in ["paging_metadata", "result"]: continue
            shells.append(shell_desc)
            print(f"[{len(shells)}] {shell_desc.get('idShort', 'N/A')} | {shell_desc.get('id', 'N/A')}")
        return shells
    except: return None

def find_sm(selected_shell, target):
    for sm in selected_shell.get('submodelDescriptors', []):
        if sm.get('idShort') == target: return sm.get('id')
    try:
        res = requests.get(f"{BASE_URL}/shells/{encode_id(selected_shell.get('id'))}")
        for sm_ref in res.json().get('submodels', []):
            sid = sm_ref['keys'][0]['value']
            if requests.get(f"{BASE_URL}/submodels/{encode_id(sid)}").json().get('idShort') == target: return sid
    except: pass
    return None

def fetch_file(sm_id, el_id, dest):
    try:
        res = requests.get(f"{BASE_URL}/submodels/{encode_id(sm_id)}/submodel-elements/{el_id}/attachment", stream=True)
        if res.status_code == 200:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, 'wb') as f:
                for chunk in res.iter_content(8192): f.write(chunk)
            return True
    except: pass
    return False

def sync_robot(selected_shell):
    rid = selected_shell.get('idShort', 'Robot')
    download_dir = f"client_site/robots/{rid}"
    
    # 1. GEOMETRIA
    print(f"\n[1] Sincronizando Ativos...")
    sm_id = find_sm(selected_shell, "GeometryData")
    if sm_id:
        res = requests.get(f"{BASE_URL}/submodels/{encode_id(sm_id)}/submodel-elements")
        els = res.json().get('result', res.json())
        count = 0
        for el in els:
            if el.get('modelType') == 'File':
                id_short = el.get('idShort')
                if id_short == "Main_URDF":
                    # URDF vai para a raiz (limpa o nome longo se existir)
                    val = el.get('value', 'robot.urdf')
                    dest = os.path.join(download_dir, os.path.basename(val).split('-')[-1])
                elif id_short.startswith("PATH_"):
                    # Descodificar caminho (PATH_meshes_SL_visual_SL_base_dae)
                    rel = id_short.replace("PATH_", "").replace("_SL_", "/").replace("_DOT_", ".")
                    # Se o id_short foi truncado pelo BaSyx, tentamos recuperar do value
                    dest = os.path.join(download_dir, rel)
                else:
                    dest = os.path.join(download_dir, os.path.basename(el.get('value', 'file')))

                print(f"    📦 -> {os.path.relpath(dest, download_dir)}")
                if fetch_file(sm_id, id_short, dest): count += 1
        print(f"    ✅ {count} ficheiros sincronizados.")

    # 2. POSIÇÃO
    sm_pos = find_sm(selected_shell, "PositionData")
    if sm_pos:
        els = requests.get(f"{BASE_URL}/submodels/{encode_id(sm_pos)}/submodel-elements").json().get('result', [])
        pos = {e.get('idShort'): e.get('value') for e in els if e.get('modelType') == 'Property'}
        with open(os.path.join(download_dir, "position.json"), 'w') as f: json.dump(pos, f, indent=4)

if __name__ == "__main__":
    print("=== Digital Twin Sync (Correct Filenames) ===")
    shells = list_available_shells()
    if shells:
        choice = input("\nEscolhe o número: ").strip()
        if choice.isdigit() and 0 < int(choice) <= len(shells): sync_robot(shells[int(choice)-1])
