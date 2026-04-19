import os
import requests
import mimetypes
import hashlib
import tkinter as tk
from tkinter import filedialog
import xml.etree.ElementTree as ET
import io
import re
import basyx.aas
from basyx.aas import model
from basyx.aas.adapter import aasx

# --- CONFIGURAÇÃO ---
BASE_URL = "http://localhost:8081"
UPLOAD_URL = f"{BASE_URL}/upload"
AAS_REGISTRY_URL = "http://localhost:8082/shell-descriptors"

def get_path(mode="file", title="Select"):
    root = tk.Tk(); root.withdraw(); root.attributes("-topmost", True)
    path = filedialog.askopenfilename(title=title) if mode == "file" else filedialog.askdirectory(title=title)
    root.destroy(); return path

def find_file_smart(search_root, target_filename, context_dir=None):
    clean_name = target_filename.replace("package://", "").replace("file://", "").replace("./", "").replace("\\", "/")
    basename = os.path.basename(clean_name)
    
    # 1. Contexto
    if context_dir:
        for p in [os.path.join(context_dir, clean_name), os.path.join(context_dir, basename)]:
            np = os.path.normpath(p)
            if os.path.exists(np) and os.path.isfile(np): return np

    # 2. Recursivo
    for root, _, files in os.walk(search_root):
        if basename in files: return os.path.join(root, basename)
    return None

class AssetManager:
    def __init__(self, assets_root):
        self.assets_root = os.path.abspath(assets_root)
        self.files_to_upload = {} # local_path -> rel_path

    def collect(self, filename, context_dir=None):
        found = find_file_smart(self.assets_root, filename, context_dir)
        if not found:
            if not any(ext in filename.lower() for ext in ['.stl', '.dae', '.obj', '.jpg', '.png']): return None
            print(f"   ⚠️  Faltou: {filename}")
            return None

        found = os.path.abspath(found)
        if found in self.files_to_upload: return self.files_to_upload[found]

        rel_path = os.path.relpath(found, self.assets_root).replace(os.sep, '/')
        self.files_to_upload[found] = rel_path
        print(f"   [+] {rel_path}")

        # Dependências internas
        if found.lower().endswith(('.dae', '.obj', '.mtl')):
            try:
                with open(found, 'r', errors='ignore') as f: content = f.read()
                # Procurar texturas/materiais (init_from, mtllib, map_Kd)
                refs = re.findall(r'<(?:init_from|texture|map_Kd|mtllib)[^>]*>\s*([^< \r\n]+)|(?:map_\w+|mtllib)\s+([^\s\r\n]+)', content)
                for r in refs:
                    ref = (r[0] or r[1]).strip()
                    if ref: self.collect(ref, os.path.dirname(found))
            except: pass
        return rel_path

class RobustFileRepo(dict):
    def get_content_type(self, fn): return mimetypes.guess_type(fn)[0] or "application/octet-stream"
    def add_file(self, n, c): self[n] = c
    def get_sha256(self, fn): return hashlib.sha256(self[fn]).hexdigest() if fn in self else ""
    def write_file(self, fn, t): 
        if fn in self: t.write(self[fn])

