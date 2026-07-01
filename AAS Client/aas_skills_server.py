import time
import base64
import urllib.parse
import threading
import random
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

console = Console()

# --- CONFIGURATION ---
AAS_SERVER = "http://localhost:8081"
PORT = 8080

def encode_id(id_str):
    """Encodes an AAS identifier to a URL-safe Base64 string for BaSyx API calls."""
    return base64.urlsafe_b64encode(id_str.encode()).decode().rstrip('=')

# --- AAS REST API HELPERS ---
def get_pin(kit_name, collection, pin_id):
    """
    Reads the value of a virtual pin from the AAS VirtualPins submodel.
    Maps:
      - 'Inputs' (PLC inputs / sensors) -> reads from AAS 'Outputs' (simulation outputs)
      - 'Outputs' (PLC outputs / actuators) -> reads from AAS 'Inputs' (simulation inputs)
    """
    aas_collection = "Outputs" if collection == "Inputs" else "Inputs"
    submodel_id = f"https://acplt.org/Submodels/Pins_{kit_name}"
    url = f"{AAS_SERVER}/submodels/{encode_id(submodel_id)}/submodel-elements/{aas_collection}.{pin_id}"
    try:
        res = requests.get(url, timeout=2)
        if res.status_code == 200:
            val = res.json().get("value")
            # Convert string representation of boolean if necessary
            if isinstance(val, str):
                return val.lower() == "true"
            return bool(val)
    except Exception as e:
        console.print(f"[red]Error reading pin {pin_id} from {kit_name}: {e}[/]")
    return False

def set_pin(kit_name, collection, pin_id, value):
    """
    Writes the value of a virtual pin to the AAS VirtualPins submodel.
    Maps:
      - 'Inputs' (PLC inputs / sensors) -> writes to AAS 'Outputs' (simulation outputs)
      - 'Outputs' (PLC outputs / actuators) -> writes to AAS 'Inputs' (simulation inputs)
    """
    aas_collection = "Outputs" if collection == "Inputs" else "Inputs"
    submodel_id = f"https://acplt.org/Submodels/Pins_{kit_name}"
    url = f"{AAS_SERVER}/submodels/{encode_id(submodel_id)}/submodel-elements/{aas_collection}.{pin_id}"
    payload = {
        "idShort": pin_id,
        "modelType": "Property",
        "valueType": "xs:boolean",
        "value": str(value).lower()
    }
    try:
        res = requests.put(url, json=payload, timeout=2, headers={"Content-Type": "application/json"})
        return res.status_code in [200, 201, 204]
    except Exception as e:
        console.print(f"[red]Error writing pin {pin_id} to {kit_name}: {e}[/]")
    return False

def is_product_present(kit_name, pin_id):
    """
    Checks if a product is present on a specific sensor.
    Product sensors in the AAS are mapped as Active Low:
      - False (0) -> Product Present
      - True (1) -> Product Absent
    """
    raw_val = get_pin(kit_name, "Inputs", pin_id)
    return not raw_val


# --- CONVEYOR ALIGNMENT SUB-SKILLS ---
def align_conveyor_b(angle):
    """Aligns Conveyor B (rotative) to 0 or 90 degrees."""
    sensor_pin = f"Conveyor_B_Rotate{angle}"
    motor_pin = "Conveyor_B_CW" if angle == 0 else "Conveyor_B_CCW"
    
    if get_pin("Conveyor_B", "Inputs", sensor_pin):
        return True

    console.print(f"[cyan]Aligning Conveyor B to {angle}° using {motor_pin}...[/]")
    set_pin("Conveyor_B", "Outputs", motor_pin, True)
    
    start = time.time()
    while not get_pin("Conveyor_B", "Inputs", sensor_pin):
        if time.time() - start > 15.0:
            console.print(f"[red]Timeout aligning Conveyor B with {motor_pin}![/]")
            set_pin("Conveyor_B", "Outputs", motor_pin, False)
            return False
        time.sleep(0.1)
        
    set_pin("Conveyor_B", "Outputs", motor_pin, False)
    console.print(f"[green]Conveyor B aligned to {angle}°.[/]")
    return True

def align_conveyor_d(angle):
    """Aligns Conveyor D (rotative) to 0 or 90 degrees."""
    sensor_pin = f"Conveyor_D_Rotate{angle}"
    motor_pin = "Conveyor_D_CW" if angle == 0 else "Conveyor_D_CCW"
    
    if get_pin("Conveyor_D", "Inputs", sensor_pin):
        return True

    console.print(f"[cyan]Aligning Conveyor D to {angle}° using {motor_pin}...[/]")
    set_pin("Conveyor_D", "Outputs", motor_pin, True)
    
    start = time.time()
    while not get_pin("Conveyor_D", "Inputs", sensor_pin):
        if time.time() - start > 15.0:
            console.print(f"[red]Timeout aligning Conveyor D with {motor_pin}![/]")
            set_pin("Conveyor_D", "Outputs", motor_pin, False)
            return False
        time.sleep(0.1)
        
    set_pin("Conveyor_D", "Outputs", motor_pin, False)
    console.print(f"[green]Conveyor D aligned to {angle}°.[/]")
    return True

