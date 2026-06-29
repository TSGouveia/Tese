# AAS Backup & Restore Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Backup (Download) and Restore (Upload) actions to the manage AAS dialog in Conveyor Wizard, allowing serialization of entire AAS configurations + GLB meshes into a consolidated JSON backup, and importing them back.

**Architecture:** We will implement state serialization helpers in `ConveyorWizard` to save and restore UI configuration states. The backup action will download the shell, submodels, and the GLB attachment, base64-encoding the GLB file. The restore action will read the JSON, recreate the GLB locally, and offer the user to either load it in the editor or deploy directly to the BaSyx servers.

**Tech Stack:** Python, PyQt6, base64, requests

---

### Task 1: Implement State Serialization Helper Functions

**Files:**
- Modify: `C:\Users\LazyT\Desktop\Tese\AAS Client\conveyor_wizard.py`

- [ ] **Step 1: Implement save_wizard_state and restore_wizard_state**
  Add helper functions to ConveyorWizard to serialize and deserialize UI state. Place them below `manage_deployed_aas` and `load_cloned_aas`.
  
  Add the following code block:
  ```python
      def save_wizard_state(self):
          return {
              "kit_name": self.edit_kit_name.text(),
              "aas_id": self.edit_aas_id.text(),
              "description": self.edit_desc.text(),
              "glb_path": self.glb_path,
              "pos": [self.sys_pos[i].value() for i in range(3)],
              "rot": [self.sys_rot[i].value() for i in range(3)],
              "scale": [self.sys_scale[i].value() for i in range(3)],
              "actuators": [w.get_data() for w in self.actuator_widgets],
              "sensors": [w.get_data() for w in self.sensor_widgets]
          }

      def restore_wizard_state(self, state):
          self.glb_path = state.get("glb_path")
          self.lbl_glb_path.setText(os.path.basename(self.glb_path) if self.glb_path else "No file selected")
          if self.glb_path and os.path.exists(self.glb_path):
              self.load_model(self.glb_path)
          self.edit_kit_name.setText(state.get("kit_name", ""))
          self.edit_aas_id.setText(state.get("aas_id", ""))
          self.edit_desc.setText(state.get("description", ""))
          pos = state.get("pos", [0, 0, 0])
          rot = state.get("rot", [0, 0, 0])
          scale = state.get("scale", [1, 1, 1])
          for i in range(3):
              self.sys_pos[i].setValue(pos[i])
              self.sys_rot[i].setValue(rot[i])
              self.sys_scale[i].setValue(scale[i])
              
          for w in list(self.actuator_widgets): self.remove_actuator(w)
          for w in list(self.sensor_widgets): self.remove_sensor(w)
          
          for act in state.get("actuators", []):
              self.add_actuator(); w = self.actuator_widgets[-1]
              w.edit_pin.setText(act.get("pin_id", ""))
              w.edit_node.setText(act.get("node", ""))
              w.combo_behavior.setCurrentText(act.get("behavior", ""))
              axis = act.get("axis", [0, 0, 0])
              w.spin_x.setValue(axis[0])
              w.spin_y.setValue(axis[1])
              w.spin_z.setValue(axis[2])
              w.spin_speed.setValue(act.get("speed", 1.0))
              w.check_visible.setChecked(act.get("visible", True))
              if "stop_sensor" in act: w.combo_stop_sens.setCurrentText(act["stop_sensor"])
              
          for sns in state.get("sensors", []):
              self.add_sensor(); w = self.sensor_widgets[-1]
              w.edit_pin.setText(sns.get("pin_id", ""))
              w.edit_node.setText(sns.get("node", ""))
              w.combo_behavior.setCurrentText(sns.get("behavior", ""))
              w.edit_filter.setText(sns.get("target_filter", "Metal"))
              w.check_visible.setChecked(sns.get("visible", False))
              w.check_active_low.setChecked(sns.get("active_low", False))
          self.update_all_actuator_dropdowns()
  ```

