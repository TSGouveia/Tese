# AAS PLC Studio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a visual PyQt6 desktop dashboard application (`AAS Client/aas_plc_studio.py`) that monitors and controls virtual inputs/outputs of active AAS kits on the BaSyx server.

**Architecture:** A PyQt6 app with a left sidebar for discovering/selecting active kits, a central monitoring panel with LEDs and toggle buttons for virtual pins, and a bottom log panel. A background thread (`PLCWorker`) polls the Registry and selected Kit Submodel periodically using requests.

**Tech Stack:** Python 3, PyQt6, requests.

---

### Task 1: Create the PLC Worker Thread
Establish the background polling thread that communicates with the BaSyx Registry and Repository and communicates via Qt Signals.

**Files:**
- Create: `AAS Client/aas_plc_studio.py`

- [ ] **Step 1: Write the PLCWorker class structure with Qt signals**

Write the following import blocks and the worker class:
```python
import sys
import os
import base64
import time
import requests
import traceback
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QListWidget, 
                             QTextEdit, QGroupBox, QSplitter, QFrame)
from PyQt6.QtGui import QColor, QFont

def encode_id(id_str):
    return base64.urlsafe_b64encode(id_str.encode()).decode().rstrip('=')

class PLCWorker(QThread):
    kits_discovered = pyqtSignal(list)
    pins_updated = pyqtSignal(list, list)
    connection_status = pyqtSignal(bool)

    def __init__(self, registry_url="http://localhost:8082/shell-descriptors", repo_url="http://localhost:8081"):
        super().__init__()
        self.registry_url = registry_url
        self.repo_url = repo_url
        self.active_pins_id = None
        self.running = True

    def set_active_kit_pins(self, pins_id):
        self.active_pins_id = pins_id

    def run(self):
        last_reg_poll = 0.0
        while self.running:
            now = time.time()
            # 1. Poll Registry every 2 seconds
            if now - last_reg_poll >= 2.0:
                last_reg_poll = now
                try:
                    res = requests.get(self.registry_url, timeout=2)
                    if res.status_code == 200:
                        shells = res.json().get("result", [])
                        kits = []
                        for s in shells:
                            shell_id = s.get("id")
                            if not shell_id: continue
                            
                            # Get detailed submodels
                            try:
                                repo_res = requests.get(f"{self.repo_url}/shells/{encode_id(shell_id)}", timeout=1.5)
                                if repo_res.status_code == 200:
                                    shell_data = repo_res.json()
                                    pins_sm_id = None
                                    for sm_ref in shell_data.get("submodels", []):
                                        keys = sm_ref.get("keys", [])
                                        if keys:
                                            sm_id = keys[0].get("value")
                                            if sm_id and ("Pins_" in sm_id or "VirtualPins" in sm_id):
                                                pins_sm_id = sm_id
                                                break
                                    if pins_sm_id:
                                        kits.append({
                                            "idShort": s.get("idShort", "Unknown"),
                                            "id": shell_id,
                                            "pins_id": pins_sm_id
                                        })
                            except:
                                pass
                        self.kits_discovered.emit(kits)
                        self.connection_status.emit(True)
                    else:
                        self.connection_status.emit(False)
                except Exception as e:
                    self.connection_status.emit(False)

            # 2. Poll Active Kit Pins every 100ms
            if self.active_pins_id:
                try:
                    url = f"{self.repo_url}/submodels/{encode_id(self.active_pins_id)}/submodel-elements?level=deep"
                    res = requests.get(url, timeout=1.5)
                    if res.status_code == 200:
                        data = res.json()
                        elements = data.get("result", data) if isinstance(data, dict) else data
                        inputs = []
                        outputs = []
                        for coll in elements:
                            if coll.get("idShort") == "Inputs":
                                inputs = coll.get("value", [])
                            elif coll.get("idShort") == "Outputs":
                                outputs = coll.get("value", [])
                        self.pins_updated.emit(inputs, outputs)
                        self.connection_status.emit(True)
                    else:
                        self.connection_status.emit(False)
                except:
                    self.connection_status.emit(False)

            self.msleep(100)

    def stop(self):
        self.running = False
        self.wait()
```

