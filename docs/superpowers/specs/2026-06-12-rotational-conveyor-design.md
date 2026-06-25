# Design Specification: Rotational Conveyor Asset

**Date:** 2026-06-12
**Topic:** Implementation of a rotational conveyor with dual-direction control and integrated sensor feedback.

## 1. Overview
The goal is to create a new Digital Twin asset for a rotational conveyor. This conveyor features a rotating platform capable of clockwise (CW) and anti-clockwise (ACW) movement, limited by two sensors (0° and 90°). It also includes two parallel belts for product movement and a detection zone for products.

## 2. Component Hierarchy (Rotativo.glb)
The asset is composed of the following hierarchy:
- **Base (Static)**: The fixed foundation.
    - **Sensor_0**: Trigger zone (invisible) located at the 0° position.
    - **Sensor_90**: Trigger zone (invisible) located at the 90° position.
- **Rotator (Moving)**: The platform that rotates.
    - **Ativador**: A physical trigger component that activates `Sensor_0` and `Sensor_90`.
    - **Belt**: First parallel conveyor belt.
    - **Belt1**: Second parallel conveyor belt.
    - **ZoneProduto**: Trigger zone (invisible) to detect product presence on top of the belts.

## 3. AAS Submodel Configuration (BaSyx)

### 3.1 Virtual Pins (Inputs/Outputs)
| Pin ID | Type | Direction | Description |
| :--- | :--- | :--- | :--- |
| `OUT_Rotate_CW` | Boolean | Output (PLC) | Activates clockwise rotation towards 0°. |
| `OUT_Rotate_ACW` | Boolean | Output (PLC) | Activates anti-clockwise rotation towards 90°. |
| `OUT_Belts_Run` | Boolean | Output (PLC) | Activates both `Belt` and `Belt1` simultaneously. |
| `IN_Rotate_0` | Boolean | Input (PLC) | Active when `Ativador` is at `Sensor_0`. |
| `IN_Rotate_90` | Boolean | Input (PLC) | Active when `Ativador` is at `Sensor_90`. |
| `IN_Product_Detected` | Boolean | Input (PLC) | Active when a product is in `ZoneProduto`. |

### 3.2 Behavior Mapping
| Element | Behavior Type | Parameters | Target Component |
| :--- | :--- | :--- | :--- |
| `OUT_Rotate_CW` | `RotateContinuous` | Axis: [0,0,1], Speed: 0.5, StopSensor: `IN_Rotate_0` | `Rotator` |
| `OUT_Rotate_ACW` | `RotateContinuous` | Axis: [0,0,-1], Speed: 0.5, StopSensor: `IN_Rotate_90` | `Rotator` |
| `OUT_Belts_Run` | `Conveyor` | Axis: [1,0,0], Speed: 1.0 | `Belt`, `Belt1` |
| `IN_Rotate_0` | `TriggerZone` | Filter: "Ativador", Visible: false | `Sensor_0` |
| `IN_Rotate_90` | `TriggerZone` | Filter: "Ativador", Visible: false | `Sensor_90` |
| `IN_Product_Detected` | `TriggerZone` | Filter: "Product", Visible: false | `ZoneProduto` |

## 4. Technical Requirements & Implementation Details

### 4.1 Unity - AASActuatorController.cs
- **Multiple Bindings per Pin**: Modify the polling logic to allow multiple `ActuatorBinding` objects to share the same `pinId`. Currently, it uses `Find`, which only returns the first match.
- **Rotation Logic**: Ensure `RotateContinuous` uses `Space.Self` and correctly handles the `StopSensorComponent` logic already present in the script.

### 4.2 Unity - AASSensorController.cs
- **Trigger Setup**: Ensure the "Ativador" and "Product" filters correctly match the incoming 3D model names/tags.
- **Visibility**: Automatically hide meshes named "Sensor_0", "Sensor_90", and "ZoneProduto" (or containing "TriggerZone") as per existing logic.

### 4.3 AAS Client - Kit Configuration
- Create `kit_config_rotativo.json` with the structure defined above.
- Use `KitStudioManager` to generate the AASX and deploy to BaSyx.

## 5. Success Criteria
1. Activating `OUT_Rotate_CW` rotates the platform until `IN_Rotate_0` becomes true.
2. Activating `OUT_Rotate_ACW` rotates the platform until `IN_Rotate_90` becomes true.
3. Activating `OUT_Belts_Run` moves both belts simultaneously.
4. `IN_Product_Detected` correctly reports the presence of a product on the belts.
5. All trigger sensors are invisible in the Unity scene.
