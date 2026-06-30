import sys
import os
import base64
import time
import requests
import traceback
import threading
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QMutex, QMutexLocker
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QListWidget, 
                             QTextEdit, QGroupBox, QSplitter, QFrame, QCheckBox)
from PyQt6.QtGui import QColor, QFont

def encode_id(id_str):
    return base64.urlsafe_b64encode(id_str.encode()).decode().rstrip('=')

class RegistryWorker(QThread):
    kits_discovered = pyqtSignal(list)
    connection_status = pyqtSignal(bool)

    def __init__(self, registry_url="http://localhost:8082/shell-descriptors", repo_url="http://localhost:8081"):
        super().__init__()
        self.registry_url = registry_url
        self.repo_url = repo_url
        self.running = True

    def run(self):
        self.running = True
        while self.running:
            try:
                res = requests.get(self.registry_url, timeout=2)
                if res.status_code == 200:
                    shells = res.json().get("result", [])
                    kits = []
                    for s in shells:
                        if not self.running:
                            break
                        shell_id = s.get("id")
                        if not shell_id: continue
                        
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
                        except Exception:
                            pass
                    if self.running:
                        self.kits_discovered.emit(kits)
                        self.connection_status.emit(True)
                else:
                    self.connection_status.emit(False)
            except Exception:
                self.connection_status.emit(False)

            # Sleep 2 seconds in increments of 100ms
            for _ in range(20):
                if not self.running:
                    break
                self.msleep(100)

    def stop(self):
        self.running = False
        self.wait()


class PinsWorker(QThread):
    pins_updated = pyqtSignal(str, list, list)
    connection_status = pyqtSignal(bool)

    def __init__(self, repo_url="http://localhost:8081"):
        super().__init__()
        self.repo_url = repo_url
        self.active_pins_id = None
        self.mutex = QMutex()
        self.running = True

    def set_active_kit_pins(self, pins_id):
        with QMutexLocker(self.mutex):
            self.active_pins_id = pins_id

    def run(self):
        self.running = True
        while self.running:
            active_pins_id = None
            with QMutexLocker(self.mutex):
                active_pins_id = self.active_pins_id

            if active_pins_id:
                try:
                    url = f"{self.repo_url}/submodels/{encode_id(active_pins_id)}/submodel-elements?level=deep"
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
                        if self.running:
                            self.pins_updated.emit(active_pins_id, inputs, outputs)
                            self.connection_status.emit(True)
                    else:
                        self.connection_status.emit(False)
                except Exception:
                    self.connection_status.emit(False)

            self.msleep(100)

    def stop(self):
        self.running = False
        self.wait()



