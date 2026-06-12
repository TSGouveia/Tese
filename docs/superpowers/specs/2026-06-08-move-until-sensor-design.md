# Design Spec: Move Until Sensor & Dynamic Visibility
Date: 2026-06-08
Status: Pending Approval

## 1. Objective
Add a mechanism where an actuator stops movement immediately upon triggering a specific sensor (local link in Unity) and provide dynamic control over sensor visibility.

## 2. Architecture
Following **Approach 2 (Local Link)**: Unity handles the real-time stop logic to eliminate network latency, then synchronizes state back to the AAS.

### 2.1 Component Grouping (Blender Workflow)
- **Problem:** Blender exports are "chaotic" with many individual objects.
- **Solution:** Use **Parenting**. 
    - In Blender, create an **Empty** (Plain Axes) named specifically (e.g., `Elevator_Group`).
    - Parent all related mesh objects to this Empty.
    - In the AAS, reference `Elevator_Group` as the `Component`. 
    - Unity moves the Empty; all child meshes follow automatically.

### 2.2 Dynamic Visibility
- **New Parameter:** `Visible` (Boolean) inside the Sensor Submodel.
- **Implementation:** 
    - If `Visible` is `false`, the `AASSensorController` disables the `MeshRenderer` of the component.
    - The `Collider` remains enabled for physics detection.
    - This allows for "invisible trigger zones" or "internal sensors".

### 2.3 Stop-on-Sensor Logic
- **New Parameter:** `StopSensorComponent` (String) inside the Actuator Submodel.
- **Workflow:**
    1. During initialization, `AASActuatorController` maps all available sensors by their component name.
    2. Actuators check if `StopSensorComponent` is defined.
    3. In `FixedUpdate`, the actuator queries the linked sensor's local state (`touching.Count > 0`).
    4. If the sensor is triggered (respecting `ActiveLow` logic), the actuator sets its internal `speed` or `movement` to zero for that frame.
    5. The actuator state is updated in the AAS to reflect the stop.

## 3. JSON Configuration Example

### Sensor (Behavior Submodel)
```json
{
  "idShort": "Sensor_Limit",
  "value": [
    { "idShort": "Component", "value": "Trigger_Object" },
    { "idShort": "Type", "value": "TriggerZone" },
    { "idShort": "Parameters", "value": [
      { "idShort": "Visible", "value": "false" },
      { "idShort": "ActiveLow", "value": "false" }
    ]}
  ]
}
```

### Actuator (Behavior Submodel)
```json
{
  "idShort": "Pusher_Actuator",
  "value": [
    { "idShort": "Component", "value": "Pusher_Group" },
    { "idShort": "Type", "value": "TranslateContinuous" },
    { "idShort": "Parameters", "value": [
      { "idShort": "AxisZ", "value": "1" },
      { "idShort": "Speed", "value": "1.5" },
      { "idShort": "StopSensorComponent", "value": "Sensor_Limit" }
    ]}
  ]
}
```

## 4. Success Criteria
- [ ] Actuator stops exactly when the sensor is triggered in Unity.
- [ ] Sensor can be made invisible without losing functionality.
- [ ] Complex Blender groups move as a single unit when the parent Empty is targeted.
- [ ] AAS reflects the stopped state accurately.