- [ ] **Step 2: Verify compilation**
  Run: `C:\Users\LazyT\Documents\PythonProjects\AAS_API_TESE\.venv\Scripts\python.exe -m py_compile "C:\Users\LazyT\Desktop\Tese\AAS Client\conveyor_wizard.py"`
  Expected: Successful exit code 0.

- [ ] **Step 3: Commit**
  Run:
  ```bash
  git add "AAS Client/conveyor_wizard.py"
  git commit -m "feat: implement save_wizard_state and restore_wizard_state helpers"
  ```

---

### Task 2: Add Backup and Restore Buttons to Manage AAS UI

**Files:**
- Modify: `C:\Users\LazyT\Desktop\Tese\AAS Client\conveyor_wizard.py` (Inside `manage_deployed_aas` method)

- [ ] **Step 1: Add Backup and Restore buttons to dialog**
  Modify button layout definition in `manage_deployed_aas` (around lines 380-395).
  
  Replace:
  ```python
          btn_layout = QHBoxLayout()
          btn_clone = QPushButton("Clone & Edit")
          btn_clone.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; min-height: 35px;")
          
          btn_delete = QPushButton("Delete AAS")
          btn_delete.setStyleSheet("background-color: #c0392b; color: white; font-weight: bold; min-height: 35px;")
          
          btn_close = QPushButton("Close")
          btn_close.setStyleSheet("min-height: 35px;")

          btn_layout.addWidget(btn_clone)
          btn_layout.addWidget(btn_delete)
          btn_layout.addWidget(btn_close)
          layout.addLayout(btn_layout)
  ```
  with:
  ```python
          btn_layout = QHBoxLayout()
          btn_clone = QPushButton("Clone & Edit")
          btn_clone.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; min-height: 35px;")
          
          btn_backup = QPushButton("Backup (Download)")
          btn_backup.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold; min-height: 35px;")
          
          btn_restore = QPushButton("Restore (Upload)")
          btn_restore.setStyleSheet("background-color: #16a085; color: white; font-weight: bold; min-height: 35px;")
          
          btn_delete = QPushButton("Delete AAS")
          btn_delete.setStyleSheet("background-color: #c0392b; color: white; font-weight: bold; min-height: 35px;")
          
          btn_close = QPushButton("Close")
          btn_close.setStyleSheet("min-height: 35px;")

          btn_layout.addWidget(btn_clone)
          btn_layout.addWidget(btn_backup)
          btn_layout.addWidget(btn_restore)
          btn_layout.addWidget(btn_delete)
          btn_layout.addWidget(btn_close)
          layout.addLayout(btn_layout)
  ```

- [ ] **Step 2: Connect stub actions to buttons**
  Add mock connects before the `dlg.exec()` call:
  ```python
          btn_backup.clicked.connect(lambda: QMessageBox.information(dlg, "Stub", "Backup clicked"))
          btn_restore.clicked.connect(lambda: QMessageBox.information(dlg, "Stub", "Restore clicked"))
  ```

- [ ] **Step 3: Verify compilation**
  Run: `C:\Users\LazyT\Documents\PythonProjects\AAS_API_TESE\.venv\Scripts\python.exe -m py_compile "C:\Users\LazyT\Desktop\Tese\AAS Client\conveyor_wizard.py"`
  Expected: Successful exit code 0.

- [ ] **Step 4: Commit**
  Run:
  ```bash
  git add "AAS Client/conveyor_wizard.py"
  git commit -m "feat: add Backup and Restore buttons to Manage AAS dialog"
  ```

---

### Task 3: Implement Backup/Download Logic

**Files:**
- Modify: `C:\Users\LazyT\Desktop\Tese\AAS Client\conveyor_wizard.py`

