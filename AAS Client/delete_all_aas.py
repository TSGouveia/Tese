import requests
import base64

# --- CONFIGURAÇÃO ---
AAS_REGISTRY_URL = "http://localhost:8082/shell-descriptors"
AAS_SERVER_URL = "http://localhost:8081/shells"
SM_SERVER_URL = "http://localhost:8081/submodels"

def encode_id(id_str):
    """Codifica o ID para Base64 URL-safe."""
    return base64.urlsafe_b64encode(id_str.encode()).decode().rstrip("=")

def delete_all():
    print("=== BaSyx Full Cleanup (Shells & Submodels) ===")
    
    # 1. APAGAR SHELLS
    print("\n[1/2] A remover Shells...")
    try:
        res = requests.get(AAS_REGISTRY_URL)
        if res.status_code == 200:
            data = res.json()
            items = data.get("result", data) if isinstance(data, dict) else data
            
            count = 0
            for item in items:
                aas_id = item if isinstance(item, str) else item.get("id")
                if not aas_id or aas_id in ["paging_metadata", "result"]: continue
                
                encoded_id = encode_id(aas_id)
                print(f"   🗑️  Removendo Shell: {aas_id}")
                
                # Apagar do Repository e do Registry
                requests.delete(f"{AAS_SERVER_URL}/{encoded_id}")
                requests.delete(f"{AAS_REGISTRY_URL}/{encoded_id}")
                count += 1
            print(f"   ✅ {count} Shells removidas.")
        else:
            print(f"   ⚠️  Registry devolveu status {res.status_code}.")
    except Exception as e:
        print(f"   ❌ Erro ao apagar Shells: {e}")

    # 2. APAGAR SUBMODELS
    print("\n[2/2] A remover Submodels do Repository...")
    try:
        res_sm = requests.get(SM_SERVER_URL)
        if res_sm.status_code == 200:
            data_sm = res_sm.json()
            items_sm = data_sm.get("result", data_sm) if isinstance(data_sm, dict) else data_sm
            
            count_sm = 0
            for item_sm in items_sm:
                sm_id = item_sm if isinstance(item_sm, str) else item_sm.get("id")
                if not sm_id: continue
                
                encoded_sm_id = encode_id(sm_id)
                print(f"   🗑️  Removendo Submodel: {sm_id}")
                requests.delete(f"{SM_SERVER_URL}/{encoded_sm_id}")
                count_sm += 1
            print(f"   ✅ {count_sm} Submodels removidos.")
    except Exception as e:
        print(f"   ❌ Erro ao apagar Submodels: {e}")

    print("\n✨ Ambiente limpo!")

if __name__ == "__main__":
    confirm = input("⚠️  ATENÇÃO: Isto vai apagar TODOS os robôs. Continuar? (s/n): ").lower()
    if confirm == 's':
        delete_all()
    else:
        print("Operação cancelada.")
