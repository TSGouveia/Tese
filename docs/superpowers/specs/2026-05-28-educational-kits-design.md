# Educational Kits Integration Design

## 1. Overview
Expand the AAS and Unity architecture to support modular industrial educational kits. The system moves away from URDF-centric monolithic structures to a **Dynamic Component-Based Architecture** where the AAS defines the physical assembly, virtual wiring (IOs), and behavioral rules.

## 2. Architecture & Data Flow

**The "AAS-First" via Configuration approach:**
1. **Python Studio:** A tool that consumes a `kit_config.json`. It registers the AAS in BaSyx, creates the submodels, and uploads 3D assets (.obj/.stl) to the AAS file repository.
2. **BaSyx (AAS Server):** The Single Source of Truth.
   - **Structural Metadata:** Defines what parts exist, where they are, and who is the parent of whom.
   - **IO Layer (Virtual Pins):** Stores the real-time state of the kit.
   - **Behavioral Metadata:** Tells the visualizer *how* to animate a component when a pin changes.
3. **Unity Visualizer:** 
   - **Bootstrap:** Connects to AAS, reads `VisualStructure`, downloads meshes, and reconstructs the 3D scene.
   - **Execution:** 
     - **Reads "Outputs":** Interprets control signals (e.g., `OUT_Motor_On`) and maps them to physics-based animations (Actuators).
     - **Writes "Inputs":** Monitors physical collisions/triggers and updates sensor states (e.g., `IN_Sensor_Peca`) in the AAS.
4. **External Logic (Soft-PLC):** A Python script or external controller that reads Inputs from the AAS and writes Outputs back, closing the control loop.

## 3. Detailed Component Definition (JSON Schema)

The configuration file defines three main aspects per component:

### 3.1. Visuals & Hierarchy
- `name`: Unique identifier for the component.
- `mesh`: File path to the 3D model.
- `parent`: Reference to another component's name to build a transform hierarchy.
- `position/rotation`: Local coordinates relative to the parent.

### 3.2. Actuator Behaviors (AAS Outputs -> Unity)
Defines how Unity moves a component when an Output pin is active:
- `TranslateContinuous`: Constant movement along an axis (e.g., a conveyor belt texture or a moving part).
- `TranslateFixed`: Moves between two points (A to B) based on a boolean (e.g., a pneumatic cylinder).
- `RotateContinuous`: Constant rotation (e.g., a motor or gear).
- `RotateHinge`: Rotates between two angles (e.g., a gate or a gripper arm).
- `Parameters`: `axis`, `speed`, `limit_min`, `limit_max`.

### 3.3. Sensor Behaviors (Unity -> AAS Inputs)
Defines how Unity detects events and updates Input pins:
- `TriggerZone`: An invisible volume that detects entry.
- `ContactSensor`: Detects physical collision between two rigidbodies.
- **Filtering Logic:** 
  - `target_filter`: The sensor only triggers if the colliding object matches a specific **Tag** or **Name** (e.g., "Product", "Metallic", "RobotGripper").
  - This allows for "Magnetic Sensors" (triggering only on objects with a "Magnetic" property/tag) or "Presence Sensors" (triggering on any "Product").

## 4. AAS Submodel Mapping

The Python Studio will generate the following Submodels:

| Submodel | Element Type | Purpose |
| :--- | :--- | :--- |
| **VisualStructure** | Collection | One collection per component containing `Mesh` (File), `Transform` (Collection of XYZ), and `Parent` (Reference). |
| **VirtualPins** | Collection | `Inputs` (Collection of Properties) and `Outputs` (Collection of Properties). |
| **BehaviorMapping** | Collection | Maps `Pin_ID` to `Component_Name` and `Behavior_Type` + `Parameters`. |

## 5. Unity Implementation Strategy

1. **AASKitImporter.cs**: 
   - Uses `UnityWebRequest` to fetch the `VisualStructure`.
   - Reconstructs the tree by instantiating `MeshFilter`/`MeshRenderer` components.
   - Attaches `Rigidbody` (Kinematic for actuators, Dynamic for products) and `Colliders` based on mesh bounds or primitive overrides.
2. **AASActuatorController.cs**:
   - Loops through `BehaviorMapping`.
   - For each active Output pin, it applies `transform.Translate` or `transform.Rotate` in the `Update` loop.
3. **AASSensorController.cs**:
   - Uses `OnTriggerEnter` / `OnCollisionEnter`.
   - Validates the `target_filter`.
   - Executes a `PUT` request to the AAS `VirtualPins/Inputs` property.

## 6. IO Polling & Performance
- **Actuators:** Polled from AAS at 20-50Hz.
- **Sensors:** Pushed to AAS immediately on event (Event-driven).
- **Optimization:** Only components with `Actuators` will have polling logic attached.