def align_conveyor_f(side):
    """Translates Conveyor F to 'Left' or 'Right' side."""
    sensor_pin = f"Sensor_{side}"
    move_pin = f"Conveyor_F_{side}"
    if get_pin("Conveyor_F", "Inputs", sensor_pin):
        return True

    console.print(f"[cyan]Translating Conveyor F to {side}...[/]")
    set_pin("Conveyor_F", "Outputs", move_pin, True)
    
    start = time.time()
    while not get_pin("Conveyor_F", "Inputs", sensor_pin):
        if time.time() - start > 15.0:
            console.print(f"[red]Timeout translating Conveyor F to {side}![/]")
            set_pin("Conveyor_F", "Outputs", move_pin, False)
            return False
        time.sleep(0.1)
        
    set_pin("Conveyor_F", "Outputs", move_pin, False)
    console.print(f"[green]Conveyor F translated to {side}.[/]")
    return True


# --- CHOREOGRAPHY SKILLS (ORCHESTRATION) ---
def passadeiraAB():
    console.print("[yellow]Skill: [bold]passadeiraAB[/bold] started.[/]")
    if not is_product_present("Conveyor_A", "Sensor_Product"):
        console.print("[red]Aborted: No product detected on Conveyor A.[/]")
        return "aborted: no product on A"
    if not align_conveyor_b(90):
        return "failed to align B"
    
    set_pin("Conveyor_A", "Outputs", "Move_Conveyor_OUT", True)
    set_pin("Conveyor_B", "Outputs", "Move_Conveyor_OUT", True)
    
    start = time.time()
    while not is_product_present("Conveyor_B", "Conveyor_B_Product"):
        if time.time() - start > 15.0:
            console.print("[red]Timeout in passadeiraAB (Product not detected on B)[/]")
            break
        time.sleep(0.1)
        
    set_pin("Conveyor_A", "Outputs", "Move_Conveyor_OUT", False)
    set_pin("Conveyor_B", "Outputs", "Move_Conveyor_OUT", False)
    console.print("[green]Skill: [bold]passadeiraAB[/bold] completed.[/]")
    return "skill AB done"

def passadeiraBC():
    console.print("[yellow]Skill: [bold]passadeiraBC[/bold] started.[/]")
    if not is_product_present("Conveyor_B", "Conveyor_B_Product"):
        console.print("[red]Aborted: No product detected on Conveyor B.[/]")
        return "aborted: no product on B"
    if not align_conveyor_b(0):
        return "failed to align B"
        
    set_pin("Conveyor_B", "Outputs", "Move_Conveyor_OUT", True)
    set_pin("Conveyor_C", "Outputs", "Move_Conveyor_OUT", True)
    
    start = time.time()
    while not is_product_present("Conveyor_C", "Sensor_Product"):
        if time.time() - start > 15.0:
            console.print("[red]Timeout in passadeiraBC (Product not detected on C)[/]")
            break
        time.sleep(0.1)
        
    set_pin("Conveyor_B", "Outputs", "Move_Conveyor_OUT", False)
    set_pin("Conveyor_C", "Outputs", "Move_Conveyor_OUT", False)
    console.print("[green]Skill: [bold]passadeiraBC[/bold] completed.[/]")
    return "skill BC done"

def passadeiraCD():
    console.print("[yellow]Skill: [bold]passadeiraCD[/bold] started.[/]")
    if not is_product_present("Conveyor_C", "Sensor_Product"):
        console.print("[red]Aborted: No product detected on Conveyor C.[/]")
        return "aborted: no product on C"
    if not align_conveyor_d(90):
        return "failed to align D"
        
    set_pin("Conveyor_C", "Outputs", "Move_Conveyor_OUT", True)
    set_pin("Conveyor_D", "Outputs", "Move_Conveyor_IN", True)
    
    start = time.time()
    while not is_product_present("Conveyor_D", "Conveyor_D_Product"):
        if time.time() - start > 15.0:
            console.print("[red]Timeout in passadeiraCD (Product not detected on D)[/]")
            break
        time.sleep(0.1)
        
    set_pin("Conveyor_C", "Outputs", "Move_Conveyor_OUT", False)
    set_pin("Conveyor_D", "Outputs", "Move_Conveyor_IN", False)
    console.print("[green]Skill: [bold]passadeiraCD[/bold] completed.[/]")
    return "skill CD done"

def passadeiraDE():
    console.print("[yellow]Skill: [bold]passadeiraDE[/bold] started.[/]")
    if not is_product_present("Conveyor_D", "Conveyor_D_Product"):
        console.print("[red]Aborted: No product detected on Conveyor D.[/]")
        return "aborted: no product on D"
    if not align_conveyor_d(0):
        return "failed to align D"
        
    set_pin("Conveyor_D", "Outputs", "Move_Conveyor_IN", True)
    set_pin("Conveyor_E", "Outputs", "Move_Conveyor_OUT", True)
    
    start = time.time()
    while not is_product_present("Conveyor_E", "Sensor_Product"):
        if time.time() - start > 15.0:
            console.print("[red]Timeout in passadeiraDE (Product not detected on E)[/]")
            break
        time.sleep(0.1)
        
    set_pin("Conveyor_D", "Outputs", "Move_Conveyor_IN", False)
    set_pin("Conveyor_E", "Outputs", "Move_Conveyor_OUT", False)
    console.print("[green]Skill: [bold]passadeiraDE[/bold] completed.[/]")
    return "skill DE done"