- [ ] **Step 2: Save the file**
Write the worker code to `AAS Client/aas_plc_studio.py` and commit the file.

---

### Task 2: Create the User Interface layout and theme
Implement the main window styling, sidebar panel, control dashboard, and bottom logger view using PyQt6.

**Files:**
- Modify: `AAS Client/aas_plc_studio.py`

- [ ] **Step 1: Write UI elements and Styling**
Add the UI design code and initialization inside the main window class `AASPLCStudio`:

```python
class AASPLCStudio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AAS PLC Studio - BaSyx Dashboard")
        self.resize(1100, 750)
        self.selected_kit = None
        self.last_states = {}

        # 1. Dark stylesheet theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
            }
            QWidget {
                background-color: #121212;
                color: #e0e0e0;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }
            QListWidget {
                background-color: #1e1e1e;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #2d2d2d;
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background-color: #2a2a2a;
            }
            QListWidget::item:selected {
                background-color: #512da8;
                color: white;
            }
            QPushButton {
                background-color: #311b92;
                border: none;
                color: white;
                padding: 8px 15px;
                border-radius: 4px;
                font-weight: bold;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #4527a0;
            }
            QPushButton:pressed {
                background-color: #5e35b1;
            }
            QGroupBox {
                border: 1px solid #333;
                border-radius: 6px;
                margin-top: 15px;
                font-weight: bold;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                color: #b39ddb;
            }
            QTextEdit {
                background-color: #151515;
                border: 1px solid #2d2d2d;
                border-radius: 4px;
                font-family: 'Consolas', monospace;
                color: #81c784;
            }
            QFrame#IndicatorBox {
                background-color: #1e1e1e;
                border: 1px solid #2a2a2a;
                border-radius: 6px;
            }
        """)

        # 2. Main layout splitter
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        self.setCentralWidget(main_splitter)

        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(10, 10, 10, 10)
        main_splitter.addWidget(top_widget)

        # 2.1 Sidebar layout
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        
        lbl_sidebar = QLabel("Active AAS Kits")
        lbl_sidebar.setStyleSheet("font-weight: bold; font-size: 15px; color: #b39ddb;")
        sidebar_layout.addWidget(lbl_sidebar)

        self.kit_list = QListWidget()
        self.kit_list.itemClicked.connect(self.select_kit)
        sidebar_layout.addWidget(self.kit_list)

        self.btn_refresh = QPushButton("🔄 Refresh Registry")
        self.btn_refresh.clicked.connect(self.trigger_refresh)
        sidebar_layout.addWidget(self.btn_refresh)
        
        top_layout.addWidget(sidebar, 1)

        # 2.2 Central Control Panel
        self.panel = QWidget()
        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(10, 0, 0, 0)

        # Header Status
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        self.lbl_kit_title = QLabel("Select an AAS Kit from the sidebar")
        self.lbl_kit_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #e0e0e0;")
        header_layout.addWidget(self.lbl_kit_title)

        # Connection LED Status Indicator
        self.lbl_status = QLabel("Offline")
        self.lbl_status.setStyleSheet("padding: 4px 8px; border-radius: 4px; background-color: #c62828; color: white; font-weight: bold;")
        header_layout.addWidget(self.lbl_status)
        panel_layout.addWidget(header_widget)

        # Split Inputs & Outputs
        grid_widget = QWidget()
        grid_layout = QHBoxLayout(grid_widget)
        grid_layout.setContentsMargins(0, 10, 0, 0)

        self.input_group = QGroupBox("Inputs (Sensors)")
        self.input_layout = QVBoxLayout(self.input_group)
        self.input_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.output_group = QGroupBox("Outputs (Actuators)")
        self.output_layout = QVBoxLayout(self.output_group)
        self.output_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        grid_layout.addWidget(self.input_group)
        grid_layout.addWidget(self.output_group)
        panel_layout.addWidget(grid_widget)

        top_layout.addWidget(self.panel, 3)

        # 3. Bottom Logger
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        log_layout.setContentsMargins(10, 0, 10, 10)
        
        lbl_logger = QLabel("Live Event Logs")
        lbl_logger.setStyleSheet("font-weight: bold; color: #81c784;")
        log_layout.addWidget(lbl_logger)
        
        self.txt_logs = QTextEdit()
        self.txt_logs.setReadOnly(True)
        log_layout.addWidget(self.txt_logs)
        main_splitter.addWidget(log_widget)
        
        main_splitter.setSizes([500, 200])

        # Log initial event
        self.log_event("App started. Waiting for BaSyx Registry connection...")

        # 4. Start Background worker
        self.worker = PLCWorker()
        self.worker.kits_discovered.connect(self.on_kits_discovered)
        self.worker.pins_updated.connect(self.on_pins_updated)
        self.worker.connection_status.connect(self.on_connection_status)
        self.worker.start()

    def log_event(self, msg, level="INFO"):
        t_str = time.strftime("%H:%M:%S")
        color = "#81c784" if level == "INFO" else "#e57373"
        self.txt_logs.append(f"<span style='color: #888;'>[{t_str}]</span> <span style='color: {color};'>[{level}]</span> {msg}")

    def on_connection_status(self, online):
        if online:
            self.lbl_status.setText("Online")
            self.lbl_status.setStyleSheet("padding: 4px 8px; border-radius: 4px; background-color: #2e7d32; color: white; font-weight: bold;")
        else:
            self.lbl_status.setText("Offline")
            self.lbl_status.setStyleSheet("padding: 4px 8px; border-radius: 4px; background-color: #c62828; color: white; font-weight: bold;")

    def trigger_refresh(self):
        self.log_event("Manually scanning registry...")
        # Restarts worker to force immediate poll
        self.worker.stop()
        self.worker.start()

    def closeEvent(self, event):
        self.worker.stop()
        event.accept()
```

