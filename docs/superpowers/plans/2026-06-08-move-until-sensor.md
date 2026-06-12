# Move Until Sensor & Dynamic Visibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a local stop mechanism for actuators when a specific sensor is triggered, and add a visibility toggle for sensors in the JSON configuration.

**Architecture:** Use Approach 2 (Local Link) where the `AASActuatorController` queries the `AASSensorController` locally to check for sensor triggers in real-time. Visibility is controlled by enabling/disabling `MeshRenderer` components.

**Tech Stack:** Unity (C#), AAS (JSON metadata via BaSyx).

---

### Task 1: Update Sensor Visibility Logic

**Files:**
- Modify: `DT Unity/Assets/Scripts/AAS/AASSensorController.cs`

- [ ] **Step 1: Update `SensorBinding` class to include `visible` property.**

```csharp
[Serializable]
public class SensorBinding
{
    public string pinId;
    public string componentName;
    public string type;
    public string targetFilter;
    public bool lastState = false;
    public int overlapCount = 0; 
    public bool activeLow = false;
    public bool visible = true; // New property
}
```

- [ ] **Step 2: Update `LoadBindingsRoutine` to parse `Visible` parameter.**

```csharp
// Inside LoadBindingsRoutine, within the parameter loop:
bool visible = true;
// ...
if (p["idShort"]?.ToString() == "Visible") visible = p["value"]?.ToString().ToLower() != "false";
// ...
// After creating the binding:
var binding = new SensorBinding {
    pinId = pinId,
    componentName = compName,
    type = type,
    targetFilter = filter,
    activeLow = activeLow,
    visible = visible // Set the new property
};
```

- [ ] **Step 3: Implement visibility toggle in `LoadBindingsRoutine`.**

```csharp
// Inside LoadBindingsRoutine, where TriggerZone renderers are hidden:
foreach (var c in target.GetComponentsInChildren<Collider>())
{
    if (type == "TriggerZone" || !binding.visible) 
    {
        c.isTrigger = (type == "TriggerZone");
        
        // Hide the mesh renderer if the sensor is a TriggerZone OR marked as invisible
        var renderer = c.GetComponent<Renderer>();
        if (renderer != null) renderer.enabled = false;
    }
}
```

- [ ] **Step 4: Commit changes.**

```bash
git add "DT Unity/Assets/Scripts/AAS/AASSensorController.cs"
git commit -m "feat(sensor): add visibility control via JSON parameter"
```

---

### Task 2: Update Actuator Metadata for Sensor Linking

**Files:**
- Modify: `DT Unity/Assets/Scripts/AAS/AASActuatorController.cs`

- [ ] **Step 1: Update `ActuatorBinding` class to include `stopSensorComponent` and sensor reference.**

```csharp
[Serializable]
public class ActuatorBinding
{
    public string pinId;
    public GameObject target;
    public string type;
    public Vector3 axis;
    public float speed;
    public float limitMin;
    public float limitMax;
    public bool currentState;
    
    public Vector3 initialPosition;
    public Quaternion initialRotation;
    public Vector2 currentOffset;

    public string stopSensorComponent; // New property
    public AASSensorController.SensorPhysicsProxy linkedSensor; // New reference
}
```

- [ ] **Step 2: Update `LoadBindingsRoutine` to parse `StopSensorComponent` parameter.**

```csharp
// Inside LoadBindingsRoutine, within the parameter loop:
string stopSensor = "";
// ...
if (pid == "StopSensorComponent") stopSensor = p["value"]?.ToString();
// ...
// When creating the binding:
var binding = new ActuatorBinding {
    pinId = pinId, target = target, type = type, axis = unityAxis,
    speed = speed, limitMin = min, limitMax = max,
    initialPosition = target.transform.localPosition,
    initialRotation = target.transform.localRotation,
    stopSensorComponent = stopSensor // Set the new property
};
```

- [ ] **Step 3: Commit changes.**

```bash
git add "DT Unity/Assets/Scripts/AAS/AASActuatorController.cs"
git commit -m "feat(actuator): add StopSensorComponent metadata parsing"
```

---

### Task 3: Implement Stop-on-Sensor Logic

**Files:**
- Modify: `DT Unity/Assets/Scripts/AAS/AASActuatorController.cs`

- [ ] **Step 1: Link Actuators to Sensors after both controllers are initialized.**

```csharp
// At the end of LoadBindingsRoutine, after isInitialized = true:
foreach (var b in bindings) {
    if (!string.IsNullOrEmpty(b.stopSensorComponent)) {
        var sensorController = FindFirstObjectByType<AASSensorController>();
        if (sensorController != null) {
            // Find the proxy by component name
            var proxy = sensorController.GetComponentsInChildren<AASSensorController.SensorPhysicsProxy>()
                .FirstOrDefault(p => p.binding.componentName == b.stopSensorComponent || p.binding.pinId == b.stopSensorComponent);
            if (proxy != null) {
                b.linkedSensor = proxy;
                Debug.Log($"[Actuator] 🔗 Linked {b.pinId} to sensor {b.stopSensorComponent}");
            }
        }
    }
}
```

- [ ] **Step 2: Add helper method `IsBlockedBySensor` to check stop condition.**

```csharp
private bool IsBlockedBySensor(ActuatorBinding b) {
    if (b.linkedSensor == null) return false;
    // Check if the sensor is currently triggered (lastState is calculated locally in Proxy)
    return b.linkedSensor.binding.lastState;
}
```

- [ ] **Step 3: Update `Update` loop to skip movement if blocked.**

```csharp
void Update()
{
    if (!isInitialized) return;
    foreach (var b in bindings) {
        if (b.target == null) continue;
        
        // Check if movement is allowed
        bool isBlocked = IsBlockedBySensor(b);
        if (isBlocked && b.currentState) {
            // Force state to false or just skip movement? 
            // In Approach 2, we skip movement to stop immediately.
            continue; 
        }

        switch (b.type) {
            // ... existing cases ...
        }
    }
}
```

- [ ] **Step 4: Commit changes.**

```bash
git add "DT Unity/Assets/Scripts/AAS/AASActuatorController.cs"
git commit -m "feat(actuator): implement local stop-on-sensor logic"
```

---

### Task 4: Documentation for User

- [ ] **Step 1: Write a guide for the user on how to set up translation and rotation with sensors.**

Create `docs/GUIDE_MOVEMENTS.md`:
```markdown
# Guia de Movimentação e Sensores

## 1. Como fazer translação/rotação
No teu JSON do AAS (Submodelo de Comportamento), define um elemento para o teu Atuador.

### Exemplo: Translação Contínua (Empurrador)
- **Component**: Nome do objeto ou Empty no Blender.
- **Type**: `TranslateContinuous`
- **Parameters**:
    - `AxisZ`: 1 (direção do movimento)
    - `Speed`: 0.5 (velocidade)
    - `StopSensorComponent`: "Nome_Do_Teu_Sensor" (opcional)

### Exemplo: Rotação (Braço)
- **Type**: `RotateContinuous` ou `RotateHinge` (para ângulos fixos).

## 2. Sensores Invisíveis
Para teres uma "trigger zone" que não se vê na Unity:
No Submodelo do Sensor, adiciona o parâmetro:
- `Visible`: `false`

## 3. Organização no Blender
- Usa **Empties** para agrupar objetos caóticos.
- O script mexe o objeto que deres o nome; se esse objeto tiver filhos, eles vão todos atrás.
```

- [ ] **Step 2: Commit documentation.**

```bash
git commit -m "docs: add guide for movements and sensors"
```
