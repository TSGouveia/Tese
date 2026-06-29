# Manage Deployed AAS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the "Clone Existing AAS" button in the Conveyor Wizard with a "Manage Deployed AAS" dialog that allows users to clone/load or delete deployed AAS from the server.

**Architecture:** We will modify the PyQt GUI layout in `conveyor_wizard.py` to change the start button and implement a `QDialog` that fetches active shell descriptors. The dialog will provide buttons to load a configuration (refactoring existing clone logic) or clean up a shell and its associated submodels using DELETE requests to the BaSyx repo and registry endpoints.

**Tech Stack:** Python, PyQt6, requests, base64

---

### Task 1: Update Imports in conveyor_wizard.py

**Files:**
- Modify: `C:\Users\LazyT\Desktop\Tese\AAS Client\conveyor_wizard.py:18-26`

- [ ] **Step 1: Add QListWidget and QListWidgetItem to imports**
  Update the imports block at the top of the file to include PyQt6's list widgets.
  
  Replace lines 18-24:
  ```python
  from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                               QFileDialog, QStackedWidget, QFormLayout, 
                               QTreeWidget, QTreeWidgetItem, QCheckBox, 
                               QDoubleSpinBox, QComboBox, QMessageBox, QTextEdit,
                               QGroupBox, QScrollArea, QDialog, QDialogButtonBox,
                               QSplitter)
  ```
  with:
  ```python
  from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                               QFileDialog, QStackedWidget, QFormLayout, 
                               QTreeWidget, QTreeWidgetItem, QCheckBox, 
                               QDoubleSpinBox, QComboBox, QMessageBox, QTextEdit,
                               QGroupBox, QScrollArea, QDialog, QDialogButtonBox,
                               QSplitter, QListWidget, QListWidgetItem)
  ```

- [ ] **Step 2: Verify Python compilation**
  Run compile check:
  `C:\Users\LazyT\Documents\PythonProjects\AAS_API_TESE\.venv\Scripts\python.exe -m py_compile "C:\Users\LazyT\Desktop\Tese\AAS Client\conveyor_wizard.py"`
  Expected: Successful exit code 0.

- [ ] **Step 3: Commit**
  Run:
  ```bash
  git add "AAS Client/conveyor_wizard.py"
  git commit -m "feat: add QListWidget imports to conveyor_wizard.py"
  ```

---

### Task 2: Replace Clone Button with Manage AAS Button

**Files:**
- Modify: `C:\Users\LazyT\Desktop\Tese\AAS Client\conveyor_wizard.py:307-310`

- [ ] **Step 1: Replace clone button definition in setup_steps**
  Modify the `setup_steps` method of ConveyorWizard.
  
  Replace lines 308-310:
  ```python
          self.btn_clone_aas = QPushButton("Clone Existing AAS"); self.btn_clone_aas.setMinimumHeight(55); self.btn_clone_aas.setStyleSheet("background-color: #27ae60;")
          self.btn_clone_aas.clicked.connect(self.clone_from_aas)
          bl.addWidget(self.btn_select_glb); bl.addWidget(self.btn_clone_aas)
  ```
  with:
  ```python
          self.btn_manage_aas = QPushButton("Manage Deployed AAS"); self.btn_manage_aas.setMinimumHeight(55); self.btn_manage_aas.setStyleSheet("background-color: #27ae60;")
          self.btn_manage_aas.clicked.connect(self.manage_deployed_aas)
          bl.addWidget(self.btn_select_glb); bl.addWidget(self.btn_manage_aas)
  ```

- [ ] **Step 2: Verify compilation**
  Run compile check:
  `C:\Users\LazyT\Documents\PythonProjects\AAS_API_TESE\.venv\Scripts\python.exe -m py_compile "C:\Users\LazyT\Desktop\Tese\AAS Client\conveyor_wizard.py"`
  Expected: Successful exit code 0.

- [ ] **Step 3: Commit**
  Run:
  ```bash
  git add "AAS Client/conveyor_wizard.py"
  git commit -m "feat: replace clone button with manage deployed AAS button"
  ```

---

### Task 3: Implement Manage AAS Dialog and Loading/Deletion Logic

**Files:**
- Modify: `C:\Users\LazyT\Desktop\Tese\AAS Client\conveyor_wizard.py` (Add new methods, modify/refactor `clone_from_aas`)

- [ ] **Step 1: Refactor clone_from_aas to load_cloned_aas**
  Rename the existing `clone_from_aas` function to `load_cloned_aas` and modify it to accept `shell_desc` directly rather than fetching from server inside the method itself.
  
  Replace lines 342-358:
  ```python
      def clone_from_aas(self):
          try:
              res = requests.get("http://localhost:8082/shell-descriptors", timeout=5)
              shells = res.json().get("result", [])
              if not shells: return QMessageBox.information(self, "Info", "No AAS found on server.")
          except Exception as e: return QMessageBox.critical(self, "Error", f"Could not connect to registry: {e}")
              
          dlg = QDialog(self); dlg.setWindowTitle("Clone AAS"); layout = QVBoxLayout(dlg)
          combo = QComboBox()
          for s in shells: combo.addItem(f"{s.get('idShort')} ({s.get('id')})", s)
          layout.addWidget(QLabel("Select an existing Kit to clone:")); layout.addWidget(combo)
          btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
          btn_box.accepted.connect(dlg.accept); btn_box.rejected.connect(dlg.reject); layout.addWidget(btn_box)
          
          if dlg.exec() != QDialog.DialogCode.Accepted: return
          shell_desc = combo.currentData()
          QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
  ```
  with:
  ```python
      def load_cloned_aas(self, shell_desc):
          QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
  ```

