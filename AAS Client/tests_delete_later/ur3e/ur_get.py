import rtde_receive
import time
import requests
import base64
import sys

ROBOT_IP = "192.168.2.2"
DEFAULT_BASYX_URL = "http://localhost:8081"

def b64(s):
    return base64.urlsafe_b64encode(s.encode()).decode().rstrip('=')

def monitor_ur3e():
    try:
        print("\n--- UR3e to AAS Sync ---")
        
        # 1. Obter URL do BaSyx
        basyx_url = input(f"Introduza a URL do servidor BaSyx [{DEFAULT_BASYX_URL}]: ").strip()
        if not basyx_url:
            basyx_url = DEFAULT_BASYX_URL
        
        # 2. Listar AAS disponíveis
        print(f"A obter lista de AAS de {basyx_url}...")
        try:
            # Tentar obter do repositório de shells
            shells_res = requests.get(f"{basyx_url}/shells", timeout=5).json()
            shells = shells_res if isinstance(shells_res, list) else shells_res.get("result", [])
            
            if not shells:
                print("Nenhum AAS encontrado no servidor.")
                return

            print("\nRobôs (AAS) encontrados:")
            for i, s in enumerate(shells):
                print(f"[{i}] {s.get('idShort', 'Sem Nome')} ({s.get('id')})")
            
            idx = input("\nEscolha o índice do robô para editar: ").strip()
            try:
                selected_shell = shells[int(idx)]
                aas_id = selected_shell['id']
            except (ValueError, IndexError):
                print("Seleção inválida.")
                return

        except Exception as e:
            print(f"Erro ao listar AAS: {e}")
            return

        # 3. Descobrir o Submodelo de Telemetria
        print(f"A procurar submodelo de telemetria para {aas_id}...")
        try:
            res = requests.get(f"{basyx_url}/shells/{b64(aas_id)}", timeout=5).json()
            sm_refs = res.get("submodels", [])
            tel_sm_id = None
            
            for r in sm_refs:
                sid = r["keys"][0]["value"]
                # Obter detalhes do submodelo para verificar o idShort
                s_data = requests.get(f"{basyx_url}/submodels/{b64(sid)}").json()
                if s_data.get("idShort") == "TelemetryData" or "Tel_" in sid:
                    tel_sm_id = sid
                    break

            if not tel_sm_id:
                print("Erro: Submodelo 'TelemetryData' não encontrado!")
                return
            
            tel_url = f"{basyx_url}/submodels/{b64(tel_sm_id)}"
            print(f"Sincronização ativa no submodelo: {tel_sm_id}")

            # 4. Obter nomes das juntas no AAS
            joints_res = requests.get(f"{tel_url}/submodel-elements/LiveJoints", timeout=5).json()
            joint_elements = joints_res.get("value", []) if isinstance(joints_res.get("value"), list) else joints_res.get("result", [])
            
            if not joint_elements:
                print("Erro: Não foram encontradas juntas na coleção 'LiveJoints'.")
                return
            
            joint_names = [j["idShort"] for j in joint_elements]
            print(f"Juntas detetadas no AAS: {joint_names}")
            if len(joint_names) != 6:
                print(f"Aviso: O AAS tem {len(joint_names)} juntas, mas o UR3e tem 6.")

        except Exception as e:
            print(f"Erro ao comunicar com BaSyx: {e}")
            return

        # 5. Ligar ao Robot Físico
        print(f"Conectando ao UR3e em {ROBOT_IP}...")
        rtde_r = rtde_receive.RTDEReceiveInterface(ROBOT_IP)
        print("Conectado! Sincronização em tempo real iniciada.")
        print("Pressione Ctrl+C para parar.")

        while True:
            # getActualQ() lê os radianos das 6 juntas
            q = rtde_r.getActualQ()

            # 6. Enviar para o AAS via PUT no elemento (Substituição de Elemento)
            for i in range(min(6, len(joint_names))):
                # Formato exato: LiveJoints.NomeDaJunta
                prop_url = f"{tel_url}/submodel-elements/LiveJoints.{joint_names[i]}"
                
                try:
                    val = float(q[i])
                    # Ao usar PUT num elemento, enviamos o objeto Property completo (mínimo)
                    payload = {
                        "idShort": joint_names[i],
                        "modelType": "Property",
                        "valueType": "xs:double",
                        "value": str(val)
                    }
                    res = requests.put(prop_url, json=payload, headers={"Content-Type": "application/json"}, timeout=1)

                    if res.status_code not in [200, 201, 204]:
                        print(f"\nErro ao atualizar {joint_names[i]} (PUT): {res.status_code}")
                except Exception as e:
                    pass

            formatted_joints = [round(j, 3) for j in q]
            print(f"\rSyncing UR3e -> AAS: {formatted_joints}", end="")

            time.sleep(0.1)  # 10Hz

    except KeyboardInterrupt:
        print("\nMonitorização interrompida pelo utilizador.")
    except Exception as e:
        print(f"\nErro Crítico: {e}")

if __name__ == "__main__":
    monitor_ur3e()
