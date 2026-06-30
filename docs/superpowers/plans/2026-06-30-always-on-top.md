# Always on Top Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "📌 Always on Top" checkbox in the sidebar of AAS PLC Studio that dynamically toggles keeping the window on top of other windows.

**Architecture:** Integrate the checkbox in the sidebar layout, style it in the dark theme, and implement the dynamic flag toggling via PyQt6's `self.setWindowFlags()` and `self.show()` method.

**Tech Stack:** Python, PyQt6, unittest.

---

### Task 1: Create a Unit Test for AASPLCStudio

**Files:**
- Create: `AAS Client/test_aas_plc_studio.py`

- [ ] **Step 1: Write the test code**
  Write a unittest test verifying that the checkbox exists, is not checked by default, and correctly toggles the `WindowStaysOnTopHint` flag when checked.
  
  Create file `AAS Client/test_aas_plc_studio.py`:
  ```python
  import unittest
  import sys
  from PyQt6.QtWidgets import QApplication
  from PyQt6.QtCore import Qt
  from aas_plc_studio import AASPLCStudio

  class TestAASPLCStudio(unittest.TestCase):
      @classmethod
      def setUpClass(cls):
          cls.app = QApplication.instance() or QApplication(sys.argv)

      def test_always_on_top_toggle(self):
          window = AASPLCStudio()
          # Verify checkbox exists and is unchecked
          self.assertTrue(hasattr(window, 'chk_always_on_top'))
          self.assertFalse(window.chk_always_on_top.isChecked())
          
          # Toggle always on top ON
          window.chk_always_on_top.setChecked(True)
          self.assertTrue(bool(window.windowFlags() & Qt.WindowType.WindowStaysOnTopHint))
          
          # Toggle always on top OFF
          window.chk_always_on_top.setChecked(False)
          self.assertFalse(bool(window.windowFlags() & Qt.WindowType.WindowStaysOnTopHint))

          window.close()

  if __name__ == "__main__":
      unittest.main()
  ```

- [ ] **Step 2: Run test to verify it fails**
  Run: `python -m unittest test_aas_plc_studio.py` in `AAS Client` directory.
  Expected: FAIL with `AttributeError: 'AASPLCStudio' object has no attribute 'chk_always_on_top'`

---

### Task 2: Implement "Always on Top" Option in AAS PLC Studio

**Files:**
- Modify: `AAS Client/aas_plc_studio.py:1-360`

- [ ] **Step 1: Update PyQt6 Imports**
  Modify imports at the top of the file to include `QCheckBox` in `PyQt6.QtWidgets`.
  Lines 9-11 in `AAS Client/aas_plc_studio.py`:
  ```python
  from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QPushButton, QLabel, QListWidget, 
                               QTextEdit, QGroupBox, QSplitter, QFrame, QCheckBox)
  ```

- [ ] **Step 2: Add QCheckBox to Layout**
  In the constructor `__init__`, add the checkbox in the sidebar layout below the refresh button.
  Lines 238-242 in `AAS Client/aas_plc_studio.py`:
  ```python
          self.btn_refresh = QPushButton("🔄 Refresh Registry")
          self.btn_refresh.clicked.connect(self.trigger_refresh)
          sidebar_layout.addWidget(self.btn_refresh)
          
          self.chk_always_on_top = QCheckBox("📌 Always on Top")
          self.chk_always_on_top.toggled.connect(self.toggle_always_on_top)
          sidebar_layout.addWidget(self.chk_always_on_top)
          
          top_layout.addWidget(sidebar, 1)
  ```

- [ ] **Step 3: Update CSS Stylesheet**
  Add QCheckBox styling into the stylesheet block inside `__init__`.
  Add to the CSS string inside `self.setStyleSheet(...)`:
  ```css
              QCheckBox {
                  color: #e0e0e0;
                  font-size: 13px;
                  margin-top: 8px;
              }
  ```

- [ ] **Step 4: Implement Event Handler Method**
  Add the `toggle_always_on_top` method to the `AASPLCStudio` class.
  Add after `closeEvent` (around line 348) in `AAS Client/aas_plc_studio.py`:
  ```python
      def toggle_always_on_top(self, checked):
          flags = self.windowFlags()
          if checked:
              self.setWindowFlags(flags | Qt.WindowType.WindowStaysOnTopHint)
          else:
              self.setWindowFlags(flags & ~Qt.WindowType.WindowStaysOnTopHint)
          self.show()
  ```

- [ ] **Step 5: Run unit tests to verify they pass**
  Run: `python -m unittest test_aas_plc_studio.py` in `AAS Client` directory.
  Expected: PASS

- [ ] **Step 6: Commit changes**
  Run:
  ```bash
  git add "AAS Client/aas_plc_studio.py" "AAS Client/test_aas_plc_studio.py"
  git commit -m "feat: add always on top option to AAS PLC Studio"
  ```