- [ ] **Step 2: Add manage_deployed_aas implementation**
  Add the implementation for the `manage_deployed_aas` method which initializes the QDialog and runs clone/delete logic. Place it above `load_cloned_aas`.

  Add the following code block:
  ```python
      def manage_deployed_aas(self):
          try:
              res = requests.get("http://localhost:8082/shell-descriptors", timeout=5)
              shells = res.json().get("result", [])
              if not shells:
                  QMessageBox.information(self, "Info", "No AAS found on server.")
                  return
          except Exception as e:
              QMessageBox.critical(self, "Error", f"Could not connect to registry: {e}")
              return

          dlg = QDialog(self)
          dlg.setWindowTitle("Manage Deployed AAS")
          dlg.resize(600, 400)
          layout = QVBoxLayout(dlg)

          layout.addWidget(QLabel("Select a Deployed AAS to Clone or Delete:"))
          
          list_widget = QListWidget()
          layout.addWidget(list_widget)

          def refresh_list():
              list_widget.clear()
              try:
                  res = requests.get("http://localhost:8082/shell-descriptors", timeout=5)
                  shells = res.json().get("result", [])
                  for s in shells:
                      item = QListWidgetItem(f"{s.get('idShort')} ({s.get('id')})")
                      item.setData(Qt.ItemDataRole.UserRole, s)
                      list_widget.addItem(item)
              except Exception as e:
                  QMessageBox.warning(dlg, "Error", f"Failed to refresh list: {e}")

          refresh_list()

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

          def on_clone_clicked():
              item = list_widget.currentItem()
              if not item:
                  QMessageBox.warning(dlg, "Warning", "Please select an AAS to clone.")
                  return
              shell_desc = item.data(Qt.ItemDataRole.UserRole)
              dlg.accept()
              self.load_cloned_aas(shell_desc)

          def on_delete_clicked():
              item = list_widget.currentItem()
              if not item:
                  QMessageBox.warning(dlg, "Warning", "Please select an AAS to delete.")
                  return
              shell_desc = item.data(Qt.ItemDataRole.UserRole)
              id_short = shell_desc.get("idShort", "Unknown")
              shell_id = shell_desc.get("id")

              reply = QMessageBox.question(
                  dlg, "Confirm Delete",
                  f"Are you sure you want to delete AAS '{id_short}' and all its associated submodels?",
                  QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
              )
              if reply != QMessageBox.StandardButton.Yes:
                  return

              QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
              try:
                  encoded_shell_id = base64.urlsafe_b64encode(shell_id.encode()).decode().rstrip("=")
                  
                  # Fetch shell to get submodel references
                  shell_res = requests.get(f"http://localhost:8081/shells/{encoded_shell_id}", timeout=5)
                  if shell_res.status_code == 200:
                      shell_data = shell_res.json()
                      submodel_refs = shell_data.get("submodels", [])
                      for ref in submodel_refs:
                          keys = ref.get("keys", [])
                          if keys:
                              sm_id = keys[0].get("value")
                              encoded_sm_id = base64.urlsafe_b64encode(sm_id.encode()).decode().rstrip("=")
                              
                              # Delete from repository
                              requests.delete(f"http://localhost:8081/submodels/{encoded_sm_id}", timeout=5)
                              # Delete from registry
                              requests.delete(f"http://localhost:8083/submodel-descriptors/{encoded_sm_id}", timeout=5)
                  
                  # Delete shell from repository
                  requests.delete(f"http://localhost:8081/shells/{encoded_shell_id}", timeout=5)
                  
                  # Delete shell descriptor from registry
                  requests.delete(f"http://localhost:8082/shell-descriptors/{encoded_shell_id}", timeout=5)
                  
                  QApplication.restoreOverrideCursor()
                  QMessageBox.information(dlg, "Success", f"AAS '{id_short}' and its associated submodels deleted successfully.")
                  refresh_list()
              except Exception as e:
                  QApplication.restoreOverrideCursor()
                  traceback.print_exc()
                  QMessageBox.critical(dlg, "Error", f"Failed to delete AAS: {e}")

          btn_clone.clicked.connect(on_clone_clicked)
          btn_delete.clicked.connect(on_delete_clicked)
          btn_close.clicked.connect(dlg.reject)

          dlg.exec()
  ```

- [ ] **Step 3: Verify Python compilation**
  Run compile check:
  `C:\Users\LazyT\Documents\PythonProjects\AAS_API_TESE\.venv\Scripts\python.exe -m py_compile "C:\Users\LazyT\Desktop\Tese\AAS Client\conveyor_wizard.py"`
  Expected: Successful exit code 0.

- [ ] **Step 4: Commit**
  Run:
  ```bash
  git add "AAS Client/conveyor_wizard.py"
  git commit -m "feat: implement manage_deployed_aas dialog with loading and deletion"
  ```