def passadeiraEF():
    console.print("[yellow]Skill: [bold]passadeiraEF[/bold] started.[/]")
    if not is_product_present("Conveyor_E", "Sensor_Product"):
        console.print("[red]Aborted: No product detected on Conveyor E.[/]")
        return "aborted: no product on E"
    # E is on the Left of F
    if not align_conveyor_f("Right"):
        return "failed to align F"
        
    set_pin("Conveyor_E", "Outputs", "Move_Conveyor_OUT", True)
    set_pin("Conveyor_F", "Outputs", "Conveyor_F_IN", True)
    
    start = time.time()
    while not is_product_present("Conveyor_F", "Sensor_Product"):
        if time.time() - start > 15.0:
            console.print("[red]Timeout in passadeiraEF (Product not detected on F)[/]")
            break
        time.sleep(0.1)
        
    set_pin("Conveyor_E", "Outputs", "Move_Conveyor_OUT", False)
    set_pin("Conveyor_F", "Outputs", "Conveyor_F_IN", False)
    console.print("[green]Skill: [bold]passadeiraEF[/bold] completed.[/]")
    return "skill EF done"

def passadeiraFA():
    console.print("[yellow]Skill: [bold]passadeiraFA[/bold] started.[/]")
    if not is_product_present("Conveyor_F", "Sensor_Product"):
        console.print("[red]Aborted: No product detected on Conveyor F.[/]")
        return "aborted: no product on F"
    # A is on the Right of F
    if not align_conveyor_f("Left"):
        return "failed to align F"
        
    set_pin("Conveyor_F", "Outputs", "Conveyor_F_Out", True)
    set_pin("Conveyor_A", "Outputs", "Move_Conveyor_OUT", True)
    
    start = time.time()
    while not is_product_present("Conveyor_A", "Sensor_Product"):
        if time.time() - start > 15.0:
            console.print("[red]Timeout in passadeiraFA (Product not detected on A)[/]")
            break
        time.sleep(0.1)
        
    set_pin("Conveyor_F", "Outputs", "Conveyor_F_Out", False)
    set_pin("Conveyor_A", "Outputs", "Move_Conveyor_OUT", False)
    console.print("[green]Skill: [bold]passadeiraFA[/bold] completed.[/]")
    return "skill FA done"

def passadeiraBA():
    console.print("[yellow]Skill: [bold]passadeiraBA[/bold] started.[/]")
    if not is_product_present("Conveyor_B", "Conveyor_B_Product"):
        console.print("[red]Aborted: No product detected on Conveyor B.[/]")
        return "aborted: no product on B"
    if not align_conveyor_b(90):
        return "failed to align B"
    set_pin("Conveyor_B", "Outputs", "Move_Conveyor_IN", True)
    set_pin("Conveyor_A", "Outputs", "Move_Conveyor_IN", True)
    
    start = time.time()
    while not is_product_present("Conveyor_A", "Sensor_Product"):
        if time.time() - start > 15.0:
            console.print("[red]Timeout in passadeiraBA (Product not detected on A)[/]")
            break
        time.sleep(0.1)
        
    set_pin("Conveyor_B", "Outputs", "Move_Conveyor_IN", False)
    set_pin("Conveyor_A", "Outputs", "Move_Conveyor_IN", False)
    console.print("[green]Skill: [bold]passadeiraBA[/bold] completed.[/]")
    return "skill BA done"

def passadeiraCB():
    console.print("[yellow]Skill: [bold]passadeiraCB[/bold] started.[/]")
    if not is_product_present("Conveyor_C", "Sensor_Product"):
        console.print("[red]Aborted: No product detected on Conveyor C.[/]")
        return "aborted: no product on C"
    if not align_conveyor_b(0):
        return "failed to align B"
    set_pin("Conveyor_C", "Outputs", "Move_Conveyor_IN", True)
    set_pin("Conveyor_B", "Outputs", "Move_Conveyor_IN", True)
    
    start = time.time()
    while not is_product_present("Conveyor_B", "Conveyor_B_Product"):
        if time.time() - start > 15.0:
            console.print("[red]Timeout in passadeiraCB (Product not detected on B)[/]")
            break
        time.sleep(0.1)
        
    set_pin("Conveyor_C", "Outputs", "Move_Conveyor_IN", False)
    set_pin("Conveyor_B", "Outputs", "Move_Conveyor_IN", False)
    console.print("[green]Skill: [bold]passadeiraCB[/bold] completed.[/]")
    return "skill CB done"

