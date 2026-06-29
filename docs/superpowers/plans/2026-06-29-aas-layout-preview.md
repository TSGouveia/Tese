# AAS Layout Preview Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "Preview Deployed Layout" button to the Conveyor Wizard home page that fetches all active AAS from BaSyx and renders their 3D models concurrently in the viewport at their correct global transforms (with point labels).

---

### Task 1: Add layout preview button to ConveyorWizard start page

**Files:**
- Modify: `C:\Users\LazyT\Desktop\Tese\AAS Client\conveyor_wizard.py`

- [ ] **Step 1: Add btn_preview_layout to setup_steps**
  Modify the `setup_steps` method of ConveyorWizard (around lines 308-314) to define the new button and add it to the horizontal button layout `bl`.
  
  Replace:
  ```python
          self.btn_manage_aas = QPushButton("Manage Deployed AAS"); self.btn_manage_aas.setMinimumHeight(55); self.btn_manage_aas.setStyleSheet("background-color: #27ae60;")
          self.btn_manage_aas.clicked.connect(self.manage_deployed_aas)
          bl.addWidget(self.btn_select_glb); bl.addWidget(self.btn_manage_aas)
  ```
  with:
  ```python
          self.btn_manage_aas = QPushButton("Manage Deployed AAS"); self.btn_manage_aas.setMinimumHeight(55); self.btn_manage_aas.setStyleSheet("background-color: #27ae60;")
          self.btn_manage_aas.clicked.connect(self.manage_deployed_aas)
          self.btn_preview_layout = QPushButton("Preview Deployed Layout"); self.btn_preview_layout.setMinimumHeight(55); self.btn_preview_layout.setStyleSheet("background-color: #8e44ad;")
          self.btn_preview_layout.clicked.connect(self.preview_deployed_layout)
          bl.addWidget(self.btn_select_glb); bl.addWidget(self.btn_manage_aas); bl.addWidget(self.btn_preview_layout)
  ```

- [ ] **Step 2: Verify compilation**
  Run: `C:\Users\LazyT\Documents\PythonProjects\AAS_API_TESE\.venv\Scripts\python.exe -m py_compile "C:\Users\LazyT\Desktop\Tese\AAS Client\conveyor_wizard.py"`
  Expected: Successful exit code 0. (Will fail at runtime because `preview_deployed_layout` is not defined yet, which is expected before Task 2).

- [ ] **Step 3: Commit**
  Run:
  ```bash
  git add "AAS Client/conveyor_wizard.py"
  git commit -m "feat: add Preview Deployed Layout button to wizard start page"
  ```

---

### Task 2: Implement preview_deployed_layout method

**Files:**
- Modify: `C:\Users\LazyT\Desktop\Tese\AAS Client\conveyor_wizard.py`

