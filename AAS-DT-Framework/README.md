<div align="center"> 

# Automatic Generation of Simulation-Based Digital Twins from Asset Administration Shells

[![NOVA SST: Thesis](https://img.shields.io/badge/NOVA_SST-MSc_Thesis-blue)](https://run.unl.pt)
[![License: MIT](https://img.shields.io/badge/License-MIT-red.svg)](https://opensource.org/licenses/MIT)

**Tiago Daniel Santos Gouveia**<sup>1</sup>  
*Advisers:* **Prof. Dr. André Dionisio Rocha**<sup>1</sup>, **Nelson Nascimento de Freitas**<sup>1</sup>

<sup>1</sup> **NOVA School of Science and Technology (NOVA FCT)**,  
Department of Electrical and Computer Engineering,  
NOVA University Lisbon, 2829-516 Caparica, Portugal

---

<table>
  <tr>
    <td style="vertical-align: middle;">
      The Industry 4.0 paradigm relies on Cyber-Physical Systems (CPS) to achieve agile and resilient production. Digital Twins (DT) provide virtual representations capable of mirroring physical assets through real-time bidirectional telemetry. However, traditional development relies on proprietary simulation software, fragmented 3D CAD files lacking kinematics, and tedious manual matching of I/O addresses.<br/><br/>
      To overcome these barriers, this repository presents an open, modular, model-driven framework for automated procedural generation and live synchronization of industrial Digital Twins from Asset Administration Shells (AAS).
    </td>
  </tr>
</table>

</div>

---

## <div align="center">Framework Architecture</div>

The architecture spans four decoupled tiers:

1. **Layer 0 - Low-Polygon Asset Digitization (Blender):** Modeling lightweight 3D assets with proper origin points and kinematic hierarchy.
2. **Layer 1 - No-Code Semantic Authoring (AAS Client / Python):** Studio GUI (`conveyor_wizard.py`) for 3D raycasting asset placement, I/O pin mapping, and packaging into standardized `.aasx` containers.
3. **Layer 2 - Containerized AAS Storage & Discovery (Docker & BaSyx v2):** Eclipse BaSyx microservices hosting Submodel Registries, AAS Servers, MQTT Broker (Mosquitto), and Time-Series DB (InfluxDB).
4. **Layer 3 - Procedural Simulation & Live Sync (Unity 3D Engine):** Procedural scene assembly from BaSyx AAS models, physics-based kinematic simulation, dual-mode execution (Virtual Commissioning / Live Telemetry Sync), and sensor drift correction.

---

## <div align="center">Repository Structure</div>

```
AAS-DT-Framework/
├── AAS Client/               # Layer 1: Python AAS Authoring Studio
│   ├── conveyor_wizard.py    # Main GUI Studio for AAS layout generation & submodel creation
│   └── requirements.txt      # Python dependencies for the authoring studio
├── AAS Docker/               # Layer 2: Docker Compose infrastructure
│   ├── docker-compose.yml    # Eclipse BaSyx v2 (AAS Registry, Submodel Registry, AAS Server), Mosquitto MQTT & InfluxDB
│   ├── basyx/                # BaSyx configuration properties & YAMLs
│   ├── mosquitto/            # MQTT broker configuration
│   └── influxdb/             # InfluxDB database configuration
├── Documents/                # MSc Thesis LaTeX Source & PDF
│   ├── 0-Config/             # Document metadata & cover configuration
│   ├── 1-FrontMatter/        # Abstracts (EN, PT), acknowledgements, acronyms, glossary
│   ├── 2-MainMatter/         # Thesis chapters
│   ├── 5-Figures/            # Figures & diagrams
│   └── thesis.pdf            # Compiled Master's Thesis document
├── DT Unity/                 # Layer 3: Unity 3D Simulation & Telemetry Engine
│   ├── Assets/               # C# scripts, prefabs, materials, and AAS procedural generation logic
│   ├── Packages/             # Unity project dependency manifests
│   └── ProjectSettings/      # Unity project physics, tag, and layer settings
└── FMS DT/                   # Hardware Firmware
    └── FMS_DT.ino            # ESP32 / Arduino C++ code for physical FMS bench PLC control & telemetry
```

---

## <div align="center">Get Started</div>

### 1. Launch the AAS Containerized Middleware (Layer 2)
Ensure Docker Desktop is running, then start the BaSyx v2 microservices:
```bash
cd "AAS Docker"
docker-compose up -d
```
This starts the AAS Registry, Submodel Registry, AAS Environment Server, Mosquitto MQTT Broker, and InfluxDB telemetry store.

### 2. Run the AAS Authoring Studio (Layer 1)
Install dependencies and launch the Python GUI to generate AAS packages or model industrial layouts:
```bash
cd "../AAS Client"
pip install -r requirements.txt
python conveyor_wizard.py
```

### 3. Open the Simulation Engine (Layer 3)
1. Launch **Unity 2022.3 LTS** (or compatible version).
2. Open the project folder `DT Unity`.
3. Open the main scene in `Assets/Scenes`.
4. Press **Play** to trigger procedural scene assembly automatically fetched from the running BaSyx AAS Server.

### 4. Physical Bench Controller (Optional Hardware Setup)
Flash `FMS_DT/FMS_DT.ino` onto your ESP32 / Industrial PLC bench controller using Arduino IDE or PlatformIO. The controller will publish I/O state changes over MQTT to sync the Unity Digital Twin in real-time.

---

## <div align="center">Key Results & Performance</div>

Empirical evaluation on a physical modular FMS bench and 800 parametric stress-testing runs revealed:
- **Cold-boot instantiation** of the physical pilot bench in under **2.8s**.
- **Steady-state rendering rates** exceeding **480 FPS** for small to medium layouts.
- **Scalability:** Near-linear scaling up to 250 modules and stable real-time execution up to 500 modules (>90 FPS).

---

## <div align="center">Citation</div>

If you use or reference this work in your research, please cite:

```bibtex
@mastersthesis{gouveia2026digitaltwins,
  author       = {Tiago Daniel Santos Gouveia},
  title        = {Automatic Generation of Simulation-Based Digital Twins from Asset Administration Shells},
  school       = {NOVA School of Science and Technology, NOVA University Lisbon},
  year         = {2026},
  type         = {Master's Thesis}
}
```

---

## <div align="center">License</div>

This project is licensed under the [MIT License](LICENSE).