def passadeiraDC():
    console.print("[yellow]Skill: [bold]passadeiraDC[/bold] started.[/]")
    if not is_product_present("Conveyor_D", "Conveyor_D_Product"):
        console.print("[red]Aborted: No product detected on Conveyor D.[/]")
        return "aborted: no product on D"
    if not align_conveyor_d(90):
        return "failed to align D"
    set_pin("Conveyor_D", "Outputs", "Move_Conveyor_OUT", True)
    set_pin("Conveyor_C", "Outputs", "Move_Conveyor_IN", True)
    
    start = time.time()
    while not is_product_present("Conveyor_C", "Sensor_Product"):
        if time.time() - start > 15.0:
            console.print("[red]Timeout in passadeiraDC (Product not detected on C)[/]")
            break
        time.sleep(0.1)
        
    set_pin("Conveyor_D", "Outputs", "Move_Conveyor_OUT", False)
    set_pin("Conveyor_C", "Outputs", "Move_Conveyor_IN", False)
    console.print("[green]Skill: [bold]passadeiraDC[/bold] completed.[/]")
    return "skill DC done"

def passadeiraED():
    console.print("[yellow]Skill: [bold]passadeiraED[/bold] started.[/]")
    if not is_product_present("Conveyor_E", "Sensor_Product"):
        console.print("[red]Aborted: No product detected on Conveyor E.[/]")
        return "aborted: no product on E"
    if not align_conveyor_d(0):
        return "failed to align D"
    set_pin("Conveyor_E", "Outputs", "Move_Conveyor_IN", True)
    set_pin("Conveyor_D", "Outputs", "Move_Conveyor_OUT", True)
    
    start = time.time()
    while not is_product_present("Conveyor_D", "Conveyor_D_Product"):
        if time.time() - start > 15.0:
            console.print("[red]Timeout in passadeiraED (Product not detected on D)[/]")
            break
        time.sleep(0.1)
        
    set_pin("Conveyor_E", "Outputs", "Move_Conveyor_IN", False)
    set_pin("Conveyor_D", "Outputs", "Move_Conveyor_OUT", False)
    console.print("[green]Skill: [bold]passadeiraED[/bold] completed.[/]")
    return "skill ED done"

def passadeiraFE():
    console.print("[yellow]Skill: [bold]passadeiraFE[/bold] started.[/]")
    if not is_product_present("Conveyor_F", "Sensor_Product"):
        console.print("[red]Aborted: No product detected on Conveyor F.[/]")
        return "aborted: no product on F"
    if not align_conveyor_f("Right"):
        return "failed to align F"
    set_pin("Conveyor_F", "Outputs", "Conveyor_F_Out", True)
    set_pin("Conveyor_E", "Outputs", "Move_Conveyor_IN", True)
    
    start = time.time()
    while not is_product_present("Conveyor_E", "Sensor_Product"):
        if time.time() - start > 15.0:
            console.print("[red]Timeout in passadeiraFE (Product not detected on E)[/]")
            break
        time.sleep(0.1)
        
    set_pin("Conveyor_F", "Outputs", "Conveyor_F_Out", False)
    set_pin("Conveyor_E", "Outputs", "Move_Conveyor_IN", False)
    console.print("[green]Skill: [bold]passadeiraFE[/bold] completed.[/]")
    return "skill FE done"

def passadeiraAF():
    console.print("[yellow]Skill: [bold]passadeiraAF[/bold] started.[/]")
    if not is_product_present("Conveyor_A", "Sensor_Product"):
        console.print("[red]Aborted: No product detected on Conveyor A.[/]")
        return "aborted: no product on A"
    if not align_conveyor_f("Left"):
        return "failed to align F"
    set_pin("Conveyor_A", "Outputs", "Move_Conveyor_IN", True)
    set_pin("Conveyor_F", "Outputs", "Conveyor_F_IN", True)
    
    start = time.time()
    while not is_product_present("Conveyor_F", "Sensor_Product"):
        if time.time() - start > 15.0:
            console.print("[red]Timeout in passadeiraAF (Product not detected on F)[/]")
            break
        time.sleep(0.1)
        
    set_pin("Conveyor_A", "Outputs", "Move_Conveyor_IN", False)
    set_pin("Conveyor_F", "Outputs", "Conveyor_F_IN", False)
    console.print("[green]Skill: [bold]passadeiraAF[/bold] completed.[/]")
    return "skill AF done"