def deploy_via_environment_api():
    print(f"--- BaSyx Professional Twin Deployer ---")
    robot_id = input("\nID do Robô: ").strip()
    if not robot_id: return
    px = input("   X: "); py = input("   Y: "); pz = input("   Z: ")
    
    urdf_path = get_path("file", "Seleciona o URDF")
    assets_root = get_path("folder", "Seleciona a pasta ur_description")
    if not urdf_path or not assets_root: return

    manager = AssetManager(assets_root)
    
    print(f"\n[1/3] Rastreando Ativos...")
    tree = ET.parse(urdf_path)
    for elem in tree.getroot().iter():
        for attr, val in elem.attrib.items():
            if any(ext in val.lower() for ext in ['.stl', '.dae', '.obj', '.jpg', '.png']):
                rel = manager.collect(val, os.path.dirname(urdf_path))
                if rel: elem.set(attr, rel)
    
    urdf_bytes = io.BytesIO()
    tree.write(urdf_bytes, encoding='utf-8', xml_declaration=True)

    # Criar AAS
    shell = model.AssetAdministrationShell(
        asset_information=model.AssetInformation(asset_kind=model.AssetKind.INSTANCE, global_asset_id=f"http://acplt.org/Assets/{robot_id}"),
        id_=f"https://acplt.org/AAS_{robot_id}", id_short=robot_id
    )
    sm_geo = model.Submodel(id_=f"https://acplt.org/Submodels/Geo_{robot_id}", id_short="GeometryData")
    sm_pos = model.Submodel(id_=f"https://acplt.org/Submodels/Pos_{robot_id}", id_short="PositionData")
    for ax, v in [('X', px), ('Y', py), ('Z', pz)]:
        sm_pos.submodel_element.add(model.Property(id_short=f"Pos_{ax}", value_type=model.datatypes.Double, value=float(v)))

    file_repo = RobustFileRepo()
    u_fn = os.path.basename(urdf_path)
    file_repo.add_file(f"/aasx/robot/{u_fn}", urdf_bytes.getvalue())
    sm_geo.submodel_element.add(model.File(id_short="Main_URDF", value=f"/aasx/robot/{u_fn}", content_type="application/xml"))

    for l_path, r_path in manager.files_to_upload.items():
        aas_path = f"/aasx/robot/{r_path}"
        with open(l_path, 'rb') as f: file_repo.add_file(aas_path, f.read())
        
        # TRUQUE: O id_short guarda o caminho trocando / por _SL_
        path_id = "PATH_" + r_path.replace("/", "_SL_").replace(".", "_DOT_")
        sm_geo.submodel_element.add(model.File(id_short=path_id[:100], value=aas_path, content_type=mimetypes.guess_type(l_path)[0] or "application/octet-stream"))

    obj_store = model.DictObjectStore()
    obj_store.add(shell); obj_store.add(sm_geo); obj_store.add(sm_pos)
    shell.submodel.add(model.ModelReference.from_referable(sm_geo))
    shell.submodel.add(model.ModelReference.from_referable(sm_pos))

    # 3. GERAR E ENVIAR
    aasx_folder = "aasx_packages"
    os.makedirs(aasx_folder, exist_ok=True)
    output_fn = os.path.join(aasx_folder, f"{robot_id}_Twin.aasx")
    
    print(f"\n[2/3] Gerando pacote AASX com {len(manager.files_to_upload)} ativos...")
    with aasx.AASXWriter(output_fn) as writer:
        writer.write_aas(shell.id, obj_store, file_repo, robot_id)

    try:
        with open(output_fn, 'rb') as f:
            # Enviamos apenas o nome do ficheiro (sem o caminho da pasta) no multipart
            res = requests.post(UPLOAD_URL, files={'file': (os.path.basename(output_fn), f, 'application/octet-stream')})
            if res.status_code in [200, 201, 204]:
                print(f"   ✅ Digital Twin pronto!")
                requests.post(AAS_REGISTRY_URL, json={
                    "id": shell.id, "idShort": shell.id_short, "assetKind": "Instance",
                    "globalAssetId": shell.asset_information.global_asset_id,
                    "submodelDescriptors": [{"idShort": sm.id_short, "id": sm.id, "endpoints": [{"interface": "SUBMODEL-3.0", "protocolInformation": {"href": f"{BASE_URL}/submodels/{sm.id}", "endpointProtocol": "HTTP"}}]} for sm in [sm_geo, sm_pos]],
                    "endpoints": [{"interface": "AAS-3.0", "protocolInformation": {"href": f"{BASE_URL}/shells/{shell.id}", "endpointProtocol": "HTTP"}}]
                })
    except Exception as e: print(f"   ❌ Erro: {e}")

if __name__ == "__main__":
    deploy_via_environment_api()
