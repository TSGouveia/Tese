# Design Spec: URDF Robot Integration in Conveyor Wizard
Date: 2026-07-11
Status: Approved

## 1. Overview
This specification details the unifications of **Robot Studio Pro** (`create_robotic_arm.py`) and the **Conveyor Wizard** (`conveyor_wizard.py`). It enables users to select either a GLB file or a URDF/Xacro folder in the wizard, rendering the robotic arm using forward kinematics (FK) and generating the proper Robot AASX package (with `GeometryData`, `PositionData`, and `TelemetryData`) while skipping pin-based configuration steps.

---

## 2. Model Selection and Page Flow
We define a dynamic page navigation flow based on the loaded model type (`self.model_type = "GLB"` or `"URDF"`).

### 2.1 Navigation Mapping
- **GLB Page Sequence**:
  - Step 1 (Index 0): Model Selection (Choose GLB)
  - Step 2 (Index 1): Basic Info & Transform
  - Step 3 (Index 2): Configure Sensors
  - Step 4 (Index 3): Configure Actuators
  - Step 5 (Index 4): Control Logic
  - Step 6 (Index 5): Review & Deploy

- **URDF Page Sequence**:
  - Step 1 (Index 0): Model Selection (Choose URDF/Xacro Directory)
  - Step 2 (Index 1): Basic Info & Transform
  - Step 6 (Index 5): Review & Deploy (Steps 3, 4, and 5 are skipped)

---

## 3. UI Modifications in Step 1 (Model Selection)
We add a button next to "Select GLB File" on Page 1:
- **Button**: `"Select URDF / Xacro Folder"`
- **Action**: Opens a directory selection dialog. Imports and uses `XacroResolver`, `DependencyManager`, and macro dialogs from `create_robotic_arm` to resolve Xacro entry points, includes, and arguments.
- **Rendering**: Uses PyVista to calculate forward kinematics (FK) for all visual links of the robot, loads their respective mesh files (using trimesh/pyvista with manual primitive fallbacks), and displays the full robot assembly in the PyVista 3D plotter.
- **Tree View**: Populates the "Model Structure" tree with the robot's links and joints hierarchy.

---

## 4. AAS Deployment
When the user clicks "Deploy to AAS" on Step 6 (Preview & Deploy):

- If `self.model_type == "URDF"`:
  - Generates a robot AAS package.
  - Creates the submodels `GeometryData`, `PositionData`, and `TelemetryData` (with `LiveJoints` containing `self.robot.actuated_joints`).
  - Serializes and registers the AAS shell descriptor on the BaSyx registry with the robot descriptors.
- If `self.model_type == "GLB"`:
  - Generates the standard conveyor kit package with `VisualStructure`, `VirtualPins`, `BehaviorMapping`, and `ControlLogic`.

---

## 5. Success Criteria
- [ ] Users can browse and load URDF/Xacro folders in the Conveyor Wizard.
- [ ] Xacro includes, dependencies, and arguments are resolved correctly using dialogs.
- [ ] The robotic arm is rendered visually in the PyVista 3D canvas.
- [ ] Navigation skips virtual pin and logic steps for URDF models.
- [ ] Deploying a URDF creates a valid Robot AAS containing `GeometryData`, `PositionData`, and `TelemetryData` submodels on BaSyx.