# --- PUNCH STATION SKILLS ---
def estacao(modo, processing_time=3.0):
    """
    Controls the Punch Station.
    modo: 0 -> Drill, 1 -> Screw, 2 -> Calibrate
    processing_time: duration of the drill/screw process in seconds
    """
    console.print(f"[yellow]Skill: [bold]estacao[/bold] (modo={modo}, time={processing_time}) started.[/]")
    
    if modo in [0, 1]:
        if not is_product_present("Conveyor_C", "Sensor_Product"):
            console.print("[red]Aborted: No product detected on Conveyor C under the Punch Station.[/]")
            return "aborted: no product on C"
    
    def move_to_sensor(actuator, sensor, state=True, timeout=10.0):
        set_pin("Punch_FMS", "Outputs", actuator, True)
        start = time.time()
        while get_pin("Punch_FMS", "Inputs", sensor) != state:
            if time.time() - start > timeout:
                console.print(f"[red]Timeout waiting for {sensor} to be {state}![/]")
                set_pin("Punch_FMS", "Outputs", actuator, False)
                return False
            time.sleep(0.1)
        set_pin("Punch_FMS", "Outputs", actuator, False)
        return True

    if modo == 2:  # Calibrate
        console.print("[cyan]Calibrating Punch Station...[/]")
        if not move_to_sensor("Punch_Up", "Sensor_Up"):
            return "failed to calibrate (Up)"
        if not move_to_sensor("Punch_Backward", "Sensor_Backward"):
            return "failed to calibrate (Backward)"
        console.print("[green]Punch Station calibrated successfully.[/]")
        return "skill done"

    elif modo == 0:  # Drill
        # Check home position
        if not get_pin("Punch_FMS", "Inputs", "Sensor_Up") or not get_pin("Punch_FMS", "Inputs", "Sensor_Backward"):
            console.print("[cyan]Punch not in home position. Pre-calibrating...[/]")
            estacao(2)
            
        console.print("[cyan]Starting Drill sequence...[/]")
        # 1. Move Forward
        if not move_to_sensor("Punch_Forward", "Sensor_Forward"):
            return "failed to move forward"
        # 2. Start rotating drill
        set_pin("Punch_FMS", "Outputs", "Punch_Rotate", True)
        # 3. Move Down
        if not move_to_sensor("Punch_Down", "Sensor_Down"):
            set_pin("Punch_FMS", "Outputs", "Punch_Rotate", False)
            return "failed to move down"
        # 4. Wait for processing_time
        time.sleep(processing_time)
        # 5. Stop rotating drill
        set_pin("Punch_FMS", "Outputs", "Punch_Rotate", False)
        # 6. Move Up
        if not move_to_sensor("Punch_Up", "Sensor_Up"):
            return "failed to move up"
        # 7. Move Backward
        if not move_to_sensor("Punch_Backward", "Sensor_Backward"):
            return "failed to move backward"
        console.print("[green]Drill operation completed successfully.[/]")
        return "skill done"

    elif modo == 1:  # Screw
        # Check home position
        if not get_pin("Punch_FMS", "Inputs", "Sensor_Up") or not get_pin("Punch_FMS", "Inputs", "Sensor_Backward"):
            console.print("[cyan]Punch not in home position. Pre-calibrating...[/]")
            estacao(2)
            
        console.print("[cyan]Starting Screw sequence...[/]")
        # 1. Move Forward
        if not move_to_sensor("Punch_Forward", "Sensor_Forward"):
            return "failed to move forward"
        # 2. Move Down
        if not move_to_sensor("Punch_Down", "Sensor_Down"):
            return "failed to move down"
        # 3. Start rotating brush
        set_pin("Punch_FMS", "Outputs", "Punch_Rotate", True)
        # 4. Wait for processing_time
        time.sleep(processing_time)
        # 5. Stop rotating
        set_pin("Punch_FMS", "Outputs", "Punch_Rotate", False)
        # 6. Move Up
        if not move_to_sensor("Punch_Up", "Sensor_Up"):
            return "failed to move up"
        # 7. Move Backward
        if not move_to_sensor("Punch_Backward", "Sensor_Backward"):
            return "failed to move backward"
        console.print("[green]Screw operation completed successfully.[/]")
        return "skill done"
        
    return "invalid mode"


# --- AUTO FLOW TO F CHOREOGRAPHY ---
def run_flow_to_f():
    console.print("\n[yellow]Orchestrating flow: Moving product to Conveyor F...[/]")
    
    # Locate the product
    current_loc = None
    if is_product_present("Conveyor_A", "Sensor_Product"):
        current_loc = "A"
    elif is_product_present("Conveyor_B", "Conveyor_B_Product"):
        current_loc = "B"
    elif is_product_present("Conveyor_C", "Sensor_Product"):
        current_loc = "C"
    elif is_product_present("Conveyor_D", "Conveyor_D_Product"):
        current_loc = "D"
    elif is_product_present("Conveyor_E", "Sensor_Product"):
        current_loc = "E"
    elif is_product_present("Conveyor_F", "Sensor_Product"):
        current_loc = "F"
        
    if current_loc is None:
        console.print("[yellow]No product detected on any conveyor. Defaulting starting position to A...[/]")
        current_loc = "A"
    else:
        console.print(f"[green]Product located at Conveyor {current_loc}.[/]")

    def operate_at_c():
        # Randomly choose: 0 (Drill) or 1 (Screw)
        modo = random.choice([0, 1])
        modo_name = "Drill" if modo == 0 else "Screw"
        console.print(f"\n[bold yellow]>>> Product stopped at Conveyor C. Starting random operation: {modo_name} <<<[/]")
        estacao(modo, processing_time=3.0)

    # Move to F step by step
    if current_loc == "F":
        # Full lap: F -> A -> B -> C (machining) -> D -> E -> F
        passadeiraFA()
        passadeiraAB()
        passadeiraBC()
        operate_at_c()
        passadeiraCD()
        passadeiraDE()
        passadeiraEF()
    elif current_loc == "A":
        passadeiraAB()
        passadeiraBC()
        operate_at_c()
        passadeiraCD()
        passadeiraDE()
        passadeiraEF()
    elif current_loc == "B":
        passadeiraBC()
        operate_at_c()
        passadeiraCD()
        passadeiraDE()
        passadeiraEF()
    elif current_loc == "C":
        operate_at_c()
        passadeiraCD()
        passadeiraDE()
        passadeiraEF()
    elif current_loc == "D":
        passadeiraDE()
        passadeiraEF()
    elif current_loc == "E":
        passadeiraEF()
        
    console.print("[green]Auto Flow: Product successfully reached Conveyor F.[/]")
    return "auto flow to F done"

