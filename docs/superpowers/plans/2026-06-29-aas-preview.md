# Implementation Plan: AAS 3D Preview Panel

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a 3D Preview panel to the right side of the "Manage Deployed AAS" dialog that dynamically loads and displays the GLB mesh of the selected AAS.

**Architecture:**
- Adjust the layout of the `manage_deployed_aas` dialog to be side-by-side using `QSplitter`.
- Left side: AAS list and control buttons.
- Right side: A `QGroupBox` containing a `BackgroundPlotter` instance (`preview_plotter`) dedicated to displaying the 3D preview.
- Connect `list_widget.currentItemChanged` to fetch the visual structure submodel and GLB attachment from BaSyx, save it to a temp file, and render it in the preview plotter.
- Ensure proper cleanup of `preview_plotter` when the dialog is closed.

---

### Task 1: Implement load_model_into_plotter Helper

**Files:**
- Modify: `C:\Users\LazyT\Desktop\Tese\AAS Client\conveyor_wizard.py`

- [ ] **Step 1: Write helper function**
  Add a self-contained helper function to load a 3D model path into a specific PyVista plotter instance. Place it below the other helpers.
  
  Add the following code block:
  ```python
  def load_model_into_plotter(plotter, path):
      plotter.clear()
      try:
          scene = trimesh.load(path, process=False)
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
                  plotter.add_mesh(pv_mesh, texture=tx, color=cl, metallic=mt, roughness=rg)
          elif isinstance(scene, trimesh.Trimesh):
              pv_mesh = pv.wrap(scene)
              plotter.add_mesh(pv_mesh)
          plotter.reset_camera()
          plotter.camera.up = (0, 1, 0)
      except Exception as e:
          traceback.print_exc()
  ```

- [ ] **Step 2: Verify compilation**
  Run: `C:\Users\LazyT\Documents\PythonProjects\AAS_API_TESE\.venv\Scripts\python.exe -m py_compile "C:\Users\LazyT\Desktop\Tese\AAS Client\conveyor_wizard.py"`
  Expected: Successful exit code 0.

---

### Task 2: Refactor manage_deployed_aas UI and Add 3D Preview Plotter

**Files:**
- Modify: `C:\Users\LazyT\Desktop\Tese\AAS Client\conveyor_wizard.py`

- [ ] **Step 1: Expand dialog dimensions and insert splitter**
  Modify `manage_deployed_aas` (around lines 340-365) to layout list widgets and the preview panel side-by-side.
  
  Replace dialog initialization block with:
  ```python
          dlg = QDialog(self)
          dlg.setWindowTitle("Manage Deployed AAS")
          dlg.resize(1000, 500)
          main_h_layout = QHBoxLayout(dlg)

          # Left Panel (List + Buttons)
          left_panel = QWidget()
          left_layout = QVBoxLayout(left_panel)
          left_layout.setContentsMargins(0, 0, 0, 0)
          
          left_layout.addWidget(QLabel("Select a Deployed AAS to Clone, Backup or Delete:"))
          list_widget = QListWidget()
          left_layout.addWidget(list_widget)
  ```

- [ ] **Step 2: Add Preview QGroupBox and BackgroundPlotter**
  Add the right panel structure and instantiate the `preview_plotter`:
  ```python
          # Right Panel (3D Preview)
          right_panel = QGroupBox("3D Model Preview")
          right_layout = QVBoxLayout(right_panel)
          right_layout.setContentsMargins(5, 10, 5, 5)
          
          preview_plotter = BackgroundPlotter(show=False)
          preview_plotter.set_background("#161616")
          right_layout.addWidget(preview_plotter.interactor)
          
          # Add splitter
          splitter = QSplitter(Qt.Orientation.Horizontal)
          splitter.addWidget(left_panel)
          splitter.addWidget(right_panel)
          splitter.setStretchFactor(0, 3)
          splitter.setStretchFactor(1, 2)
          main_h_layout.addWidget(splitter)
  ```

