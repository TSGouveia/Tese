import time
import requests
import base64
import random
import math

DEFAULT_BASYX_URL = "http://localhost:8081"

def b64(s):
    return base64.urlsafe_b64encode(s.encode()).decode().rstrip('=')

def dummy_sync():
    try:
        print("\n--- AAS Multi-Robot Dummy Simulator ---")
        
        # 1. Obter URL do BaSyx
        basyx_url = input(f"Introduza a URL do servidor BaSyx [{DEFAULT_BASYX_URL}]: ").strip()
        if not basyx_url:
            basyx_url = DEFAULT_BASYX_URL
        
        # 2. Listar AAS disponíveis
        print(f"A obter lista de AAS de {basyx_url}...")
        try:
            shells_res = requests.get(f"{basyx_url}/shells", timeout=5).json()
            shells = shells_res if isinstance(shells_res, list) else shells_res.get("result", [])
            
            if not shells:
                print("Nenhum AAS encontrado no servidor.")
                return

            print("\nRobôs (AAS) encontrados:")
            for i, s in enumerate(shells):
                print(f"[{i}] {s.get('idShort', 'Sem Nome')} ({s.get('id')})")
            
            selection = input("\nEscolha os índices (ex: 0,1,2) ou 'all' para todos: ").strip().lower()
            
            selected_shells = []
            if selection == 'all':
                selected_shells = shells
            else:
                try:
                    indices = [int(x.strip()) for x in selection.split(',')]
                    selected_shells = [shells[i] for i in indices if 0 <= i < len(shells)]
                except:
                    print("Seleção inválida.")
                    return

            if not selected_shells:
                print("Nenhum robô selecionado.")
                return

        except Exception as e:
            print(f"Erro ao listar AAS: {e}")
            return

        # 3. Configurar cada robô selecionado
        robots_to_simulate = []
        
        for shell in selected_shells:
            aas_id = shell['id']
            name = shell.get('idShort', 'Unnamed')
            print(f"\n[Config] A configurar {name}...")
            
            try:
                # Descobrir o Submodelo de Telemetria
                res = requests.get(f"{basyx_url}/shells/{b64(aas_id)}", timeout=5).json()
                sm_refs = res.get("submodels", [])
                tel_sm_id = None
                
                for r in sm_refs:
                    sid = r["keys"][0]["value"]
                    s_data = requests.get(f"{basyx_url}/submodels/{b64(sid)}").json()
                    if s_data.get("idShort") == "TelemetryData" or "Tel_" in sid:
                        tel_sm_id = sid
                        break

                if not tel_sm_id:
                    print(f"  > Erro: Submodelo 'TelemetryData' não encontrado para {name}!")
                    continue
                
                tel_url = f"{basyx_url}/submodels/{b64(tel_sm_id)}"

                # Obter nomes das juntas
                joints_res = requests.get(f"{tel_url}/submodel-elements/LiveJoints", timeout=5).json()
                joint_elements = joints_res.get("value", []) if isinstance(joints_res.get("value"), list) else joints_res.get("result", [])
                
                if not joint_elements:
                    print(f"  > Erro: Não foram encontradas juntas em 'LiveJoints' para {name}.")
                    continue
                
                joint_names = [j["idShort"] for j in joint_elements]
                print(f"  > Juntas detetadas: {joint_names}")
                
                robots_to_simulate.append({
                    "name": name,
                    "tel_url": tel_url,
                    "joints": joint_names
                })

            except Exception as e:
                print(f"  > Erro ao configurar {name}: {e}")

        if not robots_to_simulate:
            print("\nNenhum robô pôde ser configurado com sucesso.")
            return

        print(f"\nSimulação iniciada para {len(robots_to_simulate)} robôs (Movimento Sinusoidal).")
        print("Pressione Ctrl+C para parar.")
        
        t = 0
        while True:
            t += 0.1
            for robot in robots_to_simulate:
                robot_offset = robots_to_simulate.index(robot) * 2.0 # Diferença entre robôs
                
                for j_name in robot["joints"]:
                    # Offset por junta + offset por robô para movimentos variados
                    joint_offset = robot["joints"].index(j_name) * 0.5
                    val = math.sin(t + joint_offset + robot_offset) * 1.5
                    
                    prop_url = f"{robot['tel_url']}/submodel-elements/LiveJoints.{j_name}"
                    payload = {
                        "idShort": j_name,
                        "modelType": "Property",
                        "valueType": "xs:double",
                        "value": str(val)
                    }
                    
                    try:
                        requests.put(prop_url, json=payload, headers={"Content-Type": "application/json"}, timeout=0.5)
                    except:
                        pass

            print(f"\rA simular {len(robots_to_simulate)} robôs (t={t:.1f})...", end="")
            time.sleep(0.05) # 20Hz

    except KeyboardInterrupt:
        print("\nSimulação interrompida.")
    except Exception as e:
        print(f"\nErro Crítico: {e}")

if __name__ == "__main__":
    dummy_sync()
