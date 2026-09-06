# 📐 System Architecture Specifications & UML Diagrams (AAS + Unity + Digital Twin)

This document contains the complete technical specification for all system modules, standard AAS JSON Submodel Schemas, and **5 UML Diagrams** in Mermaid format, ready for copying into **Draw.io** or rendering directly in Markdown/LaTeX thesis documents.

> 💡 **How to import into Draw.io**:
> 1. Open [Draw.io](https://app.diagrams.net).
> 2. Navigate to: **Arrange** $\rightarrow$ **Insert** $\rightarrow$ **Advanced** $\rightarrow$ **Mermaid**.
> 3. Paste the code for any diagram below and click **Insert**.

---

## 1. System Architecture Overview (Component Diagram)

```mermaid
graph TB
    subgraph Layer1["1. Authoring and Configuration Layer - AAS Client Python"]
        PyWiz["Conveyor Wizard / CLI"]
        PyBasyx["BaSyx SDK & REST Client"]
        PyWiz --> PyBasyx
    end

    subgraph Layer2["2. Middleware Layer - BaSyx AAS Server"]
        Registry["AAS Registry<br/>(Discovery / Directory)"]
        AASRepo["AAS Repository<br/>(Shells Metadata)"]
        SMRepo["Submodel Repository<br/>(TechnicalData, Behavior, Pins, Rules)"]
    end

    subgraph Layer3["3. Simulation and Digital Twin Layer - Unity Engine"]
        BM["BaSyxManager<br/>(AAS Discovery & Loader)"]
        Imp["AASKitImporter / URDFImporter<br/>(Hierarchy & Physics Setup)"]
        
        subgraph Controllers["Asset Controllers"]
            SC["AASSensorController<br/>(Sensors & Proxies)"]
            AC["AASActuatorController<br/>(Actuators & Physics Transport)"]
            RE["AASRuleEngine<br/>(Logic & Snap Engine)"]
        end
        
        AL["AASArduinoLink<br/>(TCP Socket Client)"]
        OM["OperationModeManager<br/>(VC vs DT Mode)"]
    end

    subgraph Layer4["4. Physical Hardware Layer"]
        Arduino["Arduino / PLC<br/>(TCP Server - Port I/O)"]
    end

    %% Layer Connections
    PyBasyx -->|1. Register Shells| AASRepo
    PyBasyx -->|2. Register Submodels| SMRepo
    PyBasyx -->|3. Register Endpoints| Registry

    BM -->|Query Shells| Registry
    BM -->|Fetch Metadata| AASRepo
    BM -->|Fetch JSON Deep| SMRepo
    
    BM -->|Build Geometry| Imp
    BM -->|Instantiate & Init| Controllers

    SC -->|VC Mode: HTTP PUT Inputs| SMRepo
    SMRepo -->|VC Mode: HTTP GET Outputs| AC

    AL -->|DT Mode: TCP Socket Out| Arduino
    Arduino -->|DT Mode: TCP Socket In| AL
    AL -->|DT Mode: Dispatch State Events| SC
    AL -->|DT Mode: Dispatch State Events| AC
    AC -->|DT Mode: Sync State Back| SMRepo

    OM -->|Switch Mode| SC
    OM -->|Switch Mode| AC

    %% Node Styles (Draw.io Compatible)
    style PyWiz fill:#e1f5fe,stroke:#0288d1,stroke-width:1px
    style PyBasyx fill:#e1f5fe,stroke:#0288d1,stroke-width:1px
    style Registry fill:#fff3e0,stroke:#f57c00,stroke-width:1px
    style AASRepo fill:#fff3e0,stroke:#f57c00,stroke-width:1px
    style SMRepo fill:#fff3e0,stroke:#f57c00,stroke-width:1px
    style BM fill:#e8f5e9,stroke:#388e3c,stroke-width:1px
    style Imp fill:#e8f5e9,stroke:#388e3c,stroke-width:1px
    style SC fill:#e8f5e9,stroke:#388e3c,stroke-width:1px
    style AC fill:#e8f5e9,stroke:#388e3c,stroke-width:1px
    style RE fill:#e8f5e9,stroke:#388e3c,stroke-width:1px
    style AL fill:#e8f5e9,stroke:#388e3c,stroke-width:1px
    style OM fill:#e8f5e9,stroke:#388e3c,stroke-width:1px
    style Arduino fill:#f3e5f5,stroke:#7b1fa2,stroke-width:1px
```

---

## 2. Expanded AAS Creation & Publishing Pipeline (Python $\rightarrow$ BaSyx)

```mermaid
sequenceDiagram
    autonumber
    actor Eng as Automation Engineer
    participant Py as Python AAS Client
    participant Reg as BaSyx Registry
    participant Repo as BaSyx AAS Repository
    participant SM as BaSyx Submodel Repository

    Eng->>Py: Launch Conveyor Wizard (6-Step Pipeline)
    
    Note over Py: Step 1: Model Selection
    Py->>Eng: Prompt: Select 3D Source (.glb File OR .urdf / .xacro Folder)
    Eng-->>Py: Input: Selects GLB / URDF Asset Path

    Note over Py: Step 2: System Info, Communication & Transform
    Py->>Eng: Prompt: System Info (Kit Name, AAS ID, Description, Is Dynamic)
    Py->>Eng: Prompt: Communication Settings (Protocol: None/Sockets, IP Address, Port)
    Py->>Eng: Prompt: System Transform (Position X/Y/Z, Rotation X/Y/Z, Scale X/Y/Z)
    Eng-->>Py: Input: Fills Metadata, Sockets (IP:Port), and 3D Transform

    Note over Py: Step 3: Sensors Configuration
    Py->>Eng: Prompt: Add Sensor (PinID, Detection Node, Behavior: TriggerZone/Proximity)
    Py->>Eng: Prompt: Sensor Parameters (TargetFilter, ActiveLow, Visible, Snap Product, Real Port ID)
    Eng-->>Py: Input: Configures Input Sensors & Hardware Ports

    Note over Py: Step 4: Actuators Configuration
    Py->>Eng: Prompt: Add Actuator (PinID, Target Node, Behavior: Conveyor/RotateContinuous/TranslateContinuous/Linear)
    Py->>Eng: Prompt: Actuator Parameters (Axis X/Y/Z, Speed, Stop Sensor, Real Port ID)
    Eng-->>Py: Input: Configures Output Actuators & Hardware Ports

    Note over Py: Step 5: AASX Package Build & BaSyx Deployment
    Py->>Py: Builds .aasx Package File (Contains Submodels & GLB Mesh)
    Py->>Repo: POST /upload (Uploads .aasx Binary Package File)
    Repo-->>Py: 200 OK / 201 Created (BaSyx Extracts Shell & Submodels into Repositories)

    Py->>Reg: POST /shell-descriptors (Payload: Descriptor JSON for AAS & Submodel Endpoints)
    Reg-->>Py: 201 Created
    
    Note over Eng, SM: AAS Asset Package & Registry Descriptors Successfully Deployed
```



### Step 1 · Model Selection

```mermaid
flowchart LR
    Eng(["?? Automation Engineer"]):::actor

    subgraph S1["Step 1 · Model Selection"]
        direction TB
        UC1A(["Select GLB 3D Asset File"]):::uc
        UC1B(["Select URDF / Xacro Folder"]):::uc
        UC1C(["Preview 3D Model in Viewer"]):::uc
        UC1D(["Browse Node Hierarchy Tree"]):::uc
        UC1A -.->|"include"| UC1C
        UC1B -.->|"include"| UC1C
        UC1C -.->|"include"| UC1D
    end

    Eng --> UC1A
    Eng --> UC1B

    classDef actor fill:#fef9c3,stroke:#ca8a04,stroke-width:2px,color:#1c1917,font-weight:bold
    classDef uc    fill:#e0f2fe,stroke:#0284c7,stroke-width:1.5px,color:#0c4a6e
    style S1 fill:#f0fdf4,stroke:#16a34a,stroke-width:1.5px
```

---

### Step 2 · System Info, Communication & Transform

```mermaid
flowchart LR
    Eng(["?? Automation Engineer"]):::actor

    subgraph S2["Step 2 · System Info, Communication & Transform"]
        direction TB
        UC2A(["Set Kit Name & AAS ID"]):::uc
        UC2B(["Set Description & Dynamic Flag"]):::uc
        UC2C(["Configure Comm Protocol None or Sockets"]):::uc
        UC2D(["Set Endpoint IP & Port"]):::uc
        UC2E(["Define 3D Transform Pos / Rot / Scale"]):::uc
        UC2C -.->|"include"| UC2D
    end

    Eng --> UC2A
    Eng --> UC2B
    Eng --> UC2C
    Eng --> UC2E

    classDef actor fill:#fef9c3,stroke:#ca8a04,stroke-width:2px,color:#1c1917,font-weight:bold
    classDef uc    fill:#e0f2fe,stroke:#0284c7,stroke-width:1.5px,color:#0c4a6e
    style S2 fill:#eff6ff,stroke:#3b82f6,stroke-width:1.5px
```

---

### Step 3 · Sensors Configuration (Inputs)

```mermaid
flowchart LR
    Eng(["?? Automation Engineer"]):::actor

    subgraph S3["Step 3 · Sensors Configuration - Inputs"]
        direction TB
        UC3A(["Add Input Sensor"]):::uc
        UC3B(["Assign Sensor Pin ID"]):::uc
        UC3C(["Select Detection Node from Tree"]):::uc
        UC3D(["Choose Behavior TriggerZone or Proximity"]):::uc
        UC3E(["Set Target Filter Tag"]):::uc
        UC3F(["Configure ActiveLow Flag"]):::uc
        UC3G(["Enable Snap Product on Detect"]):::uc
        UC3H(["Map Real Hardware Port ID"]):::uc
        UC3I(["Configure Move-on-State position / rotation"]):::uc
        UC3J(["Remove Sensor"]):::uc

        UC3A -.->|"include"| UC3B
        UC3A -.->|"include"| UC3C
        UC3A -.->|"include"| UC3D
        UC3E -.->|"extend"| UC3D
        UC3F -.->|"extend"| UC3D
        UC3G -.->|"extend"| UC3D
        UC3H -.->|"extend"| UC3D
        UC3I -.->|"extend"| UC3D
    end

    Eng --> UC3A
    Eng --> UC3J

    classDef actor fill:#fef9c3,stroke:#ca8a04,stroke-width:2px,color:#1c1917,font-weight:bold
    classDef uc    fill:#e0f2fe,stroke:#0284c7,stroke-width:1.5px,color:#0c4a6e
    style S3 fill:#fdf4ff,stroke:#a855f7,stroke-width:1.5px
```

---

### Step 4 · Actuators Configuration (Outputs)

```mermaid
flowchart LR
    Eng(["?? Automation Engineer"]):::actor

    subgraph S4["Step 4 · Actuators Configuration - Outputs"]
        direction TB
        UC4A(["Add Output Actuator"]):::uc
        UC4B(["Assign Actuator Pin ID"]):::uc
        UC4C(["Select Target Node from Tree"]):::uc
        UC4D(["Choose Behavior Conveyor / Rotate / Translate / Linear"]):::uc
        UC4E(["Define Motion Axis X / Y / Z"]):::uc
        UC4F(["Set Movement Speed"]):::uc
        UC4G(["Assign Stop Sensor Component"]):::uc
        UC4H(["Map Real Hardware Port ID"]):::uc
        UC4I(["Visualize Actuator Arrow in 3D View"]):::uc
        UC4J(["Remove Actuator"]):::uc

        UC4A -.->|"include"| UC4B
        UC4A -.->|"include"| UC4C
        UC4A -.->|"include"| UC4D
        UC4E -.->|"extend"| UC4D
        UC4F -.->|"extend"| UC4D
        UC4G -.->|"extend"| UC4D
        UC4H -.->|"extend"| UC4D
        UC4I -.->|"extend"| UC4A
    end

    Eng --> UC4A
    Eng --> UC4J

    classDef actor fill:#fef9c3,stroke:#ca8a04,stroke-width:2px,color:#1c1917,font-weight:bold
    classDef uc    fill:#e0f2fe,stroke:#0284c7,stroke-width:1.5px,color:#0c4a6e
    style S4 fill:#fff7ed,stroke:#f97316,stroke-width:1.5px
```

---

### Step 5 · Review, Build & Deploy

```mermaid
flowchart LR
    Eng(["?? Automation Engineer"]):::actor
    BaSyxRepo(["BaSyx AAS Repository :8081"]):::sysactor
    BaSyxReg(["BaSyx AAS Registry :8082"]):::sysactor

    subgraph S5["Step 5 · Review, Build & Deploy"]
        direction TB
        UC5A(["Preview AAS JSON Descriptor"]):::uc
        UC5B(["Validate Numeric Fields"]):::uc
        UC5C(["Build AAS Shell & Submodels in Memory"]):::uc
        UC5D(["Build VisualStructure Submodel"]):::uc
        UC5E(["Build VirtualPins Submodel Inputs + Outputs"]):::uc
        UC5F(["Build BehaviorMapping Submodel"]):::uc
        UC5G(["Build AssetInterfacesDescription Submodel"]):::uc
        UC5H(["Collect & Bundle 3D Assets glb / urdf + meshes"]):::uc
        UC5I(["Write .aasx Package Archive"]):::uc
        UC5J(["Check for Existing AAS on Server"]):::uc
        UC5K(["Overwrite Existing AAS Delete + Re-upload"]):::uc
        UC5L(["POST /upload .aasx to AAS Repository"]):::uc
        UC5M(["POST /shell-descriptors to AAS Registry"]):::uc

        UC5A -.->|"include"| UC5B
        UC5B -.->|"include"| UC5C
        UC5C -.->|"include"| UC5D
        UC5C -.->|"include"| UC5E
        UC5C -.->|"include"| UC5F
        UC5C -.->|"include"| UC5G
        UC5C -.->|"include"| UC5H
        UC5H -.->|"include"| UC5I
        UC5I -.->|"include"| UC5J
        UC5K -.->|"extend"| UC5J
        UC5K -.->|"include"| UC5L
        UC5J -.->|"include"| UC5L
        UC5L -.->|"include"| UC5M
    end

    Eng --> UC5A
    UC5L --> BaSyxRepo
    UC5M --> BaSyxReg
    UC5J -->|"GET /shells conflict check"| BaSyxRepo
    UC5K -->|"DELETE /shells & /submodels"| BaSyxRepo

    classDef actor    fill:#fef9c3,stroke:#ca8a04,stroke-width:2px,color:#1c1917,font-weight:bold
    classDef sysactor fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#1c1917,font-weight:bold
    classDef uc       fill:#e0f2fe,stroke:#0284c7,stroke-width:1.5px,color:#0c4a6e
    style S5 fill:#fef2f2,stroke:#ef4444,stroke-width:1.5px
```

---

### Operações Auxiliares

```mermaid
flowchart LR
    Eng(["?? Automation Engineer"]):::actor
    BaSyxRepo(["BaSyx AAS Repository :8081"]):::sysactor

    subgraph SAUX["Auxiliary Operations"]
        direction TB
        UCA1(["Manage Deployed AAS CRUD List"]):::ucaux
        UCA2(["Preview Deployed Layout 3D Scene"]):::ucaux
        UCA3(["Program Deployed AAS Rules"]):::ucaux
    end

    Eng --> UCA1
    Eng --> UCA2
    Eng --> UCA3
    UCA1 -->|"GET / DELETE /shells"| BaSyxRepo
    UCA3 -->|"GET & PUT /submodels"| BaSyxRepo

    classDef actor    fill:#fef9c3,stroke:#ca8a04,stroke-width:2px,color:#1c1917,font-weight:bold
    classDef sysactor fill:#ede9fe,stroke:#7c3aed,stroke-width:2px,color:#1c1917,font-weight:bold
    classDef ucaux    fill:#fce7f3,stroke:#db2777,stroke-width:1.5px,color:#500724
    style SAUX fill:#f1f5f9,stroke:#94a3b8,stroke-width:1.5px,stroke-dasharray:4 4
```
---

## 3. Discovery, Parsing & Dynamic Instantiation in Unity

```mermaid
flowchart TD
    Start([Unity Application Start]) --> GetShells[GET /shells from BaSyx Server]
    GetShells --> LoopShells{Shells Exist on Server?}

    LoopShells -->|Yes| FetchSubmodels[GET /submodels with level=deep]
    LoopShells -->|No| Ready[Scene Ready for Simulation]

    FetchSubmodels --> CheckType{Geometry Format?}

    CheckType -->|GLB File| ImpGLB[AASKitImporter: Import GLTF/GLB Meshes]
    CheckType -->|URDF File| ImpURDF[AASUrdfImporter: Build Articulated Robot]
    CheckType -->|Logical Only| CreateEmpty[Create Empty GameObject in Scene]

    ImpGLB --> NormHierarchy[NormalizeHierarchy: Reset Scale/Rotation & Normalize Names]
    ImpURDF --> NormHierarchy

    NormHierarchy --> TagProducts[Add AAS.DynamicProduct Marker to Products Only]
    TagProducts --> CreateContainer[Parent to Container AAS_Kits_Container]
    CreateEmpty --> CreateContainer

    CreateContainer --> AttachControllers[Attach & Initialize C# Components]
    
    AttachControllers --> InitSensors[AASSensorController.Init: Build Proxies & Colliders]
    AttachControllers --> InitActuators[AASActuatorController.Init: Configure Actuators & Conveyors]
    AttachControllers --> InitRules[AASRuleEngine.Init: Load Logic Rules]

    InitSensors --> LoopShells
    InitActuators --> LoopShells
    InitRules --> LoopShells

    style Start fill:#4caf50,color:#fff
    style Ready fill:#2196f3,color:#fff
    style CheckType fill:#ff9800,color:#fff
```

---

## 4. Runtime Execution: Virtual Commissioning vs Digital Twin

```mermaid
sequenceDiagram
    autonumber
    participant Prod as DynamicProduct (Workpiece)
    participant Sens as AASSensorController / SensorPhysicsProxy
    participant Act as AASActuatorController / ConveyorSurface
    participant Mode as OperationModeManager
    participant BaSyx as BaSyx Submodel Repository
    participant Sock as AASArduinoLink (TCP Socket)
    participant HW as Real Hardware (PLC / Arduino)

    Note over Prod, HW: PHASE 1: VIRTUAL COMMISSIONING (VC MODE)
    Mode->>Sens: SetMode(VirtualCommissioning)
    Mode->>Act: SetMode(VirtualCommissioning)
    
    Prod->>Sens: Enters Trigger Collider (OnTriggerEnter)
    Sens->>Sens: MatchesFilter() -> Verify DynamicProduct
    Sens->>BaSyx: PUT /submodel-elements/Inputs.Sensor_Product = true
    
    loop Polling Loop (20Hz)
        Act->>BaSyx: GET /submodel-elements/Outputs
        BaSyx-->>Act: Actuator State = true
    end
    
    Act->>Act: FixedUpdate: Move 3D Actuator
    Act->>Prod: ConveyorSurface: Transport DynamicProduct in 3D Space

    Note over Prod, HW: PHASE 2: DIGITAL TWIN (DT MODE)
    Mode->>Sens: SetMode(DigitalTwin)
    Mode->>Act: SetMode(DigitalTwin)
    Sens->>Sens: Disable Virtual HTTP Push
    Act->>Act: Disable HTTP Polling

    HW->>Sock: Socket Package: {"Port":"I0_0", "Value":1}
    Sock->>Sens: Trigger Callback OnArduinoPortChanged("I0_0", true)
    Sens->>Sens: Update realState & lastState in Unity

    HW->>Sock: Socket Package: {"Port":"R0_0", "Value":1}
    Sock->>Act: Trigger Callback OnArduinoPortChanged("R0_0", true)
    Act->>Act: Overwrite currentState = true & Move 3D Model
    Act->>BaSyx: Async PUT to Keep AAS Server Synchronized
```

---

## 5. Complete C# Framework UML Class Diagram

```mermaid
classDiagram
    class BaSyxManager {
        -string basyxServerUrl
        -List~GameObject~ instantiatedKits
        +bool IsStartupComplete
        +Start() void
        -LoadAllAAS() IEnumerator
        -ProcessShell(JObject shell) IEnumerator
    }

    class AASKitImporter {
        +ImportKit(string glbPath) KitImportData
        -NormalizeHierarchy(Transform root) void
    }

    class AASSensorController {
        -Dictionary~string,SensorBinding~ componentToSensor
        -bool _bindingsLoaded
        +Init(serverUrl, pinsId, behaviorId, componentMap) void
        +GetSensorState(pinId, out state, useReal) bool
        -LoadBindingsRoutine(componentMap) IEnumerator
        -ApplyOperationMode(mode) void
    }

    class SensorPhysicsProxy {
        +SensorBinding binding
        +Action~bool,bool,GameObject,GameObject~ onStateChange
        +HashSet~Collider~ touching
        -OnTriggerEnter(Collider other) void
        -OnTriggerExit(Collider other) void
        -MatchesFilter(Collider other) bool
        -CheckState(force) void
    }

    class AASActuatorController {
        +List~ActuatorBinding~ bindings
        -bool isInitialized
        +Init(serverUrl, pinsId, behaviorId, componentMap) void
        -FixedUpdate() void
        -StartDTConnection() void
        -OnArduinoPortChanged(binding, value) void
        -UpdateActuatorAASAsync(pinId, value) IEnumerator
    }

    class ConveyorSurface {
        +GameObject rootConveyor
        -AASActuatorController controller
        +Setup(root, ctrl) void
        -Register(GameObject other) void
        -OnCollisionStay(Collision c) void
        -OnTriggerStay(Collider other) void
    }

    class ConveyorContactTracker {
        -Rigidbody rb
        +AASActuatorController actuatorCtrl
        +NotifyContact(root, bindings) void
        -FixedUpdate() void
    }

    class AASRuleEngine {
        -List~RuleDefinition~ rules
        +Init(serverUrl, behaviorId) void
        -EvaluateRulesLoop() IEnumerator
        -ExecuteAction(action) void
    }

    class AASArduinoLink {
        +AASArduinoLink Instance
        -TcpClient _client
        -NetworkStream _stream
        -Dictionary~string,Action~bool~~ _portCallbacks
        +StartConnection(ip, port) void
        +Subscribe(portId, callback) void
        +Unsubscribe(portId, callback) void
        -ListenLoop() IEnumerator
    }

    class OperationModeManager {
        +OperationMode Current
        +event Action~OperationMode~ OnModeChanged
        +SetMode(OperationMode mode) void
    }

    class DynamicProduct {
        <<Marker Component>>
    }

    %% Relationships
    BaSyxManager ..> AASKitImporter : uses
    BaSyxManager ..> AASSensorController : instantiates
    BaSyxManager ..> AASActuatorController : instantiates
    BaSyxManager ..> AASRuleEngine : instantiates

    AASSensorController *-- SensorPhysicsProxy : attaches to sensors
    AASActuatorController *-- ConveyorSurface : attaches to surfaces
    ConveyorSurface ..> ConveyorContactTracker : attaches exclusively to DynamicProduct
    ConveyorContactTracker ..> DynamicProduct : validates presence

    AASActuatorController ..> AASArduinoLink : subscribes ports in DT Mode
    AASSensorController ..> AASArduinoLink : subscribes ports in DT Mode

    AASSensorController ..> OperationModeManager : listens to OnModeChanged
    AASActuatorController ..> OperationModeManager : listens to OnModeChanged
```

---

# 🗂️ AAS JSON Submodeling Specification & Deep-Dive

This section details the JSON metamodel hierarchy used to serialize industrial asset definitions into the BaSyx AAS Repository.

```mermaid
graph TD
    AAS["AAS Shell e.g. AAS_Punch_FMS"] --> SM1["Submodel: TechnicalData"]
    AAS --> SM2["Submodel: AssetInterfacesDescription"]
    AAS --> SM3["Submodel: BehaviorMapping"]

    SM1 --> TD1["Property: Position (X, Y, Z)"]
    SM1 --> TD2["Property: Rotation (X, Y, Z)"]
    SM1 --> TD3["Property: Scale (X, Y, Z)"]
    SM1 --> TD4["File/Attachment: Mesh (.glb / .urdf)"]
    SM1 --> TD5["Collection: DynamicObjects"]

    SM2 --> AID1["Property: Protocol (tcp)"]
    SM2 --> AID2["Property: EndpointIP (192.168.1.50)"]
    SM2 --> AID3["Property: EndpointPort (8888)"]

    SM3 --> BM1["Collection: Inputs (Sensors)"]
    SM3 --> BM2["Collection: Outputs (Actuators)"]
    SM3 --> BM3["Collection: Rules (Automation Logic)"]

    BM1 --> S1["Sensor Collection: Sensor_Product"]
    S1 --> S1P["Parameters: TargetFilter, ActiveLow, Visible, SnapTarget, RealPortID"]

    BM2 --> A1["Actuator Collection: Punch_Forward"]
    A1 --> A1P["Parameters: AxisX/Y/Z, Speed, LimitMin/Max, StopSensorComponent, RealPortID"]

    BM3 --> R1["Rule Collection: Rule_PunchSnap"]
    R1 --> R1P["Properties: Type, ConditionSim, ConditionReal, Action"]
```

---

## 📄 Submodel Schemas & JSON Examples

### 1. `TechnicalData` (Visual & Spatial Submodel)
Stores 3D model reference URLs, spatial coordinates, scale factors, and product identification lists.

```json
{
  "idShort": "TechnicalData",
  "modelType": "Submodel",
  "submodelElements": [
    { "idShort": "PositionX", "modelType": "Property", "valueType": "xs:float", "value": "9.0" },
    { "idShort": "PositionY", "modelType": "Property", "valueType": "xs:float", "value": "0.0" },
    { "idShort": "PositionZ", "modelType": "Property", "valueType": "xs:float", "value": "0.0" },
    { "idShort": "ScaleX", "modelType": "Property", "valueType": "xs:float", "value": "0.5" },
    { "idShort": "ScaleY", "modelType": "Property", "valueType": "xs:float", "value": "0.5" },
    { "idShort": "ScaleZ", "modelType": "Property", "valueType": "xs:float", "value": "0.5" },
    { "idShort": "Mesh", "modelType": "File", "contentType": "model/gltf-binary", "value": "Punch_FMS.glb" },
    {
      "idShort": "DynamicObjects",
      "modelType": "SubmodelElementCollection",
      "value": [
        { "idShort": "Obj_0", "modelType": "Property", "valueType": "xs:string", "value": "Product_Cube" }
      ]
    }
  ]
}
```

---

### 2. `AssetInterfacesDescription` (Hardware Communication Submodel)
Defines the physical socket communication interface parameters required for Digital Twin synchronization.

```json
{
  "idShort": "AssetInterfacesDescription",
  "modelType": "Submodel",
  "submodelElements": [
    { "idShort": "Protocol", "modelType": "Property", "valueType": "xs:string", "value": "tcp" },
    { "idShort": "EndpointIP", "modelType": "Property", "valueType": "xs:string", "value": "192.168.1.50" },
    { "idShort": "EndpointPort", "modelType": "Property", "valueType": "xs:integer", "value": "8888" }
  ]
}
```

---

### 3. `BehaviorMapping` (Sensors, Actuators & Rules Submodel)
Configures simulation proxies, physical I/O ports, collision filters, and logic rules.

```json
{
  "idShort": "BehaviorMapping",
  "modelType": "Submodel",
  "submodelElements": [
    {
      "idShort": "Inputs",
      "modelType": "SubmodelElementCollection",
      "value": [
        {
          "idShort": "Sensor_Product",
          "modelType": "SubmodelElementCollection",
          "value": [
            { "idShort": "PinID", "modelType": "Property", "valueType": "xs:string", "value": "Sensor_Product" },
            { "idShort": "Component", "modelType": "Property", "valueType": "xs:string", "value": "TriggerZone" },
            { "idShort": "Type", "modelType": "Property", "valueType": "xs:string", "value": "TriggerZone" },
            {
              "idShort": "Parameters",
              "modelType": "SubmodelElementCollection",
              "value": [
                { "idShort": "TargetFilter", "modelType": "Property", "valueType": "xs:string", "value": "Metal" },
                { "idShort": "ActiveLow", "modelType": "Property", "valueType": "xs:boolean", "value": "false" },
                { "idShort": "Visible", "modelType": "Property", "valueType": "xs:boolean", "value": "false" },
                { "idShort": "RealSensorEnabled", "modelType": "Property", "valueType": "xs:boolean", "value": "true" },
                { "idShort": "RealPortID", "modelType": "Property", "valueType": "xs:string", "value": "I0_0" }
              ]
            }
          ]
        }
      ]
    },
    {
      "idShort": "Outputs",
      "modelType": "SubmodelElementCollection",
      "value": [
        {
          "idShort": "Punch_Forward",
          "modelType": "SubmodelElementCollection",
          "value": [
            { "idShort": "PinID", "modelType": "Property", "valueType": "xs:string", "value": "Punch_Forward" },
            { "idShort": "Component", "modelType": "Property", "valueType": "xs:string", "value": "Torre Horizontal" },
            { "idShort": "Type", "modelType": "Property", "valueType": "xs:string", "value": "TranslateContinuous" },
            {
              "idShort": "Parameters",
              "modelType": "SubmodelElementCollection",
              "value": [
                { "idShort": "AxisX", "modelType": "Property", "valueType": "xs:float", "value": "1.0" },
                { "idShort": "AxisY", "modelType": "Property", "valueType": "xs:float", "value": "0.0" },
                { "idShort": "AxisZ", "modelType": "Property", "valueType": "xs:float", "value": "0.0" },
                { "idShort": "Speed", "modelType": "Property", "valueType": "xs:float", "value": "1.0" },
                { "idShort": "StopSensorComponent", "modelType": "Property", "valueType": "xs:string", "value": "Sensor_Forward" },
                { "idShort": "RealActuatorEnabled", "modelType": "Property", "valueType": "xs:string", "value": "true" },
                { "idShort": "RealPortID", "modelType": "Property", "valueType": "xs:string", "value": "R0_0" }
              ]
            }
          ]
        }
      ]
    },
    {
      "idShort": "Rules",
      "modelType": "SubmodelElementCollection",
      "value": [
        {
          "idShort": "Rule_SnapOnProductArrival",
          "modelType": "SubmodelElementCollection",
          "value": [
            { "idShort": "Type", "modelType": "Property", "valueType": "xs:string", "value": "if" },
            { "idShort": "ConditionSim", "modelType": "Property", "valueType": "xs:string", "value": "Inputs.Sensor_Product" },
            { "idShort": "ConditionReal", "modelType": "Property", "valueType": "xs:string", "value": "Inputs.Sensor_Product" },
            {
              "idShort": "Action",
              "modelType": "SubmodelElementCollection",
              "value": [
                { "idShort": "ActionType", "modelType": "Property", "valueType": "xs:string", "value": "snap" },
                { "idShort": "Target", "modelType": "Property", "valueType": "xs:string", "value": "TriggerZone" }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

---

# 📖 Module Technical Specifications

### Module 1: Python AAS Client & Authoring (`AAS Client` / `conveyor_wizard.py`)
* **Role**: Models asset submodels (`TechnicalData`, `AssetInterfacesDescription`, `BehaviorMapping`) and packages them into a binary `.aasx` archive (including the `.glb` mesh file). Deploys to BaSyx via two HTTP calls: `POST /upload` (multipart binary upload of the `.aasx` package to the AAS+Submodel Repositories) and `POST /shell-descriptors` (registers the AAS endpoint descriptor in the BaSyx Registry).

### Module 2: BaSyx Middleware Server
* **Role**: Serves as the central AAS Server (Single Source of Truth), decoupling configuration from Unity execution. Comprises the **AAS Registry**, **AAS Repository**, and **Submodel Repository**.

### Module 3: Unity Discovery & Loading (`BaSyxManager` & Importers)
* **Role**: Dynamically queries the BaSyx server at startup (`GET /shells`), imports 3D geometry (`.glb` / `.urdf`), bakes transform scaling, and injects the `DynamicProduct` marker component onto dynamic workpieces.

### Module 4: Sensor Management (`AASSensorController` & `SensorPhysicsProxy`)
* **Role**: Creates kinematic trigger colliders. `MatchesFilter` requires `DynamicProduct` when filtering for `"Metal"` (ensuring actuators like punches do not trigger product sensors). In VC mode, updates AAS via HTTP `PUT`. In DT mode, listens to hardware TCP socket events.

### Module 5: Actuator Control & Physics Transport (`AASActuatorController`)
* **Role**: Translates AAS output states into 3D movements (`TranslateContinuous`, `RotateContinuous`, `TranslateFixed`, `RotateHinge`). `ConveyorSurface` + `ConveyorContactTracker` transports dynamic workpieces without parent-child coupling, strictly ignoring static structural parts and sensors.

### Module 6: Logic Engine (`AASRuleEngine`)
* **Role**: Evaluates JSON logic rules (`if`, `if_else`) in a 10Hz coroutine loop, executing actions such as product snapping or visibility toggling.

### Module 7: Hardware Communication (`AASArduinoLink`)
* **Role**: A singleton C# TCP Socket client maintaining bi-directional socket connections to physical PLCs/Arduinos and dispatching port events (`I0_0`, `R0_0`) to Unity controllers.
