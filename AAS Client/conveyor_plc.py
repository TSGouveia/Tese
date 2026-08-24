import requests
import base64
import time
import os
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich import box

console = Console()

REGISTRY_URL = "http://localhost:8082/shell-descriptors"
REPO_URL = "http://localhost:8081"

def encode_id(id_str):
    return base64.urlsafe_b64encode(id_str.encode()).decode().rstrip('=')

def get_active_kits():
    """Two-step discovery: List all shells, then fetch full descriptors for submodels."""
    try:
        # Step 1: Get all shells
        res = requests.get(REGISTRY_URL, timeout=5)
        if res.status_code != 200: return []
        shells = res.json().get("result", [])
        
        kits = []
        for s in shells:
            shell_id = s.get("id")
            if not shell_id: continue
            
            # Step 2: Get detailed descriptor for this shell from the Repository
            try:
                repo_url = f"{REPO_URL}/shells/{encode_id(shell_id)}"
                repo_res = requests.get(repo_url, timeout=2)
                if repo_res.status_code == 200:
                    shell_data = repo_res.json()
                    
                    # Look for the submodel reference that contains 'Pins'
                    pins_sm_id = None
                    for sm_ref in shell_data.get("submodels", []):
                        keys = sm_ref.get("keys", [])
                        if keys and len(keys) > 0:
                            sm_id = keys[0].get("value")
                            if sm_id and ("Pins_" in sm_id or "VirtualPins" in sm_id):
                                pins_sm_id = sm_id
                                break
                                
                    if pins_sm_id:
                        kits.append({
                            "idShort": s.get("idShort", "Unknown"),
                            "id": shell_id,
                            "pins_id": pins_sm_id
                        })
            except:
                continue
        return kits
    except Exception as e:
        return []

def get_pins(submodel_id):
    url = f"{REPO_URL}/submodels/{encode_id(submodel_id)}/submodel-elements?level=deep"
    try:
        res = requests.get(url, timeout=2)
        if res.status_code != 200: return [], []
        data = res.json()
        elements = data.get("result", data) if isinstance(data, dict) else data
        
        inputs = []
        outputs = []
        for coll in elements:
            if coll.get("idShort") == "Inputs":
                inputs = coll.get("value", [])
            elif coll.get("idShort") == "Outputs":
                outputs = coll.get("value", [])
        return inputs, outputs
    except:
        return [], []

def toggle_pin(submodel_id, collection, pin_id, current_val):
    new_val = not (str(current_val).lower() == "true")
    url = f"{REPO_URL}/submodels/{encode_id(submodel_id)}/submodel-elements/{collection}.{pin_id}"
    
    payload = {
        "idShort": pin_id,
        "modelType": "Property",
        "value": str(new_val).lower(),
        "valueType": "xs:boolean"
    }
    
    try:
        res = requests.put(url, json=payload, timeout=2, headers={"Content-Type": "application/json"})
        return res.status_code in [200, 201, 204]
    except:
        return False

def generate_dashboard(kit_name, inputs, outputs):
    table = Table(title=f"Dashboard: {kit_name}", box=box.ROUNDED, expand=True)
    table.add_column("Type", style="cyan")
    table.add_column("Pin ID", style="white")
    table.add_column("Value", justify="center")

    for p in inputs:
        val = p.get("value", "false")
        color = "green" if str(val).lower() == "true" else "red"
        table.add_row("INPUT (Sensor)", p.get("idShort"), f"[{color}]{val}[/]")
    
    table.add_section()
    
    for i, p in enumerate(outputs):
        val = p.get("value", "false")
        color = "green" if str(val).lower() == "true" else "red"
        table.add_row(f"OUTPUT (Actuator)", p.get("idShort"), f"[{color}]{val}[/]")
    
    return table

if __name__ == "__main__":
    try:
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            console.print(Panel.fit("[bold blue]AAS Kit Controller (BaSyx 2.0)[/]", border_style="blue"))
            console.print("[dim]Scanning Registry...[/dim]")
            
            kits = get_active_kits()
            if not kits:
                console.print("[red]No kits with 'VirtualPins' found.[/]")
                console.print("[dim]Ensure BaSyx is running and kits are deployed.[/dim]")
                time.sleep(3); continue
            
            for i, k in enumerate(kits): console.print(f"[[bold cyan]{i+1}[/]] {k['idShort']}")
            sel = IntPrompt.ask("\nSelect Kit to Control (0 to exit)", default=0)
            if sel == 0: break
            if sel > len(kits): continue
            
            kit = kits[sel-1]
            while True:
                inputs, outputs = get_pins(kit["pins_id"])
                os.system('cls' if os.name == 'nt' else 'clear')
                console.print(generate_dashboard(kit["idShort"], inputs, outputs))
                console.print("\n[bold]Actions:[/]")
                console.print("[white][R][/] Refresh Table")
                console.print("[white][0][/] Back to Kit Selection")
                
                # In Conveyor-Centric view, we control the INPUTS of the conveyor
                for i, p in enumerate(inputs):
                    console.print(f"[bold cyan][{i+1}][/] Toggle {p.get('idShort')}")
                
                opt = Prompt.ask("\nEnter Choice", choices=["R", "0", "r"] + [str(i+1) for i in range(len(inputs))])
                if opt == "0": break
                if opt.lower() == "r": continue
                
                idx = int(opt) - 1
                success = toggle_pin(kit["pins_id"], "Inputs", inputs[idx]["idShort"], inputs[idx]["value"])
                if not success: console.print("[red]Update failed![/]"); time.sleep(1)
                
    except KeyboardInterrupt:
        pass
