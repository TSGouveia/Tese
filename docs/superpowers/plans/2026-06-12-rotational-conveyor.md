# Rotational Conveyor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a new rotational conveyor Digital Twin asset with two-pin rotation control, limit sensors, and parallel belts.

**Architecture:** We will create a new JSON configuration for the `KitStudioManager` and modify the Unity `AASActuatorController` to support multiple actuators sharing the same `pinId`. The rotation will use existing `RotateContinuous` behavior with `StopSensorComponent` for automatic stopping at 0° and 90°.

**Tech Stack:** Python (AAS Client), C# (Unity), AAS (BaSyx).

---

### Task 1: Create AAS Configuration for Rotational Conveyor

**Files:**
- Create: `AAS Client/3D_models/kit_config_rotativo.json`

- [ ] **Step 1: Write the JSON configuration file**

```json
{
  "kit_name": "RotationalConveyor",
  "aas_id": "RotationalConveyor_01",
  "description": "Conveyor rotativo com limites em 0 e 90 graus e correias paralelas.",
  "components": [
    {
      "name": "Base",
      "mesh": "Rotativo.glb/Base",
      "parent": null,
      "position": [0, 0, 0],
      "sensors": [
        {
          "pin_id": "IN_Rotate_0",
          "behavior": "TriggerZone",
          "node": "Sensor_0",
          "target_filter": "Ativador",
          "visible": false
        },
        {
          "pin_id": "IN_Rotate_90",
          "behavior": "TriggerZone",
          "node": "Sensor_90",
          "target_filter": "Ativador",
          "visible": false
        }
      ]
    },
    {
      "name": "Rotator",
      "mesh": "Rotativo.glb/Rotator",
      "parent": "Base",
      "actuators": [
        {
          "pin_id": "OUT_Rotate_CW",
          "behavior": "RotateContinuous",
          "axis": [0, 0, 1],
          "speed": 0.5,
          "stop_sensor": "IN_Rotate_0"
        },
        {
          "pin_id": "OUT_Rotate_ACW",
          "behavior": "RotateContinuous",
          "axis": [0, 0, -1],
          "speed": 0.5,
          "stop_sensor": "IN_Rotate_90"
        }
      ]
    },
    {
      "name": "Belt",
      "mesh": "Rotativo.glb/Belt",
      "parent": "Rotator",
      "actuators": [
        {
          "pin_id": "OUT_Belts_Run",
          "behavior": "Conveyor",
          "axis": [1, 0, 0],
          "speed": 1.0
        }
      ]
    },
    {
      "name": "Belt1",
      "mesh": "Rotativo.glb/Belt1",
      "parent": "Rotator",
      "actuators": [
        {
          "pin_id": "OUT_Belts_Run",
          "behavior": "Conveyor",
          "axis": [1, 0, 0],
          "speed": 1.0
        }
      ]
    },
    {
      "name": "ZoneProduto",
      "parent": "Rotator",
      "sensors": [
        {
          "pin_id": "IN_Product_Detected",
          "behavior": "TriggerZone",
          "target_filter": "Product",
          "visible": false
        }
      ]
    }
  ]
}
```

- [ ] **Step 2: Commit the configuration**

```bash
git add "AAS Client/3D_models/kit_config_rotativo.json"
git commit -m "feat: add rotational conveyor AAS configuration"
```

---

### Task 2: Update Unity AASActuatorController for Multiple Bindings

**Files:**
- Modify: `DT Unity/Assets/Scripts/AAS/AASActuatorController.cs`

- [ ] **Step 1: Modify PollingLoop to update all bindings with matching pinId**

We need to change `bindings.Find(x => x.pinId == pid)` to a loop that finds all matching bindings.

```csharp
// Around line 250 in AASActuatorController.cs
// OLD:
// var b = bindings.Find(x => x.pinId == pid);
// if (b != null) b.currentState = val;

// NEW:
foreach (var b in bindings.Where(x => x.pinId == pid)) {
    b.currentState = val;
}
```

- [ ] **Step 2: Commit Unity script changes**

```bash
git add "DT Unity/Assets/Scripts/AAS/AASActuatorController.cs"
git commit -m "refactor: support multiple actuator bindings per pinId"
```

---

### Task 3: Deploy AAS and Verify

**Files:**
- Run: `AAS Client/kit_studio_manager.py`

- [ ] **Step 1: Deploy the new rotational conveyor AAS**

Assumes BaSyx is running (AAS Docker).

Run: `python "AAS Client/kit_studio_manager.py" "AAS Client/3D_models/kit_config_rotativo.json"`
Expected: "Successfully deployed AAS: https://acplt.org/AAS_RotationalConveyor"

- [ ] **Step 2: Verify Registry entry**

Run: `curl -s http://localhost:8082/shell-descriptors | grep RotationalConveyor`
Expected: Match found in JSON output.

- [ ] **Step 3: Test with conveyor_plc.py (Manual Toggle)**

Run: `python "AAS Client/conveyor_plc.py"`
1. Select "RotationalConveyor_01".
2. Toggle `OUT_Rotate_CW`.
3. Verify in Unity (if open) that the platform rotates.
4. Toggle `OUT_Belts_Run`.
5. Verify in Unity (if open) that both belts move.