def run_flow_to_f_backwards():
    console.print("\n[yellow]Orchestrating backwards flow: Moving product to Conveyor F backwards...[/]")
    
    # Locate the product
    current_loc = None
    if is_product_present("Conveyor_A", "Sensor_Product"):
        current_loc = "A"
    elif is_product_present("Conveyor_B", "Conveyor_B_Product"):
        current_loc = "B"
    elif is_product_present("Conveyor_C", "Sensor_Product"):
        current_loc = "C"
    elif is_product_present("Conveyor_D", "Conveyor_D_Product"):
        current_loc = "D"
    elif is_product_present("Conveyor_E", "Sensor_Product"):
        current_loc = "E"
    elif is_product_present("Conveyor_F", "Sensor_Product"):
        current_loc = "F"
        
    if current_loc is None:
        console.print("[yellow]No product detected on any conveyor. Defaulting starting position to A...[/]")
        current_loc = "A"
    else:
        console.print(f"[green]Product located at Conveyor {current_loc}.[/]")

    def operate_at_c():
        modo = random.choice([0, 1])
        modo_name = "Drill" if modo == 0 else "Screw"
        console.print(f"\n[bold yellow]>>> Product stopped at Conveyor C. Starting random operation: {modo_name} <<<[/]")
        estacao(modo, processing_time=3.0)

    # Move to F backwards step by step
    if current_loc == "F":
        # Full lap backwards: F -> E -> D -> C -> B -> A -> F
        passadeiraFE()
        passadeiraED()
        passadeiraDC()
        operate_at_c()
        passadeiraCB()
        passadeiraBA()
        passadeiraAF()
    elif current_loc == "E":
        passadeiraED()
        passadeiraDC()
        operate_at_c()
        passadeiraCB()
        passadeiraBA()
        passadeiraAF()
    elif current_loc == "D":
        passadeiraDC()
        operate_at_c()
        passadeiraCB()
        passadeiraBA()
        passadeiraAF()
    elif current_loc == "C":
        operate_at_c()
        passadeiraCB()
        passadeiraBA()
        passadeiraAF()
    elif current_loc == "B":
        passadeiraBA()
        passadeiraAF()
    elif current_loc == "A":
        passadeiraAF()
        
    console.print("[green]Auto Flow (Backwards): Product successfully reached Conveyor F.[/]")
    return "auto flow to F backwards done"


# --- AUTO FLOW LOOP STATE & WORKER ---
loop_active = False
loop_thread = None

def run_loop_worker():
    global loop_active
    loop_count = 1
    while loop_active:
        console.print(f"\n[bold magenta]--- HTTP Auto Flow Cycle #{loop_count} ---[/bold magenta]")
        res = run_flow_to_f()
        if "aborted" in res or "failed" in res:
            console.print(f"[bold red]HTTP Loop stopped due to failure: {res}[/bold red]")
            loop_active = False
            break
        loop_count += 1
        time.sleep(1.0)

def run_backwards_loop_worker():
    global loop_active
    loop_count = 1
    while loop_active:
        console.print(f"\n[bold magenta]--- HTTP Backwards Auto Flow Cycle #{loop_count} ---[/bold magenta]")
        res = run_flow_to_f_backwards()
        if "aborted" in res or "failed" in res:
            console.print(f"[bold red]HTTP Loop stopped due to failure: {res}[/bold red]")
            loop_active = False
            break
        loop_count += 1
        time.sleep(1.0)