- [ ] **Step 2: Append these methods to `AAS Client/aas_plc_studio.py`**
Write and save code to file.

---

### Task 3: Implement dynamic updates and simulation actions
Handle selection change, rendering of input/output cards, connection checking, and updating property values via PUT requests on BaSyx.

**Files:**
- Modify: `AAS Client/aas_plc_studio.py`

- [ ] **Step 1: Write components updates and toggle events**

Implement the rest of the methods in `AASPLCStudio`:

```python
    def on_kits_discovered(self, kits):
        current_names = [self.kit_list.item(i).text() for i in range(self.kit_list.count())]
        new_names = [k["idShort"] for k in kits]
        
        if current_names != new_names:
            self.kit_list.clear()
            self.kits_data = kits
            for k in kits:
                self.kit_list.addItem(k["idShort"])
            self.log_event(f"Discovered {len(kits)} active AAS kits.")

    def select_kit(self, item):
        kit_name = item.text()
        self.selected_kit = next(k for k in self.kits_data if k["idShort"] == kit_name)
        self.lbl_kit_title.setText(f"Kit: {self.selected_kit['idShort']}")
        self.log_event(f"Selected kit '{self.selected_kit['idShort']}'. Starting Live Polling...")
        
        # Clear existing layouts
        self.clear_layout(self.input_layout)
        self.clear_layout(self.output_layout)
        self.last_states.clear()
        
        self.worker.set_active_kit_pins(self.selected_kit["pins_id"])

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def on_pins_updated(self, inputs, outputs):
        # 1. Update/Create Inputs (Sensors)
        for idx, pin in enumerate(inputs):
            pin_id = pin.get("idShort")
            val_str = str(pin.get("value", "False"))
            is_active = val_str.lower() == "true"
            
            # Check for changes to log
            last_val = self.last_states.get(pin_id)
            if last_val is not None and last_val != is_active:
                self.log_event(f"Sensor '{pin_id}' changed to {is_active}")
            self.last_states[pin_id] = is_active

            # Find or create card widget
            widget_name = f"input_{pin_id}"
            card = self.input_group.findChild(QWidget, widget_name)
            if not card:
                card = QWidget()
                card.setObjectName(widget_name)
                card.setStyleSheet("background-color: #1e1e1e; border: 1px solid #2d2d2d; border-radius: 6px;")
                card_layout = QHBoxLayout(card)
                card_layout.setContentsMargins(10, 5, 10, 5)

                led = QLabel()
                led.setObjectName("led")
                led.setFixedSize(12, 12)
                card_layout.addWidget(led)

                lbl_name = QLabel(pin_id)
                lbl_name.setStyleSheet("font-weight: bold; border: none; background: transparent;")
                card_layout.addWidget(lbl_name)

                btn_toggle = QPushButton("Toggle")
                btn_toggle.setStyleSheet("background-color: #263238; border: 1px solid #37474f; font-size: 11px; min-height: 22px;")
                # Use default arguments in lambda to capture variables correctly in a loop
                btn_toggle.clicked.connect(lambda checked=False, pid=pin_id: self.toggle_sensor_pin(pid))
                card_layout.addWidget(btn_toggle)

                self.input_layout.addWidget(card)

            # Update LED color
            led = card.findChild(QLabel, "led")
            if led:
                color = "#2ecc71" if is_active else "#555"
                led.setStyleSheet(f"background-color: {color}; border-radius: 6px;")

        # 2. Update/Create Outputs (Actuators)
        for idx, pin in enumerate(outputs):
            pin_id = pin.get("idShort")
            val_str = str(pin.get("value", "False"))
            is_active = val_str.lower() == "true"

            # Check for changes to log
            last_val = self.last_states.get(pin_id)
            if last_val is not None and last_val != is_active:
                self.log_event(f"Actuator '{pin_id}' changed to {is_active}")
            self.last_states[pin_id] = is_active

            widget_name = f"output_{pin_id}"
            card = self.output_group.findChild(QWidget, widget_name)
            if not card:
                card = QWidget()
                card.setObjectName(widget_name)
                card.setStyleSheet("background-color: #1e1e1e; border: 1px solid #2d2d2d; border-radius: 6px;")
                card_layout = QHBoxLayout(card)
                card_layout.setContentsMargins(10, 8, 10, 8)

                led = QLabel()
                led.setObjectName("led")
                led.setFixedSize(12, 12)
                card_layout.addWidget(led)

                lbl_name = QLabel(pin_id)
                lbl_name.setStyleSheet("font-weight: bold; border: none; background: transparent;")
                card_layout.addWidget(lbl_name)

                self.output_layout.addWidget(card)

            # Update LED color and background glow
            led = card.findChild(QLabel, "led")
            if led:
                if is_active:
                    led.setStyleSheet("background-color: #00e676; border-radius: 6px;")
                    card.setStyleSheet("background-color: #1b5e20; border: 1px solid #2e7d32; border-radius: 6px;")
                else:
                    led.setStyleSheet("background-color: #555; border-radius: 6px;")
                    card.setStyleSheet("background-color: #1e1e1e; border: 1px solid #2d2d2d; border-radius: 6px;")

    def toggle_sensor_pin(self, pin_id):
        if not self.selected_kit: return
        current_val = self.last_states.get(pin_id, False)
        new_val = not current_val
        
        self.log_event(f"Sending request to toggle '{pin_id}' to {new_val}...")
        
        # Async PUT Request inside a QThread / or quick pool execution
        # Since it is quick, we can execute directly but safely inside a try-catch to avoid freeze
        try:
            url = f"{self.worker.repo_url}/submodels/{encode_id(self.selected_kit['pins_id'])}/submodel-elements/Inputs.{pin_id}"
            payload = {
                "idShort": pin_id,
                "modelType": "Property",
                "value": str(new_val).lower(),
                "valueType": "xs:boolean"
            }
            res = requests.put(url, json=payload, timeout=1.0, headers={"Content-Type": "application/json"})
            if res.status_code not in [200, 201, 204]:
                self.log_event(f"Error toggling pin: Server returned code {res.status_code}", "ERROR")
        except Exception as e:
            self.log_event(f"Error toggling pin: {e}", "ERROR")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AASPLCStudio()
    window.show()
    sys.exit(app.exec())
```

- [ ] **Step 2: Save the file and verify execution**
Save all modifications to `AAS Client/aas_plc_studio.py` and run it to verify everything.
