import os
import json
import base64
import requests
import datetime
import math
import time
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm, FloatPrompt
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich import print as rprint

# --- CONFIGURATION ---
AAS_REGISTRY_URL = "http://localhost:8082/shell-descriptors"
SM_REGISTRY_URL = "http://localhost:8083/submodel-descriptors"
AAS_REPO_URL = "http://localhost:8081/shells"
SM_REPO_URL = "http://localhost:8081/submodels"
BACKUP_DIR = Path("backups")

console = Console()

def encode_id(id_str):
    """Encodes the ID to Base64 URL-safe for API calls."""
    return base64.urlsafe_b64encode(id_str.encode()).decode().rstrip("=")

def get_timestamp():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

class AASManager:
    def __init__(self):
        BACKUP_DIR.mkdir(exist_ok=True)

    def fetch_all(self, url):
        """Fetches all items from a registry or repo, handling pagination."""
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, dict) and "result" in data:
                    return data["result"]
                return data if isinstance(data, list) else []
            return []
        except Exception:
            return []

    def backup(self):
        timestamp = get_timestamp()
        current_backup_path = BACKUP_DIR / f"backup_{timestamp}"
        aas_path = current_backup_path / "shells"
        sm_path = current_backup_path / "submodels"
        
        aas_path.mkdir(parents=True, exist_ok=True)
        sm_path.mkdir(parents=True, exist_ok=True)

        shells = self.fetch_all(AAS_REGISTRY_URL)
        sm_descriptors = self.fetch_all(SM_REGISTRY_URL)
        submodels = self.fetch_all(SM_REPO_URL)

        if not shells:
            rprint("[yellow]No shells found in registry.[/yellow]")
            return

        with Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn(), console=console) as progress:
            t1 = progress.add_task("[cyan]Backing up Shells...", total=len(shells))
            for s in shells:
                sid = s.get("id")
                encoded = encode_id(sid)
                try:
                    res = requests.get(f"{AAS_REPO_URL}/{encoded}")
                    if res.status_code == 200:
                        with open(aas_path / f"{s.get('idShort')}_{encoded[:8]}.json", "w") as f: json.dump(res.json(), f, indent=4)
                        with open(aas_path / f"{s.get('idShort')}_{encoded[:8]}.desc.json", "w") as f: json.dump(s, f, indent=4)
                except: pass
                progress.update(t1, advance=1)

            t2 = progress.add_task("[magenta]Backing up Submodels...", total=len(submodels))
            for sm in submodels:
                smid = sm.get("id")
                encoded = encode_id(smid)
                try:
                    res = requests.get(f"{SM_REPO_URL}/{encoded}")
                    if res.status_code == 200:
                        with open(sm_path / f"{sm.get('idShort')}_{encoded[:8]}.json", "w") as f: json.dump(res.json(), f, indent=4)
                except: pass
                progress.update(t2, advance=1)
        rprint(Panel(f"[bold green]Backup saved successfully![/bold green]\nLocation: {current_backup_path}"))

    def restore(self):
        backups = sorted([d for d in BACKUP_DIR.iterdir() if d.is_dir()], reverse=True)
        if not backups:
            rprint("[yellow]No backups found.[/yellow]")
            return

        table = Table(title="Available Backups")
        table.add_column("ID", justify="right", style="cyan")
        table.add_column("Folder Name", style="white")
        for i, b in enumerate(backups): table.add_row(str(i+1), b.name)
        console.print(table)
        
        choice = Prompt.ask("Choose a backup ID", choices=[str(i+1) for i in range(len(backups))], default="1")
        selected_backup = backups[int(choice)-1]

        shell_files = list((selected_backup / "shells").glob("*.json"))
        sm_files = list((selected_backup / "submodels").glob("*.json"))

        with Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn(), console=console) as progress:
            # 1. Submodel Data
            sm_data_files = [f for f in sm_files if not f.name.endswith(".desc.json")]
            t1 = progress.add_task("[magenta]Restoring Submodel Data...", total=len(sm_data_files))
            for f in sm_data_files:
                try:
                    with open(f, "r") as j: requests.post(SM_REPO_URL, json=json.load(j))
                except: pass
                progress.update(t1, advance=1)

            # 2. SM Descriptors
            sm_desc_files = [f for f in sm_files if f.name.endswith(".desc.json")]
            t2 = progress.add_task("[yellow]Restoring SM Registry...", total=len(sm_desc_files))
            for f in sm_desc_files:
                try:
                    with open(f, "r") as j: requests.post(SM_REGISTRY_URL, json=json.load(j))
                except: pass
                progress.update(t2, advance=1)

            # 3. Shells
            shell_data_files = [f for f in shell_files if not f.name.endswith(".desc.json")]
            t3 = progress.add_task("[cyan]Restoring Shells & Registry...", total=len(shell_data_files))
            for f in shell_data_files:
                try:
                    with open(f, "r") as j: requests.post(AAS_REPO_URL, json=json.load(j))
                    d = f.with_suffix(".desc.json")
                    if d.exists():
                        with open(d, "r") as j: requests.post(AAS_REGISTRY_URL, json=json.load(j))
                except: pass
                progress.update(t3, advance=1)

        rprint("[bold green]Restoration process finished![/bold green]")

    def organize_grid(self):
        spacing = FloatPrompt.ask("Enter spacing between robots (meters)", default=2.0)
        shells = self.fetch_all(AAS_REGISTRY_URL)
        
        if not shells:
            rprint("[bold red]ERROR: No robots found in registry.[/bold red]")
            return

        rprint(f"[cyan]Organizing {len(shells)} robots. (Z is UP, grid on XY plane)[/cyan]")
        cols = math.ceil(math.sqrt(len(shells)))

        for i, s in enumerate(shells):
            id_short = s.get("idShort", "Unknown")
            shell_id = s.get("id")
            submodel_id = None

            # 1. Registry Lookup
            try:
                res_desc = requests.get(f"{AAS_REGISTRY_URL}/{encode_id(shell_id)}", timeout=5).json()
                for sm_desc in res_desc.get("submodelDescriptors", []):
                    if sm_desc.get("idShort") == "PositionData":
                        submodel_id = sm_desc.get("id")
                        break
            except: pass
            
            # 2. Prediction Fallback (Pos_{idShort})
            if not submodel_id:
                pred = f"https://acplt.org/Submodels/Pos_{id_short}"
                if requests.get(f"{SM_REPO_URL}/{encode_id(pred)}", timeout=2).status_code == 200:
                    submodel_id = pred

            if submodel_id:
                row, col = i // cols, i % cols
                x, y = col * spacing, row * spacing
                encoded_sm = encode_id(submodel_id)
                headers = {"Content-Type": "application/json"}
                
                payload_x = {"idShort": "Pos_X", "modelType": "Property", "value": str(x), "valueType": "xs:double"}
                payload_y = {"idShort": "Pos_Y", "modelType": "Property", "value": str(y), "valueType": "xs:double"}
                
                requests.put(f"{SM_REPO_URL}/{encoded_sm}/submodel-elements/Pos_X", json=payload_x, headers=headers)
                requests.put(f"{SM_REPO_URL}/{encoded_sm}/submodel-elements/Pos_Y", json=payload_y, headers=headers)
                rprint(f"  [green]✅[/green] {id_short} moved to ({x}, {y})")
            else:
                rprint(f"  [yellow]⚠️[/yellow] {id_short}: PositionData not found.")

        rprint("[bold green]Grid organization finished![/bold green]")

    def simulate_movement(self):
        shells = self.fetch_all(AAS_REGISTRY_URL)
        if not shells:
            rprint("[bold red]No robots found to simulate.[/bold red]")
            return

        rprint("\n[bold cyan]Select robots for sinusoidal simulation:[/bold cyan]")
        for i, s in enumerate(shells):
            rprint(f"  [{i}] {s.get('idShort')} ({s.get('id')})")
        
        selection = Prompt.ask("\nEnter indices (e.g. 0,1,2) or 'all'", default="all").strip().lower()
        selected_shells = shells if selection == 'all' else [shells[int(x.strip())] for x in selection.split(',') if 0 <= int(x.strip()) < len(shells)]

        robots_to_sim = []
        for s in selected_shells:
            name = s.get('idShort')
            # Find TelemetryData
            tel_id = None
            try:
                res_desc = requests.get(f"{AAS_REGISTRY_URL}/{encode_id(s['id'])}", timeout=5).json()
                for sm in res_desc.get("submodelDescriptors", []):
                    if sm.get("idShort") == "TelemetryData":
                        tel_id = sm.get("id")
                        break
            except: pass
            
            if not tel_id:
                pred = f"https://acplt.org/Submodels/Tel_{name}"
                if requests.get(f"{SM_REPO_URL}/{encode_id(pred)}", timeout=2).status_code == 200: tel_id = pred

            if tel_id:
                try:
                    res_joints = requests.get(f"{SM_REPO_URL}/{encode_id(tel_id)}/submodel-elements/LiveJoints", timeout=5).json()
                    joint_list = res_joints.get("value", []) if isinstance(res_joints.get("value"), list) else res_joints.get("result", [])
                    robots_to_sim.append({
                        "name": name,
                        "url": f"{SM_REPO_URL}/{encode_id(tel_id)}/submodel-elements/LiveJoints",
                        "joints": [j["idShort"] for j in joint_list]
                    })
                    rprint(f"  [green]+[/green] {name} configured with {len(joint_list)} joints.")
                except: pass

        if not robots_to_sim:
            rprint("[bold red]No telemetry submodels found for simulation.[/bold red]")
            return

        rprint(f"\n[bold green]Starting simulation for {len(robots_to_sim)} robots...[/bold green]")
        rprint("[dim]Press Ctrl+C to stop.[/dim]")
        
        t = 0
        try:
            while True:
                t += 0.1
                for i, robot in enumerate(robots_to_sim):
                    for j_idx, j_name in enumerate(robot["joints"]):
                        val = math.sin(t + j_idx * 0.5 + i * 2.0) * 1.5
                        payload = {"idShort": j_name, "modelType": "Property", "valueType": "xs:double", "value": str(val)}
                        try: requests.put(f"{robot['url']}.{j_name}", json=payload, timeout=0.5)
                        except: pass
                rprint(f"\r[cyan]Simulating... time={t:.1f}[/cyan]", end="")
                time.sleep(0.05)
        except KeyboardInterrupt:
            rprint("\n[yellow]Simulation stopped.[/yellow]")

    def cleanup(self):
        if not Confirm.ask("[bold red]DANGER: DELETE ALL DATA?[/bold red]"): return
        with Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn(), console=console) as progress:
            t = progress.add_task("[red]Cleaning environment...", total=2)
            for url, repo in [(AAS_REGISTRY_URL, AAS_REPO_URL), (SM_REGISTRY_URL, SM_REPO_URL)]:
                items = self.fetch_all(url)
                for item in items:
                    idx = item if isinstance(item, str) else item.get("id")
                    if not idx or idx in ["paging_metadata", "result"]: continue
                    requests.delete(f"{repo}/{encode_id(idx)}")
                    requests.delete(f"{url}/{encode_id(idx)}")
                progress.update(t, advance=1)
        rprint("[bold green]All repositories and registries are now clean![/bold green]")

    def run(self):
        while True:
            console.clear()
            rprint(Panel.fit("[bold blue]AAS Manager Pro[/bold blue]\n[dim]Complete AAS & Robot Ecosystem Control[/dim]", border_style="blue"))
            rprint("1. [bold cyan]Backup[/bold cyan] (Download All Data)")
            rprint("2. [bold green]Restore[/bold green] (Upload from Backup)")
            rprint("3. [bold yellow]Organize Grid[/bold yellow] (Space out Robots)")
            rprint("4. [bold magenta]Simulate Movement[/bold magenta] (Sinusoidal Test)")
            rprint("5. [bold red]Cleanup[/bold red] (Wipe Everything)")
            rprint("6. [bold white]Exit[/bold white]")
            
            choice = Prompt.ask("\nSelect Option", choices=["1", "2", "3", "4", "5", "6"])
            if choice == "1": self.backup()
            elif choice == "2": self.restore()
            elif choice == "3": self.organize_grid()
            elif choice == "4": self.simulate_movement()
            elif choice == "5": self.cleanup()
            elif choice == "6": break
            if choice != "4": Prompt.ask("\nPress Enter to return to menu")

if __name__ == "__main__":
    manager = AASManager()
    try: manager.run()
    except KeyboardInterrupt: pass
