# Cross-AAS Rules & Standalone Rules Editor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement standalone control rules programming (independent of GLB files) for logical orchestrator shells, enable cross-AAS conditions/actions in PyQt6, and update the Unity driver/engine to resolve remote kits.

**Architecture:**
1. **PyQt6 Editor**: Add a button on Page 1 to launch a dialog that retrieves active shells, compiles a list of all sensors/actuators on the network, edits the rules using the 3-panel editor, and writes directly back to BaSyx.
2. **Unity Driver & Engine**: Update `IAASDriver` signatures to accept `kitId`. Implement local lookup (finding the GameObject for `kitId`) and BaSyx API lookup in `AASHttpDriver`.
3. **Unity BaSyxManager**: Support logical-only orchestrator shells (no GLB) by instantiating empty manager GameObjects and attaching `AASRuleEngine` to them.

**Tech Stack:** PyQt6, Unity C#, Newtonsoft.Json.

---

### Task 1: Refactor PyQt6 Wizard Logic to Support Cross-AAS Dropdowns & Standalone Editor Dialog

**Files:**
- Modify: `AAS Client/conveyor_wizard.py`

- [ ] **Step 1.1: Support `"kit"` key in wizard's Step 5 serialization**
  Update the step and trigger serialization code in `ConveyorWizard` so that every trigger condition and action step JSON includes the target `"kit"` (e.g. `self.edit_kit_name.text()` as default).
  Ensure step dropdown entries on Step 5 are populated as `[KitName] - [PinID]` when editing.

- [ ] **Step 1.2: Implement `AASRulesEditorDialog` Class**
  Create a new PyQt6 `QDialog` class in `conveyor_wizard.py` called `AASRulesEditorDialog`.
  This dialog will:
  - Fetch all active shells from the BaSyx Registry (`http://localhost:8082/shell-descriptors`).
  - Present a combobox to select the target shell to program rules for.
  - Fetch all sensor (Outputs) and actuator (Inputs) definitions from all active shells (by querying their `BehaviorMapping` submodel from `http://localhost:8081`).
  - Render the identical 3-panel rule editor (Sequences list, Trigger conditions editor, Steps editor with bottom edit pane).
  - Load existing rules from the `ControlLogic` submodel of the chosen shell if it exists.
  - Expose a "Save & Deploy" button that serializes the logic rules and executes an HTTP `PUT` request to update the `Rules` property in the `ControlLogic` submodel on the BaSyx repository.

- [ ] **Step 1.3: Add Button on Main Screen Page 1**
  Add a new button `"Program Deployed AAS Rules"` to `self.page1` layout:
  ```python
  self.btn_program_rules = QPushButton("Program Deployed AAS Rules")
  self.btn_program_rules.setMinimumHeight(55)
  self.btn_program_rules.setStyleSheet("background-color: #d35400; color: white; font-weight: bold;")
  self.btn_program_rules.clicked.connect(self.open_program_rules_dialog)
  ```
  Implement the `open_program_rules_dialog` method to instantiate and show `AASRulesEditorDialog` modally.

- [ ] **Step 1.4: Verify PyQt6 code executes cleanly**
  Run tests: `python -m unittest "AAS Client/test_conveyor_wizard.py"`
  Confirm no errors and commit.

- [ ] **Step 1.5: Commit changes**
  ```bash
  git add "AAS Client/conveyor_wizard.py"
  git commit -m "feat: add standalone AAS rules programmer dialog and cross-AAS kit support"
  ```

---

### Task 2: Update Unity Driver and Rule Engine for Cross-AAS Resolution

**Files:**
- Modify: `DT Unity/Assets/Scripts/AAS/IAASDriver.cs`
- Modify: `DT Unity/Assets/Scripts/AAS/AASRuleEngine.cs`