- [ ] **Step 1: Write on_backup_clicked implementation**
  Add the backup logic inside `manage_deployed_aas` that gathers remote configuration and visual structure mesh and writes to JSON.
  
  Define `on_backup_clicked` inside `manage_deployed_aas` before `btn_backup.clicked.connect`:
  ```python
          def on_backup_clicked():
              item = list_widget.currentItem()
              if not item:
                  QMessageBox.warning(dlg, "Warning", "Please select an AAS to backup.")
                  return
              shell_desc = item.data(Qt.ItemDataRole.UserRole)
              id_short = shell_desc.get("idShort", "Unknown")
              shell_id = shell_desc.get("id")

              QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
              try:
                  encoded_shell_id = base64.urlsafe_b64encode(shell_id.encode()).decode().rstrip("=")
                  
                  # Fetch shell to get submodels
                  shell_res = requests.get(f"http://localhost:8081/shells/{encoded_shell_id}", timeout=5)
                  if shell_res.status_code != 200:
                      raise Exception(f"Failed to fetch Shell (Code {shell_res.status_code})")
                  shell_data = shell_res.json()
                  
                  submodel_refs = shell_data.get("submodels", [])
                  submodels_data = {}
                  for ref in submodel_refs:
                      keys = ref.get("keys", [])
                      if keys:
                          sm_id = keys[0].get("value")
                          encoded_sm_id = base64.urlsafe_b64encode(sm_id.encode()).decode().rstrip("=")
                          sm_res = requests.get(f"http://localhost:8081/submodels/{encoded_sm_id}", timeout=5)
                          if sm_res.status_code == 200:
                              sm_data = sm_res.json()
                              submodels_data[sm_data.get("idShort", "")] = sm_data

                  vis_data = next((v for k,v in submodels_data.items() if "VisualStructure" in k or "Visual" in k), None)
                  beh_data = next((v for k,v in submodels_data.items() if "BehaviorMapping" in k or "Behavior" in k), None)
                  
                  if not all([vis_data, beh_data]):
                      raise Exception("AAS is missing required submodels.")

                  # Gather config parameters (equivalent to clone parsing)
                  kit_name = shell_desc.get("idShort", "ClonedKit")
                  description = ""
                  if "KitConfiguration" in submodels_data:
                      cfg = submodels_data["KitConfiguration"]
                      for el in cfg.get("submodelElements", []):
                          if el["idShort"] == "Description":
                              description = el.get("value", "")

                  pos_val = [0.0]*3; rot_val = [0.0]*3; scale_val = [1.0]*3
                  mesh_href = None
                  for el in vis_data.get("submodelElements", []):
                      if el["modelType"] == "SubmodelElementCollection": 
                          for sel in el.get("value", []):
                              if sel["idShort"] == "Transform":
                                  for t in sel.get("value", []):
                                      v = float(t.get("value", 0))
                                      if t["idShort"] == "PosX": pos_val[0] = v
                                      elif t["idShort"] == "PosY": pos_val[1] = v
                                      elif t["idShort"] == "PosZ": pos_val[2] = v
                                      elif t["idShort"] == "RotX": rot_val[0] = v
                                      elif t["idShort"] == "RotY": rot_val[1] = v
                                      elif t["idShort"] == "RotZ": rot_val[2] = v
                                      elif t["idShort"] == "ScaleX": scale_val[0] = v
                                      elif t["idShort"] == "ScaleY": scale_val[1] = v
                                      elif t["idShort"] == "ScaleZ": scale_val[2] = v
                              elif sel["idShort"] == "Mesh" and sel["modelType"] == "File":
                                  mesh_href = sel.get("value")

                  actuators = []
                  sensors = []
                  act_types = ["Conveyor", "RotateContinuous", "TranslateContinuous", "Piston", "Linear"]
                  sens_types = ["TriggerZone", "Presence", "Proximity"]
                  
                  for el in beh_data.get("submodelElements", []):
                      if el["modelType"] == "SubmodelElementCollection":
                          props = {p["idShort"]: p.get("value") for p in el.get("value", []) if p["modelType"] == "Property"}
                          params = {}
                          for p in el.get("value", []):
                              if p["idShort"] == "Parameters":
                                  params = {pp["idShort"]: pp.get("value") for pp in p.get("value", []) if pp["modelType"] == "Property"}
                                  
                          b_type = props.get("Type", ""); pin_id = props.get("PinID", ""); node = props.get("Component", "")
                          
                          if b_type in act_types:
                              act_data = {
                                  "pin_id": pin_id, "node": node, "behavior": b_type,
                                  "axis": [float(params.get("AxisX", 0)), float(params.get("AxisY", 0)), float(params.get("AxisZ", 0))],
                                  "speed": float(params.get("Speed", 1.0)),
                                  "visible": str(params.get("Visible", "True")).lower() == "true"
                              }
                              if "StopSensorComponent" in params:
                                  act_data["stop_sensor"] = params["StopSensorComponent"]
                              actuators.append(act_data)
                          elif b_type in sens_types:
                              sens_data = {
                                  "pin_id": pin_id, "node": node, "behavior": b_type,
                                  "target_filter": params.get("TargetFilter", "Metal"),
                                  "visible": str(params.get("Visible", "False")).lower() == "true",
                                  "active_low": str(params.get("ActiveLow", "False")).lower() == "true"
                              }
                              sensors.append(sens_data)

                  # Get GLB attachment
                  glb_bytes = b""
                  if mesh_href:
                      vis_id = vis_data.get("id")
                      encoded_vis_id = base64.urlsafe_b64encode(vis_id.encode()).decode().rstrip("=")
                      coll_id_short = None
                      for el in vis_data.get("submodelElements", []):
                          if el["modelType"] == "SubmodelElementCollection": 
                              for sel in el.get("value", []):
                                  if sel["idShort"] == "Mesh":
                                      coll_id_short = el["idShort"]
                                      break
                      if coll_id_short:
                          dl_url = f"http://localhost:8081/submodels/{encoded_vis_id}/submodel-elements/{coll_id_short}.Mesh/attachment"
                          m_res = requests.get(dl_url, timeout=5)
                          if m_res.status_code == 200:
                              glb_bytes = m_res.content

                  # Assemble backup structure
                  backup_data = {
                      "version": "1.0",
                      "kit_name": kit_name,
                      "aas_id": shell_desc.get("id", f"https://acplt.org/AAS_{kit_name}"),
                      "description": description,
                      "config_data": {
                          "kit_name": kit_name,
                          "aas_id": kit_name,
                          "description": description,
                          "pos": pos_val,
                          "rot": rot_val,
                          "scale": scale_val,
                          "actuators": actuators,
                          "sensors": sensors
                      },
                      "glb_filename": f"{kit_name}.glb",
                      "glb_base64": base64.b64encode(glb_bytes).decode('utf-8')
                  }

                  # Restore override cursor before QFileDialog blocks the thread
                  while QApplication.overrideCursor() is not None:
                      QApplication.restoreOverrideCursor()

                  save_path, _ = QFileDialog.getSaveFileName(dlg, "Save AAS Backup", f"{kit_name}_backup.json", "JSON Files (*.json)")
                  if save_path:
                      with open(save_path, "w", encoding="utf-8") as f:
                          json.dump(backup_data, f, indent=2)
                      QMessageBox.information(dlg, "Success", "Backup saved successfully!")
              except Exception as e:
                  while QApplication.overrideCursor() is not None:
                      QApplication.restoreOverrideCursor()
                  traceback.print_exc()
                  QMessageBox.critical(dlg, "Error", f"Failed to backup AAS: {e}")
              finally:
                  while QApplication.overrideCursor() is not None:
                      QApplication.restoreOverrideCursor()
  ```