- [ ] **Step 1: Write preview_deployed_layout implementation**
  Add the method to `ConveyorWizard`. Place it right below `manage_deployed_aas` (around line 490).
  
  Add the following code block:
  ```python
      def preview_deployed_layout(self):
          try:
              res = requests.get("http://localhost:8082/shell-descriptors", timeout=5)
              shells = res.json().get("result", [])
              if not shells:
                  QMessageBox.information(self, "Info", "No AAS found on server.")
                  return
          except Exception as e:
              QMessageBox.critical(self, "Error", f"Could not connect to registry: {e}")
              return

          QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
          self.plotter.clear()
          self.meshes = {}
          self.actors = {}
          self.node_tree.clear()
          self.glb_path = None
          self.lbl_glb_path.setText("No file selected (Layout Preview Mode)")

          import trimesh.transformations as tf
          loaded_count = 0

          try:
              for s in shells:
                  shell_id = s.get("id")
                  id_short = s.get("idShort", "AAS")
                  encoded_shell_id = base64.urlsafe_b64encode(shell_id.encode()).decode().rstrip("=")

                  # Fetch shell details
                  shell_res = requests.get(f"http://localhost:8081/shells/{encoded_shell_id}", timeout=5)
                  if shell_res.status_code != 200: continue
                  shell_data = shell_res.json()

                  # Fetch submodel refs
                  submodel_refs = shell_data.get("submodels", [])
                  vis_id = None
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
                  if not vis_data: continue

                  # Parse transform
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
                                  coll_id_short = el["idShort"]

                  if mesh_href and coll_id_short:
                      # Fetch mesh attachment
                      vis_id_node = vis_data.get("id")
                      encoded_vis_id = base64.urlsafe_b64encode(vis_id_node.encode()).decode().rstrip("=")
                      dl_url = f"http://localhost:8081/submodels/{encoded_vis_id}/submodel-elements/{coll_id_short}.Mesh/attachment"
                      m_res = requests.get(dl_url, timeout=5)
                      if m_res.status_code == 200:
                          import tempfile
                          tp = os.path.join(tempfile.gettempdir(), f"{id_short}_layout.glb")
                          with open(tp, "wb") as f: f.write(m_res.content)
                          
                          # Load and transform geometry
                          scene = trimesh.load(tp, process=False)
                          
                          # Build transformation matrix M = T * R * S
                          T = tf.translation_matrix(pos_val)
                          R = tf.euler_matrix(np.radians(rot_val[0]), np.radians(rot_val[1]), np.radians(rot_val[2]), 'sxyz')
                          S = tf.scale_matrix(scale_val)
                          M = tf.concatenate_matrices(T, R, S)
                          
                          scene.apply_transform(M)
                          
                          # Add meshes to main viewport
                          centers = []
                          if isinstance(scene, trimesh.Scene):
                              for gn, mesh in scene.geometry.items():
                                  tx = None; cl = None; mt = 0.0; rg = 0.5
                                  if hasattr(mesh, 'visual') and hasattr(mesh.visual, 'material'):
                                      mat = mesh.visual.material; img = getattr(mat, 'image', getattr(mat, 'baseColorTexture', None))
                                      if img:
                                          try: tx = pv.Texture(np.array(img))
                                          except: pass
                                      if hasattr(mat, 'main_color') or hasattr(mat, 'baseColorFactor'):
                                          c = getattr(mat, 'main_color', getattr(mat, 'baseColorFactor', None))
                                          if c is not None: cl = [x/255.0 for x in c[:3]] if max(c) > 1.0 else c[:3]
                                      mt = getattr(mat, 'metallicFactor', 0.0)
                                      rg = getattr(mat, 'roughnessFactor', 0.5)
                                  pv_mesh = pv.wrap(mesh)
                                  self.plotter.add_mesh(pv_mesh, texture=tx, color=cl, metallic=mt, roughness=rg)
                                  centers.append(mesh.bounds)
                          elif isinstance(scene, trimesh.Trimesh):
                              pv_mesh = pv.wrap(scene)
                              self.plotter.add_mesh(pv_mesh)
                              centers.append(scene.bounds)
                          
                          # Add point label at center
                          if centers:
                              b = np.array(centers)
                              min_b = np.min(b[:, [0, 2, 4]], axis=0); max_b = np.max(b[:, [1, 3, 5]], axis=0)
                              pos = (min_b + max_b) / 2.0
                              # Float slightly above the conveyor model
                              pos[1] += (max_b[1] - min_b[1]) * 0.5 + 0.5
                              self.plotter.add_point_labels([pos], [id_short], font_size=16, text_color="white", shape_color="#8e44ad", show_points=False)
                          
                          loaded_count += 1

              self.plotter.reset_camera()
              self.plotter.camera.up = (0, 1, 0)
              while QApplication.overrideCursor() is not None:
                  QApplication.restoreOverrideCursor()
              QMessageBox.information(self, "Success", f"Factory layout loaded! Rendered {loaded_count} active AAS kits.")
          except Exception as ex:
              while QApplication.overrideCursor() is not None:
                  QApplication.restoreOverrideCursor()
              traceback.print_exc()
              QMessageBox.critical(self, "Error", f"Failed to load factory layout: {ex}")
          finally:
              while QApplication.overrideCursor() is not None:
                  QApplication.restoreOverrideCursor()
  ```

- [ ] **Step 2: Verify compilation**
  Run: `C:\Users\LazyT\Documents\PythonProjects\AAS_API_TESE\.venv\Scripts\python.exe -m py_compile "C:\Users\LazyT\Desktop\Tese\AAS Client\conveyor_wizard.py"`
  Expected: Successful exit code 0.

- [ ] **Step 3: Commit and Push**
  Run:
  ```bash
  git add "AAS Client/conveyor_wizard.py"
  git commit -m "feat: implement preview_deployed_layout method"
  git push origin main
  ```