# --- HTTP REQUEST HANDLER ---
class SkillsHTTPRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Override to prevent default console spam
        pass

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)
        
        response_text = "Not Found"
        status_code = 404

        if path == "/passadeiras":
            skill_arg = query.get("skill", [""])[0]
            if skill_arg == "AB":
                response_text = passadeiraAB()
                status_code = 200
            elif skill_arg == "BC":
                response_text = passadeiraBC()
                status_code = 200
            elif skill_arg == "CD":
                response_text = passadeiraCD()
                status_code = 200
            elif skill_arg == "DE":
                response_text = passadeiraDE()
                status_code = 200
            elif skill_arg == "EF":
                response_text = passadeiraEF()
                status_code = 200
            elif skill_arg == "FA":
                response_text = passadeiraFA()
                status_code = 200
            elif skill_arg == "auto_f":
                response_text = run_flow_to_f()
                status_code = 200
            elif skill_arg == "auto_f_loop":
                global loop_active, loop_thread
                if loop_active:
                    response_text = "Continuous Auto Flow loop already active in background"
                else:
                    loop_active = True
                    loop_thread = threading.Thread(target=run_loop_worker, daemon=True)
                    loop_thread.start()
                    response_text = "Continuous Auto Flow loop started in background"
                status_code = 200
            elif skill_arg == "auto_f_backwards":
                response_text = run_flow_to_f_backwards()
                status_code = 200
            elif skill_arg == "auto_f_backwards_loop":
                if loop_active:
                    response_text = "Continuous Auto Flow loop already active in background"
                else:
                    loop_active = True
                    loop_thread = threading.Thread(target=run_backwards_loop_worker, daemon=True)
                    loop_thread.start()
                    response_text = "Continuous Backwards Auto Flow loop started in background"
                status_code = 200
            elif skill_arg == "stop_loop":
                loop_active = False
                response_text = "Continuous Auto Flow loop stop requested"
                status_code = 200
            else:
                response_text = "Unknown skill parameter"
                status_code = 400

        elif path == "/estacao":
            skill_arg = query.get("skill", [""])[0]
            try:
                mode = int(skill_arg)
                response_text = estacao(mode, processing_time=3.0)
                status_code = 200
            except ValueError:
                response_text = "Invalid skill parameter (must be int)"
                status_code = 400

        elif path == "/sensores":
            try:
                s1 = get_pin("Punch_FMS", "Inputs", "Sensor_Up")
                s2 = get_pin("Punch_FMS", "Inputs", "Sensor_Down")
                response_text = f"{'1' if s1 else '0'};{'1' if s2 else '0'};"
                status_code = 200
            except Exception as e:
                response_text = f"Error reading sensors: {e}"
                status_code = 500

        # Send response
        self.send_response(status_code)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(response_text.encode("utf-8"))


# --- SERVING AND INTERACTIVE MENU ---
def run_server_background(httpd):
    try:
        httpd.serve_forever()
    except Exception:
        pass

