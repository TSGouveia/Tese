import os
import sys
import json
import time
import zipfile
import base64
import urllib.parse
import requests

REPO_URL = "http://localhost:8081"
REGISTRY_URL = "http://localhost:8082"
SUBMODEL_REGISTRY_URL = "http://localhost:8083"

TEMPLATE_AASX = os.path.join("aasx_packages", "Conveyor_1_Kit.aasx")
PUNCH_TEMPLATE_AASX = os.path.join("aasx_packages", "Punch_FMS_Kit.aasx")

def get_all_encodings(raw_id):
    if not raw_id:
        return []
    encodings = []
    # 1. Base64 URL-safe (padded and unpadded)
    b64_url = base64.urlsafe_b64encode(raw_id.encode()).decode()
    encodings.append(b64_url)
    encodings.append(b64_url.rstrip("="))
    # 2. Standard Base64 (padded and unpadded)
    b64_std = base64.b64encode(raw_id.encode()).decode()
    encodings.append(b64_std)
    encodings.append(b64_std.rstrip("="))
    # 3. URL Encoded
    encodings.append(urllib.parse.quote_plus(raw_id))
    encodings.append(urllib.parse.quote(raw_id))
    return list(set(encodings))

def delete_all_aas():
    print("\n--- A LIMPAR TODAS AS AAS DO BASYX ---")
    try:
        r = requests.get(f"{REGISTRY_URL}/shell-descriptors", timeout=5)
        shells = r.json()
        if isinstance(shells, dict):
            shells = shells.get("result", [])
    except Exception as e:
        print(f"Erro ao ligar ao Registry ({REGISTRY_URL}): {e}")
        shells = []

    # Também tentar shells direto do Repo
    try:
        r_repo = requests.get(f"{REPO_URL}/shells", timeout=5)
        repo_shells = r_repo.json()
        if isinstance(repo_shells, dict):
            repo_shells = repo_shells.get("result", [])
        for s in repo_shells:
            s_id = s.get("id")
            if s_id and not any(x.get("id") == s_id for x in shells):
                shells.append(s)
    except Exception as e:
        print(f"Erro ao obter shells do Repo ({REPO_URL}): {e}")

    if not shells:
        print("Nenhuma AAS encontrada no servidor.")
    else:
        for s in shells:
            shell_id = s.get("id")
            id_short = s.get("idShort", shell_id)
            print(f"-> A apagar AAS: {id_short} ({shell_id})...")
            
            # Buscar submodelos
            found_submodels = []
            for enc_shell in get_all_encodings(shell_id):
                try:
                    s_res = requests.get(f"{REPO_URL}/shells/{enc_shell}", timeout=5)
                    if s_res.status_code == 200:
                        data = s_res.json()
                        for ref in data.get("submodels", []):
                            keys = ref.get("keys", [])
                            if keys:
                                sm_id = keys[0].get("value")
                                if sm_id and sm_id not in found_submodels:
                                    found_submodels.append(sm_id)
                        break
                except Exception:
                    pass

            # Apagar submodelos
            for sm_id in found_submodels:
                for enc in get_all_encodings(sm_id):
                    for base in [f"{REPO_URL}/submodels", f"{REGISTRY_URL}/submodel-descriptors", f"{SUBMODEL_REGISTRY_URL}/submodel-descriptors"]:
                        try:
                            requests.delete(f"{base}/{enc}", timeout=3)
                        except Exception:
                            pass

            # Apagar Shell
            for enc in get_all_encodings(shell_id):
                for base in [f"{REPO_URL}/shells", f"{REGISTRY_URL}/shell-descriptors"]:
                    try:
                        requests.delete(f"{base}/{enc}", timeout=3)
                    except Exception:
                        pass

    # Apagar quaisquer submodelos orfãos que tenham ficado no repo
    try:
        r_sm = requests.get(f"{REPO_URL}/submodels", timeout=5)
        all_sm = r_sm.json()
        if isinstance(all_sm, dict):
            all_sm = all_sm.get("result", [])
        for sm in all_sm:
            sm_id = sm.get("id")
            if sm_id:
                for enc in get_all_encodings(sm_id):
                    for base in [f"{REPO_URL}/submodels", f"{REGISTRY_URL}/submodel-descriptors", f"{SUBMODEL_REGISTRY_URL}/submodel-descriptors"]:
                        try:
                            requests.delete(f"{base}/{enc}", timeout=3)
                        except Exception:
                            pass
    except Exception:
        pass

    print("Limpeza concluida com sucesso!")

