# URDF Robot Integration in Conveyor Wizard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Unify robot arm creation (`create_robotic_arm.py`) and conveyor creation (`conveyor_wizard.py`) inside the step-by-step wizard, allowing users to browse/load URDFs, render robotic arms via forward kinematics in PyVista, and export the proper Robot AASX packages.

**Architecture:**
1. **PyQt6 UI**: Add a "Select URDF / Xacro Folder" button in Step 1. Enable dynamic navigation that skips sensor/actuator/logic pages for URDF models (jumping directly from Step 2 to Step 6).
2. **Visualizer Rendering**: Port the URDF loading (xacro resolving, arguments expansion) and the PyVista forward kinematics rendering (link mesh mapping, primitive fallbacks) from `create_robotic_arm.py`.
3. **AASX Generation**: Replicate the AASX packaging code for URDF robots (`GeometryData` with embedded includes/meshes, `PositionData`, and `TelemetryData` with actuated joints) in `deploy_to_aas` when the model type is URDF.

**Tech Stack:** PyQt6, Python urdfpy, trimesh, pyvista, basyx-python-sdk.

---

### Task 1: Integrate URDF Loader, Rendering, and Step Navigation in Conveyor Wizard

**Files:**
- Modify: `AAS Client/conveyor_wizard.py`

- [ ] **Step 1.1: Import modules from `create_robotic_arm`**
  Add imports at the top of `conveyor_wizard.py`:
  ```python
  from create_robotic_arm import (
      XacroResolver,
      DependencyManager,
      DependencyDialog,
      XacroArgsDialog,
      expand_xacro_final,
      URDF
  )
  ```

- [ ] **Step 1.2: Add state variables and setup UI buttons**
  - Add state variables in `ConveyorWizard.__init__`:
    - `self.model_type = "GLB"`
    - `self.robot = None`
    - `self.current_urdf_xml = ""`
    - `self.current_urdf_path = ""`
    - `self.current_urdf_tree = None`
    - `self.files_to_upload = {}`
    - `self.current_robot_root = ""`
  - Add button in `setup_steps` page 1 UI layout next to GLB select:
    ```python
    self.btn_select_urdf = QPushButton("Select URDF / Xacro Folder")
    self.btn_select_urdf.setMinimumHeight(55)
    self.btn_select_urdf.setStyleSheet("background-color: #2980b9;")
    self.btn_select_urdf.clicked.connect(self.browse_urdf)
    ```

- [ ] **Step 1.3: Implement `browse_urdf` and rendering methods**
  - Replicate `load_robot` logic as `browse_urdf` inside `ConveyorWizard`:
    - Open directory dialog, map directory files using `XacroResolver`.
    - Present xacro includes/arguments dialogs if needed.
    - Write temp parsed URDF file.
    - Call `self.robot = URDF.load(temp)` and set `self.model_type = "URDF"`.
    - Trigger `self._build_urdf_view()`.
  - Implement `_build_urdf_view()`:
    - Clear plotter, calculate forward kinematics: `fk = self.robot.visual_geometry_fk()`.
    - Iterate visual links, load mesh files (checking scaling and manual primitives fallback: Cylinder, Box, Sphere, Mesh with trimesh).
    - Wrap and add meshes to the PyVista canvas, populate `self.meshes` and `self.actors`.
    - Populate the model tree structure (`self.node_tree`) with the links and joints of the robot.

- [ ] **Step 1.4: Implement dynamic step navigation**
  - In `next_step(self)`:
    - If `self.model_type == "URDF"` and current index is 1 (Step 2: Basic Info & Transform), jump directly to page index 5 (Review & Deploy).
  - In `prev_step(self)`:
    - If `self.model_type == "URDF"` and current index is 5, jump directly to page index 1.
  - In `update_nav(self)`:
    - If `self.model_type == "URDF"`, set the step label to:
      - Index 0: `Step 1 of 3: Model Selection`
      - Index 1: `Step 2 of 3: Basic Info & Transform`
      - Index 5: `Step 3 of 3: Review & Deploy`
      Ensure `self.btn_next` label is set to "Deploy to AAS" when on page index 5.

- [ ] **Step 1.5: Commit UI and Navigation changes**
  ```bash
  git add "AAS Client/conveyor_wizard.py"
  git commit -m "feat: integrate URDF model loading, rendering, and step navigation"
  ```

---

### Task 2: Implement Robot AASX Generation inside deploy_to_aas

**Files:**
- Modify: `AAS Client/conveyor_wizard.py`

- [ ] **Step 2.1: Add URDF JSON preview representation**
  Update `update_json_preview` so that if `self.model_type == "URDF"`, it builds the JSON preview showing the robot model, joints, and transformation, matching the format of robotic arms.

- [ ] **Step 2.2: Add Robot AASX packing to `deploy_to_aas`**
  Modify `deploy_to_aas` to branch based on `self.model_type`:
  - If `self.model_type == "URDF"`:
    - Package URDF-specific submodels: `GeometryData`, `PositionData`, `TelemetryData`.
    - Embed the main URDF XML content and all referenced mesh files (`self.files_to_upload`) into the AASX package using `RobustFileRepo`.
    - Publish the AAS package to the BaSyx repository and register its submodel descriptors on the BaSyx Registry.
    - Show success message and complete.
  - If `self.model_type == "GLB"`:
    - Run the existing conveyor kit deployment logic.

- [ ] **Step 2.3: Test PyQt6 code execution**
  Ensure tests compile and run properly.
  Run: `python "AAS Client/test_conveyor_wizard.py"`
  Add a mock unit test in `test_conveyor_wizard.py` verifying URDF loading (mock URDF/xacro files) and step skipping navigation.

- [ ] **Step 2.4: Commit AASX generation changes**
  ```bash
  git add "AAS Client/conveyor_wizard.py" "AAS Client/test_conveyor_wizard.py"
  git commit -m "feat: implement Robot AASX generation and package publishing for URDF models"
  ```

---

### Verification and Testing

1. Run `python "AAS Client/conveyor_wizard.py"`.
2. Click `"Select URDF / Xacro Folder"`, choose a robot folder (e.g. `robots_tested` or any robot directory), and verify the robot renders in the 3D visualizer.
3. Advance to Step 2, fill in name/ID, and verify clicking "Next" jumps directly to Step 3 (Review & Deploy).
4. Verify clicking "Deploy to AAS" packages and uploads a valid AAS containing `GeometryData`, `PositionData`, and `TelemetryData` to BaSyx.