def run_menu(httpd):
    while True:
        console.clear()
        console.print(Panel.fit(
            "[bold blue]AAS Skills Orchestrator[/bold blue]\n"
            f"[dim]Background HTTP Server running on: http://localhost:{PORT}[/dim]\n"
            f"[dim]Target AAS Repository: {AAS_SERVER}[/dim]",
            border_style="blue"
        ))
        
        console.print("1. [cyan]passadeiraAB[/cyan] (Conveyor A -> B)")
        console.print("2. [cyan]passadeiraBC[/cyan] (Conveyor B -> C)")
        console.print("3. [cyan]passadeiraCD[/cyan] (Conveyor C -> D)")
        console.print("4. [cyan]passadeiraDE[/cyan] (Conveyor D -> E)")
        console.print("5. [cyan]passadeiraEF[/cyan] (Conveyor E -> F)")
        console.print("6. [cyan]passadeiraFA[/cyan] (Conveyor F -> A)")
        console.print("7. [yellow]estacao - Drill[/yellow] (modo 0)")
        console.print("8. [yellow]estacao - Screw[/yellow] (modo 1)")
        console.print("9. [yellow]estacao - Calibrate[/yellow] (modo 2)")
        console.print("10. [green]Auto Flow to F[/green] (random operation at C)")
        console.print("11. [green]Continuous Auto Flow (Loop)[/green] (Press Ctrl+C to stop)")
        console.print("12. [green]Continuous Backwards Auto Flow (Loop)[/green] (Press Ctrl+C to stop)")
        console.print("13. [magenta]Check Sensors Table[/magenta] (Live States)")
        console.print("14. [bold red]Exit[/bold red]")
        
        choice = Prompt.ask("\nSelect Option", choices=[str(i) for i in range(1, 15)], default="14")
        
        if choice == "1":
            passadeiraAB()
        elif choice == "2":
            passadeiraBC()
        elif choice == "3":
            passadeiraCD()
        elif choice == "4":
            passadeiraDE()
        elif choice == "5":
            passadeiraEF()
        elif choice == "6":
            passadeiraFA()
        elif choice == "7":
            estacao(0)
        elif choice == "8":
            estacao(1)
        elif choice == "9":
            estacao(2)
        elif choice == "10":
            run_flow_to_f()
        elif choice == "11":
            console.print("[bold yellow]Starting Continuous Auto Flow loop. Press Ctrl+C to interrupt...[/bold yellow]")
            try:
                loop_count = 1
                while True:
                    console.print(f"\n[bold magenta]--- Cycle #{loop_count} ---[/bold magenta]")
                    res = run_flow_to_f()
                    if "aborted" in res or "failed" in res:
                        console.print(f"[bold red]Loop stopped due to failure: {res}[/bold red]")
                        break
                    loop_count += 1
                    time.sleep(1.0)
            except KeyboardInterrupt:
                console.print("\n[bold yellow]Continuous Auto Flow loop interrupted by user.[/bold yellow]")
        elif choice == "12":
            console.print("[bold yellow]Starting Continuous Backwards Auto Flow loop. Press Ctrl+C to interrupt...[/bold yellow]")
            try:
                loop_count = 1
                while True:
                    console.print(f"\n[bold magenta]--- Cycle #{loop_count} ---[/bold magenta]")
                    res = run_flow_to_f_backwards()
                    if "aborted" in res or "failed" in res:
                        console.print(f"[bold red]Loop stopped due to failure: {res}[/bold red]")
                        break
                    loop_count += 1
                    time.sleep(1.0)
            except KeyboardInterrupt:
                console.print("\n[bold yellow]Continuous Backwards Auto Flow loop interrupted by user.[/bold yellow]")
        elif choice == "13":
            console.clear()
            console.print("[bold cyan]Querying AAS Virtual Pins...[/bold cyan]")
            
            # Read product presence (interpreting active low) and limit switches (raw active high)
            sensors = {
                "Conveyor A Product (Present)": is_product_present("Conveyor_A", "Sensor_Product"),
                "Conveyor B Product (Present)": is_product_present("Conveyor_B", "Conveyor_B_Product"),
                "Conveyor B Rotate0 (Limit)": get_pin("Conveyor_B", "Inputs", "Conveyor_B_Rotate0"),
                "Conveyor B Rotate90 (Limit)": get_pin("Conveyor_B", "Inputs", "Conveyor_B_Rotate90"),
                "Conveyor C Product (Present)": is_product_present("Conveyor_C", "Sensor_Product"),
                "Conveyor D Product (Present)": is_product_present("Conveyor_D", "Conveyor_D_Product"),
                "Conveyor D Rotate0 (Limit)": get_pin("Conveyor_D", "Inputs", "Conveyor_D_Rotate0"),
                "Conveyor D Rotate90 (Limit)": get_pin("Conveyor_D", "Inputs", "Conveyor_D_Rotate90"),
                "Conveyor E Product (Present)": is_product_present("Conveyor_E", "Sensor_Product"),
                "Conveyor F Product (Present)": is_product_present("Conveyor_F", "Sensor_Product"),
                "Conveyor F Left Limit": get_pin("Conveyor_F", "Inputs", "Sensor_Left"),
                "Conveyor F Right Limit": get_pin("Conveyor_F", "Inputs", "Sensor_Right"),
                "Punch Up Limit": get_pin("Punch_FMS", "Inputs", "Sensor_Up"),
                "Punch Down Limit": get_pin("Punch_FMS", "Inputs", "Sensor_Down"),
                "Punch Forward Limit": get_pin("Punch_FMS", "Inputs", "Sensor_Forward"),
                "Punch Backward Limit": get_pin("Punch_FMS", "Inputs", "Sensor_Backward"),
            }
            
            table = Table(title="Live Sensor States", border_style="cyan")
            table.add_column("Sensor Name", style="white")
            table.add_column("Interpreted State", justify="center")
            
            for name, val in sensors.items():
                state_str = "[bold green]YES / ACTIVE[/bold green]" if val else "[bold red]NO / INACTIVE[/bold red]"
                table.add_row(name, state_str)
                
            console.print(table)
            Prompt.ask("\nPress Enter to return to menu")
        elif choice == "14":
            break
            
        if choice in [str(i) for i in range(1, 13)]:
            Prompt.ask("\nOperation completed. Press Enter to return to menu")

def reset_all_actuators():
    console.print("[yellow]Initializing system: Resetting all actuators to 0 (False)...[/]")
    actuators_map = {
        "Conveyor_A": ["Move_Conveyor_IN", "Move_Conveyor_OUT"],
        "Conveyor_B": ["Conveyor_B_CCW", "Conveyor_B_CW", "Move_Conveyor_IN", "Move_Conveyor_OUT"],
        "Conveyor_C": ["Move_Conveyor_IN", "Move_Conveyor_OUT"],
        "Conveyor_D": ["Conveyor_D_CCW", "Conveyor_D_CW", "Move_Conveyor_IN", "Move_Conveyor_OUT"],
        "Conveyor_E": ["Move_Conveyor_IN", "Move_Conveyor_OUT"],
        "Conveyor_F": ["Conveyor_F_Left", "Conveyor_F_Right", "Conveyor_F_IN", "Conveyor_F_Out"],
        "Punch_FMS": ["Punch_Forward", "Punch_Backward", "Punch_Up", "Punch_Down", "Punch_Rotate"]
    }
    for kit, actuators in actuators_map.items():
        for act in actuators:
            set_pin(kit, "Outputs", act, False)
    console.print("[green]All actuators reset to 0.[/]")

def main():
    # Reset all actuators to 0 at script startup
    reset_all_actuators()
    
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, SkillsHTTPRequestHandler)
    
    # Start HTTP server in background daemon thread
    server_thread = threading.Thread(target=run_server_background, args=(httpd,), daemon=True)
    server_thread.start()
    
    try:
        run_menu(httpd)
    except KeyboardInterrupt:
        pass
    finally:
        console.print("\n[yellow]Stopping server...[/]")
        httpd.server_close()

if __name__ == "__main__":
    main()