def generate_and_deploy_conveyors(count, step_x=-4.5):
    if not os.path.exists(TEMPLATE_AASX):
        print(f"ERRO: Nao encontrei o template base '{TEMPLATE_AASX}'.")
        return

    # Check for punch template
    has_punch = os.path.exists(PUNCH_TEMPLATE_AASX)
    if not has_punch:
        print(f"[Aviso] Punch template '{PUNCH_TEMPLATE_AASX}' nao encontrado. Punches nao serao criados.")

    print(f"\nA gerar e fazer deploy de {count} conveyors (step X = {step_x})...")
    if has_punch:
        # Punch positions: conveyor 3, 8, 13, 18, ... (first=3, then every 5)
        punch_positions = [i for i in range(3, count + 1, 5)]
        print(f"Punches serao colocados nos conveyors: {punch_positions}")

    # Ler dados do pacote template (Conveyor)
    with zipfile.ZipFile(TEMPLATE_AASX, 'r') as zin:
        template_files = {name: zin.read(name) for name in zin.namelist()}
        data_json = json.loads(template_files['aasx/data.json'].decode('utf-8'))

    # Ler dados do pacote template (Punch)
    if has_punch:
        with zipfile.ZipFile(PUNCH_TEMPLATE_AASX, 'r') as zin:
            punch_template_files = {name: zin.read(name) for name in zin.namelist()}
            punch_data_json = json.loads(punch_template_files['aasx/data.json'].decode('utf-8'))

    # Criar pasta aasx_packages se não existir
    os.makedirs("aasx_packages", exist_ok=True)

    punch_counter = 0

    for i in range(1, count + 1):
        num_str = str(i)
        conveyor_name = f"Conveyor_{num_str}"
        shell_id = f"https://acplt.org/AAS_Conveyor_{num_str}"
        global_asset_id = f"https://acplt.org/AAS_Conveyor_{num_str}"
        pos_x = round((i - 1) * step_x, 3)

        # Clonar data_json
        new_data = json.loads(json.dumps(data_json))

        # Modificar Shell
        shell = new_data['assetAdministrationShells'][0]
        shell['id'] = shell_id
        shell['idShort'] = conveyor_name
        if 'assetInformation' in shell:
            shell['assetInformation']['globalAssetId'] = global_asset_id

        # Mapear submodelos e atualizar IDs
        sm_descriptors = []
        for sm in new_data['submodels']:
            old_sm_id = sm['id']
            # Substituir _Conveyor_1 por _Conveyor_{num_str}
            if "_Conveyor_" in old_sm_id:
                prefix = old_sm_id.rsplit("_Conveyor_", 1)[0]
                new_sm_id = f"{prefix}_{conveyor_name}"
            else:
                new_sm_id = f"{old_sm_id}_{num_str}"

            sm['id'] = new_sm_id
            sm_descriptors.append({
                "idShort": sm.get("idShort"),
                "id": new_sm_id,
                "endpoints": [{
                    "interface": "SUBMODEL-3.0",
                    "protocolInformation": {
                        "href": f"{REPO_URL}/submodels/{new_sm_id}",
                        "endpointProtocol": "HTTP"
                    }
                }]
            })

            # Atualizar coordenadas no VisualStructure
            if sm.get('idShort') == 'VisualStructure':
                for el in sm.get('submodelElements', []):
                    if el.get('modelType') == 'SubmodelElementCollection':
                        for sub_el in el.get('value', []):
                            if sub_el.get('idShort') == 'Transform':
                                for coord in sub_el.get('value', []):
                                    if coord.get('idShort') == 'PosX':
                                        coord['value'] = str(float(pos_x))

        # Atualizar referencias dos submodelos no Shell
        shell['submodels'] = [
            {"type": "ModelReference", "keys": [{"type": "Submodel", "value": sm['id']}]}
            for sm in new_data['submodels']
        ]

        # Criar novo arquivo .aasx
        out_aasx_path = os.path.join("aasx_packages", f"{conveyor_name}_Kit.aasx")
        with zipfile.ZipFile(out_aasx_path, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
            for name, content in template_files.items():
                if name == 'aasx/data.json':
                    zout.writestr(name, json.dumps(new_data, indent=2).encode('utf-8'))
                else:
                    zout.writestr(name, content)

        print(f"[{i}/{count}] A enviar {conveyor_name} (X={pos_x}) para BaSyx...")

        # 1. Upload .aasx para o Repo BaSyx
        with open(out_aasx_path, 'rb') as f:
            res_upload = requests.post(
                f"{REPO_URL}/upload",
                files={'file': (os.path.basename(out_aasx_path), f, 'application/octet-stream')},
                timeout=10
            )

        if res_upload.status_code not in [200, 201, 204]:
            print(f"  [Aviso] Falha no upload para Repo (HTTP {res_upload.status_code}): {res_upload.text[:150]}")

        # 2. Registar shell no Registry
        reg_payload = {
            "id": shell_id,
            "idShort": conveyor_name,
            "assetKind": "Instance",
            "globalAssetId": global_asset_id,
            "submodelDescriptors": sm_descriptors,
            "endpoints": [{
                "interface": "AAS-3.0",
                "protocolInformation": {
                    "href": f"{REPO_URL}/shells/{shell_id}",
                    "endpointProtocol": "HTTP"
                }
            }]
        }

        try:
            res_reg = requests.post(f"{REGISTRY_URL}/shell-descriptors", json=reg_payload, timeout=10)
            if res_reg.status_code not in [200, 201, 204, 409]:
                print(f"  [Aviso] Falha ao registar no Registry (HTTP {res_reg.status_code}): {res_reg.text[:150]}")
            else:
                print(f"  -> {conveyor_name} carregado e registado com sucesso!")
        except Exception as e:
            print(f"  [Aviso] Erro no Registry: {e}")

        # 3. Spawnar Punch se este conveyor esta na posicao certa (3, 8, 13, 18, ...)
        if has_punch and i in punch_positions:
            punch_counter += 1
            deploy_punch(punch_counter, pos_x, punch_data_json, punch_template_files)

    total_punches = punch_counter if has_punch else 0
    print(f"\nFeito! {count} conveyors e {total_punches} punches criadas e deployadas.")


def deploy_punch(punch_num, pos_x, punch_data_json, punch_template_files):
    """Deploy a single Punch AAS at the given X position."""
    punch_name = f"Punch_{punch_num}"
    shell_id = f"https://acplt.org/AAS_{punch_name}"
    global_asset_id = f"http://acplt.org/Assets/{punch_name}"

    # Clonar data_json do Punch
    new_data = json.loads(json.dumps(punch_data_json))

    # Modificar Shell
    shell = new_data['assetAdministrationShells'][0]
    shell['id'] = shell_id
    shell['idShort'] = punch_name
    if 'assetInformation' in shell:
        shell['assetInformation']['globalAssetId'] = global_asset_id

    # Mapear submodelos e atualizar IDs
    sm_descriptors = []
    for sm in new_data['submodels']:
        old_sm_id = sm['id']
        # Substituir _Punch_FMS por _Punch_{num}
        if "_Punch_FMS" in old_sm_id:
            new_sm_id = old_sm_id.replace("_Punch_FMS", f"_{punch_name}")
        else:
            new_sm_id = f"{old_sm_id}_{punch_num}"

        sm['id'] = new_sm_id
        sm_descriptors.append({
            "idShort": sm.get("idShort"),
            "id": new_sm_id,
            "endpoints": [{
                "interface": "SUBMODEL-3.0",
                "protocolInformation": {
                    "href": f"{REPO_URL}/submodels/{new_sm_id}",
                    "endpointProtocol": "HTTP"
                }
            }]
        })

        # Atualizar coordenadas no VisualStructure
        if sm.get('idShort') == 'VisualStructure':
            for el in sm.get('submodelElements', []):
                if el.get('modelType') == 'SubmodelElementCollection':
                    for sub_el in el.get('value', []):
                        if sub_el.get('idShort') == 'Transform':
                            for coord in sub_el.get('value', []):
                                if coord.get('idShort') == 'PosX':
                                    coord['value'] = str(float(pos_x))

    # Atualizar referencias dos submodelos no Shell
    shell['submodels'] = [
        {"type": "ModelReference", "keys": [{"type": "Submodel", "value": sm['id']}]}
        for sm in new_data['submodels']
    ]

    # Criar novo arquivo .aasx
    out_aasx_path = os.path.join("aasx_packages", f"{punch_name}_Kit.aasx")
    with zipfile.ZipFile(out_aasx_path, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
        for name, content in punch_template_files.items():
            if name == 'aasx/data.json':
                zout.writestr(name, json.dumps(new_data, indent=2).encode('utf-8'))
            else:
                zout.writestr(name, content)

    print(f"  [PUNCH] A enviar {punch_name} (X={pos_x}) para BaSyx...")

    # 1. Upload .aasx para o Repo BaSyx
    with open(out_aasx_path, 'rb') as f:
        res_upload = requests.post(
            f"{REPO_URL}/upload",
            files={'file': (os.path.basename(out_aasx_path), f, 'application/octet-stream')},
            timeout=10
        )

    if res_upload.status_code not in [200, 201, 204]:
        print(f"  [Aviso] Falha no upload do Punch (HTTP {res_upload.status_code}): {res_upload.text[:150]}")

    # 2. Registar shell no Registry
    reg_payload = {
        "id": shell_id,
        "idShort": punch_name,
        "assetKind": "Instance",
        "globalAssetId": global_asset_id,
        "submodelDescriptors": sm_descriptors,
        "endpoints": [{
            "interface": "AAS-3.0",
            "protocolInformation": {
                "href": f"{REPO_URL}/shells/{shell_id}",
                "endpointProtocol": "HTTP"
            }
        }]
    }

    try:
        res_reg = requests.post(f"{REGISTRY_URL}/shell-descriptors", json=reg_payload, timeout=10)
        if res_reg.status_code not in [200, 201, 204, 409]:
            print(f"  [Aviso] Falha ao registar Punch no Registry (HTTP {res_reg.status_code}): {res_reg.text[:150]}")
        else:
            print(f"  -> {punch_name} carregado e registado com sucesso!")
    except Exception as e:
        print(f"  [Aviso] Erro no Registry (Punch): {e}")

def main():
    print("=" * 45)
    print("   CONVEYOR SPAWNER JAVARDO - BASYX AAS   ")
    print("=" * 45)
    print("1) Limpar TODAS as AAS e spawnar N conveyors")
    print("2) Apenas spawnar N conveyors (sem limpar tudo)")
    print("3) Apenas limpar TODAS as AAS")
    print("0) Sair")
    
    escolha = input("\nEscolha uma opcao [1/2/3/0]: ").strip()
    
    if escolha == "1":
        delete_all_aas()
        try:
            qtd = int(input("\nQuantas conveyors queres ter? ").strip())
            if qtd <= 0:
                print("Numero invalido.")
                return
            generate_and_deploy_conveyors(qtd)
        except ValueError:
            print("Entrada invalida! Insere um numero inteiro.")
            
    elif escolha == "2":
        try:
            qtd = int(input("\nQuantas conveyors queres ter? ").strip())
            if qtd <= 0:
                print("Numero invalido.")
                return
            generate_and_deploy_conveyors(qtd)
        except ValueError:
            print("Entrada invalida! Insere um numero inteiro.")

    elif escolha == "3":
        confirm = input("Tens a certeza que queres limpar TODAS as AAS do BaSyx? (s/n): ").strip().lower()
        if confirm in ['s', 'sim', 'y', 'yes']:
            delete_all_aas()
        else:
            print("Operacao cancelada.")

    elif escolha == "0":
        print("A sair...")
    else:
        print("Opcao desconhecida.")

if __name__ == "__main__":
    main()
