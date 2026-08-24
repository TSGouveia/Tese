# Real-Digital Communication & Sensory Linking Design Specification

## Overview
This specification describes the architecture and implementation for linking physical equipment (e.g., Arduino controllers via Sockets) with the digital representation of industrial kits in the AAS Client (Python) and Unity Digital Twin.

Python (AAS Client / Conveyor Wizard) acts as the **AAS Creator and Configurator**, enabling users to dynamically configure communication protocols, dynamic endpoints (IP and Port), and physical sensor mappings.
Unity acts as the **Runtime Engine**, importing the exported AAS metamodel and dynamically managing socket connections, sensor state updates, and piece teleportation/positioning in 3D space.

---

## 1. Python UI Components (`conveyor_wizard.py`)

### 1.1 Kit-Level Communication Settings
- **Communication Protocol**: `QComboBox` offering options `["None", "Sockets"]` (Default: `"Sockets"`).
- **Endpoint IP**: `QLineEdit` for dynamic IP configuration (e.g. `"192.168.10.1"`).
- **Endpoint Port**: `QSpinBox` / `QLineEdit` for dynamic network port configuration (Default range: 1–65535, Default value: `8888`).
- **Dynamic Visibility**: When protocol is `"None"`, the IP and Port input fields are disabled/hidden.

### 1.2 Sensor Widget Configuration (`SensorWidget`)
- **Real Physical Sensor Toggle**: `QCheckBox` labeled `"Real Physical Sensor"`.
- **Real Port ID**: `QLineEdit` labeled `"Real Port ID"` for typing physical port names (e.g., `I0_0`, `I1_2`).
- **Dynamic Behavior**: The `Real Port ID` input field is only enabled when `"Real Physical Sensor"` checkbox is checked.

---

## 2. AAS Metamodel Submodel Serialization

### 2.1 `AssetInterfacesDescription` Submodel
Generated when saving or exporting the kit. Contains:
- `Protocol`: String (`"Sockets"` or `"None"`)
- `EndpointIP`: String (e.g. `"192.168.10.1"`)
- `EndpointPort`: Integer/String (e.g. `8888`)

### 2.2 `BehaviorMapping` / `VirtualPins` Submodel
For each sensor widget in the kit:
- `RealSensorEnabled`: Boolean (`True` / `False`)
- `RealPortID`: String (e.g. `"I0_0"`)

---

## 3. Unity Runtime Responsibilities
1. Unity imports/parses the generated AAS submodels (`AssetInterfacesDescription` & `BehaviorMapping`).
2. Extracts dynamic communication settings (`Protocol`, `EndpointIP`, `EndpointPort`).
3. If `Protocol == "Sockets"`, Unity opens TCP Socket connection to `EndpointIP:EndpointPort`.
4. Upon receiving JSON payload from Arduino (e.g. `{"Port": "I0_0", "Value": 1}`):
   - Unity locates the sensor element where `RealPortID == "I0_0"`.
   - Updates the digital twin sensor state.
   - Snaps / teleports physical piece model in 3D scene to the corresponding sensor position.
