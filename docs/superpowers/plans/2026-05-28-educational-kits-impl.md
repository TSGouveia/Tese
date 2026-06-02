# Educational Kits Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a dynamic system to create, deploy, and visualize modular industrial educational kits using AAS and Unity, driven by a JSON configuration.

**Architecture:** A Python-based "Studio" script translates JSON to AAS Submodels. Unity dynamically reconstructs the kit and handles IO synchronization (Actuators/Sensors) via REST.

**Tech Stack:** Python (PyQt6, BaSyx SDK), C# (Unity, Newtonsoft.JSON, UnityWebRequest).

---

### Task 1: Python Studio - JSON Parser & AAS Structure Generator

**Files:**
- Create: `AAS Client/kit_studio_manager.py`
- Modify: `AAS Client/aas_manager.py` (if common AAS creation logic can be extracted)

- [ ] **Step 1: Implement the JSON parser**
Create a class to validate and parse the `kit_config.json` into internal models.

- [ ] **Step 2: Implement AAS creation logic**
Implement the creation of the `VisualStructure`, `VirtualPins`, and `BehaviorMapping` submodels using the BaSyx Python SDK.

- [ ] **Step 3: Asset Deployment**
Implement logic to collect 3D meshes referenced in the JSON and upload them to the BaSyx file repository.

- [ ] **Step 4: Integration Test**
Run the script with `kit_config_template.json` and verify the AAS is correctly visible in the BaSyx Dashboard.

- [ ] **Step 5: Commit**
```bash
git add "AAS Client/kit_studio_manager.py" "AAS Client/AAS_TEMPLATES/kit_config_template.json"
git commit -m "feat(python): add kit studio manager for JSON-to-AAS conversion"
```

### Task 2: Unity - Dynamic Kit Importer

**Files:**
- Create: `DT Unity/Assets/Scripts/AAS/AASKitImporter.cs`

- [ ] **Step 1: Implement AAS Submodel Polling**
Write logic to fetch the `VisualStructure` from the BaSyx REST API.

- [ ] **Step 2: Recursive Mesh Loader**
Implement a routine that downloads meshes and reconstructs the transform hierarchy based on `ParentName`.

- [ ] **Step 3: Physics Setup**
Automatically attach `MeshCollider` and `Rigidbody` (set to Kinematic) to the instantiated components.

- [ ] **Step 4: Commit**
```bash
git add "DT Unity/Assets/Scripts/AAS/AASKitImporter.cs"
git commit -m "feat(unity): add AASKitImporter for dynamic component loading"
```

### Task 3: Unity - Virtual Pins Synchronization (Actuators & Sensors)

**Files:**
- Create: `DT Unity/Assets/Scripts/AAS/AASActuatorController.cs`
- Create: `DT Unity/Assets/Scripts/AAS/AASSensorController.cs`

- [ ] **Step 1: Actuator Logic**
Implement `AASActuatorController` to poll `VirtualPins/Outputs` and apply `Translate` or `Rotate` behaviors based on the `BehaviorMapping`.

- [ ] **Step 2: Sensor Logic**
Implement `AASSensorController` using `OnTriggerEnter`. Check the `target_filter` (Tag/Name) and send a `PUT` request to update the `VirtualPins/Inputs`.

- [ ] **Step 3: Commit**
```bash
git add "DT Unity/Assets/Scripts/AAS/AASActuatorController.cs" "DT Unity/Assets/Scripts/AAS/AASSensorController.cs"
git commit -m "feat(unity): add Actuator and Sensor controllers for Virtual Pins sync"
```

### Task 4: Final Validation

- [ ] **Step 1: Full Loop Test**
1. Run Python Studio to create the "SortingStation" AAS.
2. Open Unity and load the kit via AAS ID.
3. Use a simple Python script (Soft-PLC) to toggle the `OUT_Conveyor_Run` pin.
4. Verify the belt moves in Unity and the presence sensor updates the AAS when a product is placed.

- [ ] **Step 2: Commit**
```bash
git commit -m "test: verify full IO loop for educational kits"
```