- [ ] **Step 3: Connect close event cleanup**
  Ensure the dialog `finished` signal cleans up `preview_plotter` to avoid memory leak:
  ```python
          def cleanup_plotter():
              try: preview_plotter.close()
              except: pass
          dlg.finished.connect(lambda r: cleanup_plotter())
  ```

- [ ] **Step 4: Verify compilation**
  Run: `C:\Users\LazyT\Documents\PythonProjects\AAS_API_TESE\.venv\Scripts\python.exe -m py_compile "C:\Users\LazyT\Desktop\Tese\AAS Client\conveyor_wizard.py"`
  Expected: Successful exit code 0.

---

### Task 3: Implement Dynamic Selection Change Preview

**Files:**
- Modify: `C:\Users\LazyT\Desktop\Tese\AAS Client\conveyor_wizard.py`

- [ ] **Step 1: Write on_selection_changed connection**
  Write selection changed callback inside `manage_deployed_aas` that downloads and displays the GLB of the chosen AAS:
  ```python
          def on_selection_changed():
              item = list_widget.currentItem()
              if not item:
                  preview_plotter.clear()
                  return
              shell_desc = item.data(Qt.ItemDataRole.UserRole)
              shell_id = shell_desc.get("id")
              
              QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
              try:
                  encoded_shell_id = base64.urlsafe_b64encode(shell_id.encode()).decode().rstrip("=")
                  shell_res = requests.get(f"http://localhost:8081/shells/{encoded_shell_id}", timeout=2)
                  if shell_res.status_code != 200:
                      preview_plotter.clear()
                      return
                  
                  shell_data = shell_res.json()
                  submodel_refs = shell_data.get("submodels", [])
                  
                  vis_id = None
                  for ref in submodel_refs:
                      keys = ref.get("keys", [])
                      if keys and ("VisualStructure" in keys[0].get("value", "") or "Visual" in keys[0].get("value", "")):
                          vis_id = keys[0].get("value")
                          break
                  
                  if not vis_id:
                      preview_plotter.clear()
                      return
                  
                  encoded_vis_id = base64.urlsafe_b64encode(vis_id.encode()).decode().rstrip("=")
                  vis_res = requests.get(f"http://localhost:8081/submodels/{encoded_vis_id}", timeout=2)
                  if vis_res.status_code != 200:
                      preview_plotter.clear()
                      return
                  
                  vis_data = vis_res.json()
                  mesh_href = None
                  coll_id_short = None
                  for el in vis_data.get("submodelElements", []):
                      if el["modelType"] == "SubmodelElementCollection": 
                          for sel in el.get("value", []):
                              if sel["idShort"] == "Mesh" and sel["modelType"] == "File":
                                  mesh_href = sel.get("value")
                                  coll_id_short = el["idShort"]
                                  break
                  
                  if mesh_href and coll_id_short:
                      dl_url = f"http://localhost:8081/submodels/{encoded_vis_id}/submodel-elements/{coll_id_short}.Mesh/attachment"
                      m_res = requests.get(dl_url, timeout=3)
                      if m_res.status_code == 200:
                          import tempfile
                          tp = os.path.join(tempfile.gettempdir(), f"{shell_desc['idShort']}_preview.glb")
                          with open(tp, "wb") as f:
                              f.write(m_res.content)
                          load_model_into_plotter(preview_plotter, tp)
                          return
                  
                  preview_plotter.clear()
              except Exception as e:
                  traceback.print_exc()
                  preview_plotter.clear()
              finally:
                  while QApplication.overrideCursor() is not None:
                      QApplication.restoreOverrideCursor()

          list_widget.currentItemChanged.connect(on_selection_changed)
  ```

- [ ] **Step 2: Verify compilation**
  Run: `C:\Users\LazyT\Documents\PythonProjects\AAS_API_TESE\.venv\Scripts\python.exe -m py_compile "C:\Users\LazyT\Desktop\Tese\AAS Client\conveyor_wizard.py"`
  Expected: Successful exit code 0.

- [ ] **Step 3: Commit and Push**
  Run:
  ```bash
  git add "AAS Client/conveyor_wizard.py"
  git commit -m "feat: implement 3D preview panel in manage deployed AAS dialog"
  git push origin main
  ```