class AASPLCStudio(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AAS PLC Studio - BaSyx Dashboard")
        self.resize(1100, 750)
        self.selected_kit = None
        self.last_states = {}
        self.known_kits = []
        self.input_widgets = {}
        self.output_widgets = {}
        self.registry_online = False
        self.pins_online = False

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
                background-color: #311b92;
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
            QCheckBox {
                color: #e0e0e0;
                font-size: 13px;
                margin-top: 8px;
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
        
        self.chk_always_on_top = QCheckBox("📌 Always on Top")
        self.chk_always_on_top.toggled.connect(self.toggle_always_on_top)
        sidebar_layout.addWidget(self.chk_always_on_top)
        
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

        # 4. Start Background workers
        self.registry_worker = RegistryWorker()
        self.registry_worker.kits_discovered.connect(self.on_kits_discovered)
        self.registry_worker.connection_status.connect(self.on_registry_connection_status)
        
        self.pins_worker = PinsWorker()
        self.pins_worker.pins_updated.connect(self.on_pins_updated)
        self.pins_worker.connection_status.connect(self.on_pins_connection_status)
        
        self.registry_worker.start()
        self.pins_worker.start()

    def log_event(self, msg, level="INFO"):
        t_str = time.strftime("%H:%M:%S")
        color = "#81c784" if level == "INFO" else "#e57373"
        self.txt_logs.append(f"<span style='color: #888;'>[{t_str}]</span> <span style='color: {color};'>[{level}]</span> {msg}")

    def on_registry_connection_status(self, online):
        self.registry_online = online
        self.update_connection_status()

    def on_pins_connection_status(self, online):
        self.pins_online = online
        self.update_connection_status()

    def update_connection_status(self):
        is_online = self.registry_online and (self.selected_kit is None or self.pins_online)
        if is_online:
            self.lbl_status.setText("Online")
            self.lbl_status.setStyleSheet("padding: 4px 8px; border-radius: 4px; background-color: #2e7d32; color: white; font-weight: bold;")
        else:
            self.lbl_status.setText("Offline")
            self.lbl_status.setStyleSheet("padding: 4px 8px; border-radius: 4px; background-color: #c62828; color: white; font-weight: bold;")

    def trigger_refresh(self):
        self.log_event("Manually scanning registry...")
        self.registry_worker.stop()
        self.pins_worker.stop()
        self.registry_online = False
        self.pins_online = False
        self.update_connection_status()
        self.registry_worker.start()
        self.pins_worker.start()

    def toggle_always_on_top(self, checked):
        flags = self.windowFlags()
        if checked:
            self.setWindowFlags(flags | Qt.WindowType.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(flags & ~Qt.WindowType.WindowStaysOnTopHint)
        self.show()

    def closeEvent(self, event):
        self.registry_worker.stop()
        self.pins_worker.stop()
        event.accept()

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count() > 0:
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                elif item.layout() is not None:
                    self.clear_layout(item.layout())

    def on_kits_discovered(self, kits):
        if getattr(self, "known_kits", None) == kits:
            return
        self.known_kits = kits
        
        selected_id = self.selected_kit.get("id") if self.selected_kit else None
        
        self.kit_list.clear()
        for kit in kits:
            from PyQt6.QtWidgets import QListWidgetItem
            item = QListWidgetItem(kit["idShort"])
            self.kit_list.addItem(item)
            
            if selected_id and kit.get("id") == selected_id:
                self.kit_list.setCurrentItem(item)

    def select_kit(self, item):
        row = self.kit_list.row(item)
        if not (0 <= row < len(getattr(self, "known_kits", []))):
            return
        kit = self.known_kits[row]
        
        self.selected_kit = kit
        self.lbl_kit_title.setText(f"Kit: {kit['idShort']}")
        
        # Clear existing card widgets/layouts
        self.clear_layout(self.input_layout)
        self.clear_layout(self.output_layout)
        
        self.input_widgets = {}
        self.output_widgets = {}
        self.last_states = {}
        
        # Update worker active pins ID
        self.pins_online = False
        self.update_connection_status()
        self.pins_worker.set_active_kit_pins(kit["pins_id"])
        self.log_event(f"Selected kit: {kit['idShort']} (Pins submodel: {kit['pins_id']})")

    def toggle_sensor_pin(self, pin_id):
        if not self.selected_kit:
            return
        
        current_val = self.last_states.get(pin_id, False)
        new_val = not current_val
        
        submodel_id = self.selected_kit["pins_id"]
        encoded_sm_id = encode_id(submodel_id)
        repo_url = self.pins_worker.repo_url
        url = f"{repo_url}/submodels/{encoded_sm_id}/submodel-elements/Inputs.{pin_id}"
        
        payload = {
            "idShort": pin_id,
            "modelType": "Property",
            "value": str(new_val).lower(),
            "valueType": "xs:boolean"
        }
        
        def do_put():
            try:
                res = requests.put(url, json=payload, timeout=1.5, headers={"Content-Type": "application/json"})
                if res.status_code in [200, 201, 204]:
                    self.log_event(f"Toggled sensor {pin_id} to {new_val}")
                else:
                    self.log_event(f"Failed to toggle sensor {pin_id}: HTTP {res.status_code}", "ERROR")
            except Exception as e:
                self.log_event(f"Error toggling sensor {pin_id}: {str(e)}", "ERROR")

        threading.Thread(target=do_put, daemon=True).start()

    def on_pins_updated(self, pins_id, inputs, outputs):
        if not self.selected_kit or self.selected_kit.get("pins_id") != pins_id:
            return
        if not hasattr(self, "input_widgets"):
            self.input_widgets = {}
        if not hasattr(self, "output_widgets"):
            self.output_widgets = {}

        # 1. Inputs (Sensors)
        for pin in inputs:
            pin_id = pin.get("idShort")
            if not pin_id:
                continue
            
            val = str(pin.get("value", "false")).lower() == "true"
            
            # Check if card already exists under self.input_group
            if pin_id not in self.input_widgets:
                card = QFrame()
                card.setObjectName("IndicatorBox")
                card.setStyleSheet("""
                    QFrame#IndicatorBox {
                        background-color: #1e1e1e;
                        border: 1px solid #2a2a2a;
                        border-radius: 6px;
                    }
                """)
                card_layout = QHBoxLayout(card)
                card_layout.setContentsMargins(10, 10, 10, 10)
                
                # LED status label
                led = QLabel()
                led.setFixedSize(16, 16)
                led.setStyleSheet("border-radius: 8px; background-color: #555555; border: 1px solid #333333;")
                
                # Name label
                name_lbl = QLabel(pin_id)
                name_lbl.setStyleSheet("font-weight: bold; font-size: 13px;")
                
                # Toggle button
                btn_toggle = QPushButton("Toggle")
                btn_toggle.clicked.connect(lambda checked=False, pid=pin_id: self.toggle_sensor_pin(pid))
                
                card_layout.addWidget(led)
                card_layout.addWidget(name_lbl)
                card_layout.addStretch()
                card_layout.addWidget(btn_toggle)
                
                self.input_layout.addWidget(card)
                self.input_widgets[pin_id] = {
                    "card": card,
                    "led": led,
                    "btn": btn_toggle,
                    "name_lbl": name_lbl
                }
                
            w_dict = self.input_widgets[pin_id]
            
            # Log state changes
            prev_val = self.last_states.get(pin_id)
            if prev_val is None or prev_val != val:
                self.last_states[pin_id] = val
                self.log_event(f"Sensor '{pin_id}' changed to {'ON' if val else 'OFF'}")
                
            # Update the LED indicator style
            if val:
                w_dict["led"].setStyleSheet("border-radius: 8px; background-color: #4caf50; border: 1px solid #81c784;")
            else:
                w_dict["led"].setStyleSheet("border-radius: 8px; background-color: #555555; border: 1px solid #333333;")

        # 2. Outputs (Actuators)
        for pin in outputs:
            pin_id = pin.get("idShort")
            if not pin_id:
                continue
            
            val = str(pin.get("value", "false")).lower() == "true"
            
            if pin_id not in self.output_widgets:
                card = QFrame()
                card.setObjectName("IndicatorBox")
                card_layout = QHBoxLayout(card)
                card_layout.setContentsMargins(10, 10, 10, 10)
                
                # LED status label
                led = QLabel()
                led.setFixedSize(16, 16)
                led.setStyleSheet("border-radius: 8px; background-color: #555555; border: 1px solid #333333;")
                
                # Name label
                name_lbl = QLabel(pin_id)
                name_lbl.setStyleSheet("font-weight: bold; font-size: 13px;")
                
                card_layout.addWidget(led)
                card_layout.addWidget(name_lbl)
                card_layout.addStretch()
                
                self.output_layout.addWidget(card)
                self.output_widgets[pin_id] = {
                    "card": card,
                    "led": led,
                    "name_lbl": name_lbl
                }
                
            w_dict = self.output_widgets[pin_id]
            
            # Log state changes
            prev_val = self.last_states.get(pin_id)
            if prev_val is None or prev_val != val:
                self.last_states[pin_id] = val
                self.log_event(f"Actuator '{pin_id}' changed to {'ON' if val else 'OFF'}")
                
            # Update LED color and card background styling
            if val:
                w_dict["led"].setStyleSheet("border-radius: 8px; background-color: #4caf50; border: 1px solid #81c784;")
                w_dict["card"].setStyleSheet("""
                    QFrame#IndicatorBox {
                        background-color: #1b5e20;
                        border: 1px solid #2e7d32;
                        border-radius: 6px;
                    }
                """)
            else:
                w_dict["led"].setStyleSheet("border-radius: 8px; background-color: #555555; border: 1px solid #333333;")
                w_dict["card"].setStyleSheet("""
                    QFrame#IndicatorBox {
                        background-color: #1e1e1e;
                        border: 1px solid #2a2a2a;
                        border-radius: 6px;
                    }
                """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AASPLCStudio()
    window.show()
    sys.exit(app.exec())