- [ ] **Step 2.1: Update `IAASDriver` interface signature**
  Modify interface in `IAASDriver.cs`:
  ```csharp
  public interface IAASDriver
  {
      void WriteActuator(string kitId, string pinId, bool value);
      bool ReadSensor(string kitId, string pinId);
  }
  ```

- [ ] **Step 2.2: Implement Kit Resolution in `AASHttpDriver`**
  Modify `AASHttpDriver.cs`:
  - `ReadSensor(kitId, pinId)`: Search the scene for the GameObject named `kitId` (or matching it). If found, fetch its `SensorPhysicsProxy` objects locally to read the state of `pinId`. If not found (or offline), query BaSyx via HTTP GET from the submodel `https://acplt.org/Submodels/Pins_{kitId}` (or the cached submodel id from `BaSyxManager`).
  - `WriteActuator(kitId, pinId, value)`: Search the scene for the GameObject named `kitId`. If found, set the actuator's `currentState` in its `AASActuatorController` component. Perform an HTTP `PUT` request to BaSyx to update `Inputs.pinId` for the target `kitId` shell:
    `url = $"{baseRepoUrl}/submodels/{Base64Url("https://acplt.org/Submodels/Pins_" + kitId)}/submodel-elements/Inputs.{pinId}"`

- [ ] **Step 2.3: Modify `AASRuleEngine.cs` to pass kit parameter**
  Update `AASRuleEngine.cs` where trigger conditions and steps are evaluated:
  - Retrieve the `"kit"` key from the JSON condition/step objects (e.g. `string targetKit = cond["kit"]?.ToString();`). If null, default to the local kit name.
  - Pass `targetKit` to `driver.ReadSensor(targetKit, sensor)` and `driver.WriteActuator(targetKit, actuator, value)`.

- [ ] **Step 2.4: Commit C# updates**
  ```bash
  git add "DT Unity/Assets/Scripts/AAS/IAASDriver.cs" "DT Unity/Assets/Scripts/AAS/AASRuleEngine.cs"
  git commit -m "feat: update Unity rule engine and driver to support cross-AAS kit parameters"
  ```

---

### Task 3: Support Logical-Only AAS (No GLB) in BaSyxManager

**Files:**
- Modify: `DT Unity/Assets/Scripts/BaSyxManager.cs`

- [ ] **Step 3.1: Expose Kit Submodel Lookups**
  Add a mapping or lookup method in `BaSyxManager` to query the registered virtual pins submodel ID of a kit:
  `public string GetVirtualPinsSubmodelId(string kitIdShort)`
  Let `AASHttpDriver` query this mapping to resolve accurate remote URLs if needed.

- [ ] **Step 3.2: Instantiate Purely Logical AAS Shells**
  Modify `SyncRobotsRoutine` in `BaSyxManager.cs`:
  If a discovered AAS shell descriptor has `ControlLogic` but does **not** have `VisualStructure` (no GLB), it is a logical orchestrator:
  - Instantiate a dummy GameObject: `GameObject logicalGo = new GameObject("LogicalAAS_" + shell.idShort);`
  - Attach `AASRuleEngine` and `AASHttpDriver` components to it.
  - Call `engine.Init` passing the repository URL, `ControlLogic` submodel ID, and the driver instance (passing null for sensor/actuator controllers since it has no local body).

- [ ] **Step 3.3: Commit BaSyxManager updates**
  ```bash
  git add "DT Unity/Assets/Scripts/BaSyxManager.cs"
  git commit -m "feat: add support for logical-only (no GLB) orchestrator shells in BaSyxManager"
  ```

---

### Verification and Testing

1. Run `python "AAS Client/conveyor_wizard.py"`.
2. Click `"Program Deployed AAS Rules"`, select an active shell, define logical rules targeting other shells (e.g., when sensor on kit A is true, turn motor on kit B to true), and hit save.
3. Start Unity, play the scene, and verify that the empty logical shell GameObject is instantiated, parses rules, and controls other active 3D kits across the scene.
