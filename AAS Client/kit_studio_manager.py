import os
import requests
import mimetypes
import posixpath
import basyx.aas.model as model
import basyx.aas.adapter.aasx as aasx
import hashlib

class RobustFileRepo(dict):
    def get_content_type(self, fn): 
        return mimetypes.guess_type(fn)[0] or "application/octet-stream"
    def add_file(self, n, c): self[n] = c
    def write_file(self, fn, t): 
        if fn in self: t.write(self[fn])
    def get_sha256(self, fn):
        if fn in self:
            return hashlib.sha256(self[fn]).hexdigest()
        return ""

class KitStudioManager:
    def __init__(self):
        self.kit_name = None
        self.aas_id = None
        self.description = None
        self.components = []

    def load_config(self, config_dict):
        self.kit_name = config_dict.get("kit_name")
        self.aas_id = config_dict.get("aas_id")
        self.description = config_dict.get("description")
        self.components = config_dict.get("components", [])

    def generate_aas(self):
        asset_info = model.AssetInformation(asset_kind=model.AssetKind.INSTANCE, global_asset_id=f"http://acplt.org/Assets/{self.kit_name}")
        shell = model.AssetAdministrationShell(asset_information=asset_info, id_=f"https://acplt.org/AAS_{self.kit_name}", id_short=self.aas_id)
        visual_structure = model.Submodel(id_=f"https://acplt.org/Submodels/Visual_{self.kit_name}", id_short="VisualStructure")
        virtual_pins = model.Submodel(id_=f"https://acplt.org/Submodels/Pins_{self.kit_name}", id_short="VirtualPins")
        behavior_mapping = model.Submodel(id_=f"https://acplt.org/Submodels/Behavior_{self.kit_name}", id_short="BehaviorMapping")

        inputs_coll = model.SubmodelElementCollection(id_short="Inputs")
        outputs_coll = model.SubmodelElementCollection(id_short="Outputs")
        virtual_pins.submodel_element.add(inputs_coll)
        virtual_pins.submodel_element.add(outputs_coll)

        for comp in self.components:
            name = comp["name"]
            safe_name = name.replace(" ", "_").replace("-", "_")
            comp_coll = model.SubmodelElementCollection(id_short=safe_name)
            mesh_filename = comp.get("mesh", "")
            if mesh_filename:
                comp_coll.value.add(model.File(id_short="Mesh", content_type="application/octet-stream", value=mesh_filename))
            comp_coll.value.add(model.Property(id_short="Parent", value_type=model.datatypes.String, value=comp.get("parent", "")))
            
            transform_coll = model.SubmodelElementCollection(id_short="Transform")
            pos = comp.get("position", [0,0,0])
            rot = comp.get("rotation", [0,0,0])
            scale = comp.get("scale", [1,1,1])
            for i, axis in enumerate(["X", "Y", "Z"]): transform_coll.value.add(model.Property(id_short=f"Pos{axis}", value_type=model.datatypes.Double, value=float(pos[i])))
            for i, axis in enumerate(["X", "Y", "Z"]): transform_coll.value.add(model.Property(id_short=f"Rot{axis}", value_type=model.datatypes.Double, value=float(rot[i])))
            for i, axis in enumerate(["X", "Y", "Z"]): transform_coll.value.add(model.Property(id_short=f"Scale{axis}", value_type=model.datatypes.Double, value=float(scale[i])))
            comp_coll.value.add(transform_coll)
            visual_structure.submodel_element.add(comp_coll)

            if "actuators" in comp:
                for act in comp["actuators"]:
                    pin_id = act["pin_id"]
                    target_comp = act.get("node", name)
                    
                    # Only add to virtual pins if it doesn't exist
                    existing_pins = [p.id_short for p in inputs_coll.value]
                    if pin_id not in existing_pins:
                        inputs_coll.value.add(model.Property(id_short=pin_id, value_type=model.datatypes.Boolean, value=False))
                    
                    # Make behavior mapping ID unique
                    beh_id = f"{pin_id}_{target_comp}".replace(" ", "_")
                    beh_coll = model.SubmodelElementCollection(id_short=beh_id)
                    beh_coll.value.add(model.Property(id_short="PinID", value_type=model.datatypes.String, value=pin_id))
                    beh_coll.value.add(model.Property(id_short="Component", value_type=model.datatypes.String, value=target_comp))
                    beh_coll.value.add(model.Property(id_short="Type", value_type=model.datatypes.String, value=act.get("behavior")))
                    params_coll = model.SubmodelElementCollection(id_short="Parameters")
                    if "axis" in act:
                        for i, a in enumerate(["X", "Y", "Z"]): params_coll.value.add(model.Property(id_short=f"Axis{a}", value_type=model.datatypes.Double, value=float(act["axis"][i])))
                    if "speed" in act: params_coll.value.add(model.Property(id_short="Speed", value_type=model.datatypes.Double, value=float(act["speed"])))
                    if "stop_sensor" in act: params_coll.value.add(model.Property(id_short="StopSensorComponent", value_type=model.datatypes.String, value=act["stop_sensor"]))
                    beh_coll.value.add(params_coll)
                    behavior_mapping.submodel_element.add(beh_coll)
            
            if "sensors" in comp:
                for sens in comp["sensors"]:
                    pin_id = sens["pin_id"]
                    target_comp = sens.get("node", name)
                    
                    # Only add to virtual pins if it doesn't exist
                    existing_pins = [p.id_short for p in outputs_coll.value]
                    if pin_id not in existing_pins:
                        outputs_coll.value.add(model.Property(id_short=pin_id, value_type=model.datatypes.Boolean, value=False))
                    
                    # Make behavior mapping ID unique
                    beh_id = f"{pin_id}_{target_comp}".replace(" ", "_")
                    beh_coll = model.SubmodelElementCollection(id_short=beh_id)
                    beh_coll.value.add(model.Property(id_short="PinID", value_type=model.datatypes.String, value=pin_id))
                    beh_coll.value.add(model.Property(id_short="Component", value_type=model.datatypes.String, value=target_comp))
                    beh_coll.value.add(model.Property(id_short="Type", value_type=model.datatypes.String, value=sens.get("behavior")))
                    params_coll = model.SubmodelElementCollection(id_short="Parameters")
                    if "target_filter" in sens: params_coll.value.add(model.Property(id_short="TargetFilter", value_type=model.datatypes.String, value=sens["target_filter"]))
                    if "active_low" in sens: params_coll.value.add(model.Property(id_short="ActiveLow", value_type=model.datatypes.Boolean, value=bool(sens["active_low"])))
                    if "visible" in sens: params_coll.value.add(model.Property(id_short="Visible", value_type=model.datatypes.Boolean, value=bool(sens["visible"])))
                    if "snap_target" in sens: params_coll.value.add(model.Property(id_short="SnapTarget", value_type=model.datatypes.String, value=sens["snap_target"]))
                    if "snap_position" in sens:
                        for i, a in enumerate(["X", "Y", "Z"]): params_coll.value.add(model.Property(id_short=f"SnapPos{a}", value_type=model.datatypes.Double, value=float(sens["snap_position"][i])))
                    beh_coll.value.add(params_coll)
                    behavior_mapping.submodel_element.add(beh_coll)

        shell.submodel.add(model.ModelReference.from_referable(visual_structure))
        shell.submodel.add(model.ModelReference.from_referable(virtual_pins))
        shell.submodel.add(model.ModelReference.from_referable(behavior_mapping))
        return shell, [visual_structure, virtual_pins, behavior_mapping]

    def deploy_aas(self, shell, submodels, base_dir, repo_url="http://localhost:8081", registry_url="http://localhost:8082"):
        obj_store = model.DictObjectStore()
        obj_store.add(shell)
        for sm in submodels: obj_store.add(sm)
        file_repo = RobustFileRepo()
        
        # PURE PASS-THROUGH: Pack all files in the directory
        # No more manual conversion or MTL hacking. Let glTF handle it.
        asset_extensions = ['.obj', '.mtl', '.stl', '.png', '.jpg', '.jpeg', '.dae', '.fbx', '.glb', '.gltf', '.bin']
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                if any(file.lower().endswith(ext) for ext in asset_extensions):
                    local_path = os.path.join(root, file)
                    rel_path = os.path.relpath(local_path, base_dir).replace("\\", "/")
                    with open(local_path, 'rb') as f: content = f.read()
                    aas_path = posixpath.normpath(posixpath.join("/aasx/kit", rel_path))
                    print(f"Packing {aas_path} ({len(content)} bytes) into AASX.")
                    file_repo.add_file(aas_path, content)

        # Update references to point to the AASX paths
        for sm in submodels:
            for el in sm.submodel_element:
                if isinstance(el, model.File) and el.value and not el.value.startswith("/aasx/"):
                    el.value = posixpath.normpath(posixpath.join("/aasx/kit", el.value))
                elif isinstance(el, model.SubmodelElementCollection):
                    for sub_el in el.value:
                        if isinstance(sub_el, model.File) and sub_el.value and not sub_el.value.startswith("/aasx/"):
                            sub_el.value = posixpath.normpath(posixpath.join("/aasx/kit", sub_el.value))

        os.makedirs("aasx_packages", exist_ok=True)
        out_fn = os.path.join("aasx_packages", f"{self.kit_name}_Kit.aasx")
        with aasx.AASXWriter(out_fn) as writer: writer.write_aas(shell.id, obj_store, file_repo, self.aas_id)
        with open(out_fn, 'rb') as f:
            res = requests.post(f"{repo_url}/upload", files={'file': (os.path.basename(out_fn), f, 'application/octet-stream')}, timeout=10)
        
        if res.status_code in [200, 201, 204]:
            payload = {
                "id": shell.id, "idShort": shell.id_short, "assetKind": "Instance",
                "globalAssetId": shell.asset_information.global_asset_id,
                "submodelDescriptors": [{"idShort": sm.id_short, "id": sm.id, "endpoints": [{"interface": "SUBMODEL-3.0", "protocolInformation": {"href": f"{repo_url}/submodels/{sm.id}", "endpointProtocol": "HTTP"}}]} for sm in submodels],
                "endpoints": [{"interface": "AAS-3.0", "protocolInformation": {"href": f"{repo_url}/shells/{shell.id}", "endpointProtocol": "HTTP"}}]
            }
            requests.post(f"{registry_url}/shell-descriptors", json=payload, timeout=10)
        else: raise Exception(f"Repository upload failed ({res.status_code}): {res.text}")

if __name__ == "__main__":
    import json, sys
    config_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join("AAS_TEMPLATES", "kit_config_template.json")
    if not os.path.exists(config_path): sys.exit(1)
    try:
        with open(config_path, "r") as f: config = json.load(f)
    except: sys.exit(1)
    manager = KitStudioManager()
    manager.load_config(config)
    shell, submodels = manager.generate_aas()
    print(f"Generating and deploying AAS for {manager.kit_name}...")
    try:
        manager.deploy_aas(shell, submodels, os.path.dirname(config_path))
        print(f"Successfully deployed AAS: {shell.id}")
    except Exception as e: print(f"Deployment failed: {e}")