- [ ] **Step 2: Connect Backup button to action**
  Replace the stub connection with `btn_backup.clicked.connect(on_backup_clicked)`.

- [ ] **Step 3: Verify compilation**
  Run: `C:\Users\LazyT\Documents\PythonProjects\AAS_API_TESE\.venv\Scripts\python.exe -m py_compile "C:\Users\LazyT\Desktop\Tese\AAS Client\conveyor_wizard.py"`
  Expected: Successful exit code 0.

- [ ] **Step 4: Commit**
  Run:
  ```bash
  git add "AAS Client/conveyor_wizard.py"
  git commit -m "feat: implement AAS backup/download logic"
  ```

---

### Task 4: Implement Restore/Upload Logic

**Files:**
- Modify: `C:\Users\LazyT\Desktop\Tese\AAS Client\conveyor_wizard.py`

- [ ] **Step 1: Write on_restore_clicked implementation**
  Add the restore logic that decodes backup data and offers to either edit or deploy directly.
  
  Define `on_restore_clicked` inside `manage_deployed_aas` before `btn_restore.clicked.connect`:
  ```python
          def on_restore_clicked():
              open_path, _ = QFileDialog.getOpenFileName(dlg, "Open AAS Backup", "", "JSON Files (*.json)")
              if not open_path:
                  return

              try:
                  with open(open_path, "r", encoding="utf-8") as f:
                      backup_data = json.load(f)
              except Exception as e:
                  QMessageBox.critical(dlg, "Error", f"Failed to parse backup file: {e}")
                  return

              config_data = backup_data.get("config_data")
              glb_base64 = backup_data.get("glb_base64", "")
              if not config_data:
                  QMessageBox.critical(dlg, "Error", "Invalid backup file: config_data missing.")
                  return

              # Decode GLB to temp file
              try:
                  glb_bytes = base64.b64decode(glb_base64.encode('utf-8'))
                  import tempfile
                  tp = os.path.join(tempfile.gettempdir(), backup_data.get("glb_filename", "restored.glb"))
                  with open(tp, "wb") as f:
                      f.write(glb_bytes)
                  config_data["glb_path"] = tp
              except Exception as e:
                  QMessageBox.critical(dlg, "Error", f"Failed to decode GLB mesh: {e}")
                  return

              # Ask user what they want to do
              reply = QMessageBox.question(
                  dlg, "Restore Options",
                  "Would you like to load this backup into the Wizard for editing (Yes) or deploy it directly to the server (No)?",
                  QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
              )
              if reply == QMessageBox.StandardButton.Cancel:
                  return

              if reply == QMessageBox.StandardButton.Yes:
                  # Option A: Load into Wizard
                  self.restore_wizard_state(config_data)
                  dlg.accept()
                  QMessageBox.information(self, "Success", "Backup loaded into Wizard successfully.")
              else:
                  # Option B: Deploy directly
                  QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                  try:
                      # Save current state
                      curr_state = self.save_wizard_state()
                      # Load state temporarily
                      self.restore_wizard_state(config_data)
                      # Trigger deploy
                      self.deploy_to_aas()
                      # Restore old state
                      self.restore_wizard_state(curr_state)
                      
                      while QApplication.overrideCursor() is not None:
                          QApplication.restoreOverrideCursor()
                      QMessageBox.information(dlg, "Success", "AAS restored directly to BaSyx successfully.")
                      refresh_list()
                  except Exception as ex:
                      while QApplication.overrideCursor() is not None:
                          QApplication.restoreOverrideCursor()
                      QMessageBox.critical(dlg, "Error", f"Direct deployment failed: {ex}")
                  finally:
                      while QApplication.overrideCursor() is not None:
                          QApplication.restoreOverrideCursor()
  ```

- [ ] **Step 2: Connect Restore button to action**
  Replace the stub connection with `btn_restore.clicked.connect(on_restore_clicked)`.

- [ ] **Step 3: Verify compilation**
  Run: `C:\Users\LazyT\Documents\PythonProjects\AAS_API_TESE\.venv\Scripts\python.exe -m py_compile "C:\Users\LazyT\Desktop\Tese\AAS Client\conveyor_wizard.py"`
  Expected: Successful exit code 0.

- [ ] **Step 4: Commit**
  Run:
  ```bash
  git add "AAS Client/conveyor_wizard.py"
  git commit -m "feat: implement AAS restore/upload logic"
  ```
