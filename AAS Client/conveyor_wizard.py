import sys
import os
import json
import trimesh
import numpy as np
import pyvista as pv
import requests
import mimetypes
import hashlib
import posixpath
import base64
import io
import re
import traceback
import time

from pyvistaqt import BackgroundPlotter
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                             QFileDialog, QStackedWidget, QFormLayout, 
                             QTreeWidget, QTreeWidgetItem, QCheckBox, 
                             QDoubleSpinBox, QComboBox, QMessageBox, QTextEdit,
                             QGroupBox, QScrollArea, QDialog, QDialogButtonBox,
                             QSplitter, QListWidget, QListWidgetItem, QInputDialog)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QColor, QFont

import basyx.aas.model as model
import basyx.aas.adapter.aasx as aasx

# =================================================================
# AAS UTILITIES
# =================================================================
class RobustFileRepo(dict):
    def get_content_type(self, fn): return mimetypes.guess_type(fn)[0] or "application/octet-stream"
    def add_file(self, n, c): self[n] = c
    def write_file(self, fn, t):
        if fn in self: t.write(self[fn])
    def get_sha256(self, fn):
        if fn in self: return hashlib.sha256(self[fn]).hexdigest()
        return ""

def sanitize_aas_id(name):
    res = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    res = re.sub(r'_+', '_', res)
    if not res: return "ELEMENT_ID"
    if not res[0].isalpha(): res = "ID_" + res
    return res.strip('_')

def is_valid_aas_id(name):
    if not name: return False
    return bool(re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', name))

ERROR_STYLE = "background-color: #4a1010; border: 1px solid #e74c3c;"
VALID_STYLE = "background-color: #2d2d2d; border: 1px solid #3d3d3d;"
VALIDATION_MSG = "⚠️ Invalid ID: Letters, digits, underscores only. Must start with letter."

class ActuatorWidget(QGroupBox):
    def __init__(self, parent_wizard):
        super().__init__("Actuator Configuration")
        self.wizard = parent_wizard
        self.layout = QFormLayout(self); self.layout.setSpacing(5); self.layout.setContentsMargins(10, 15, 10, 10)
        
        self.edit_pin = QLineEdit("IN_Pin")
        self.edit_pin.textChanged.connect(self.validate)
        
        self.edit_node = QLineEdit("")
        self.edit_node.setReadOnly(True)
        self.edit_node.setPlaceholderText("Select node in Tree or 3D...")
        
        self.combo_stop_sens = QComboBox()
        self.combo_stop_sens.setEditable(True)
        
        self.check_visible = QCheckBox("Visible by Default")
        self.check_visible.setChecked(True)
        
        self.combo_behavior = QComboBox(); self.combo_behavior.addItems([
            "Conveyor", "RotateContinuous", "TranslateContinuous", "Piston", "Linear"
        ])
        
        axis_layout = QHBoxLayout()
        self.spin_x = QDoubleSpinBox(); self.spin_x.setRange(-10, 10); self.spin_x.setSingleStep(0.1); self.spin_x.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.spin_y = QDoubleSpinBox(); self.spin_y.setRange(-10, 10); self.spin_y.setSingleStep(0.1); self.spin_y.setValue(1.0); self.spin_y.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        self.spin_z = QDoubleSpinBox(); self.spin_z.setRange(-10, 10); self.spin_z.setSingleStep(0.1); self.spin_z.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        axis_layout.addWidget(self.spin_x); axis_layout.addWidget(self.spin_y); axis_layout.addWidget(self.spin_z)
        
        self.spin_speed = QDoubleSpinBox(); self.spin_speed.setRange(-100, 100); self.spin_speed.setValue(1.0); self.spin_speed.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        
        self.layout.addRow("Pin ID:", self.edit_pin)
        self.layout.addRow("Target Node:", self.edit_node)
        self.layout.addRow("Behavior:", self.combo_behavior)
        self.layout.addRow("Stop Sensor:", self.combo_stop_sens)
        self.layout.addRow("Axis (X,Y,Z):", axis_layout)
        self.layout.addRow("Speed:", self.spin_speed)
        self.layout.addRow(self.check_visible)
        
        btn_del = QPushButton("Delete")
        btn_del.setStyleSheet("background-color: #a93226;")
        btn_del.clicked.connect(lambda: self.wizard.remove_actuator(self))
        self.layout.addRow(btn_del)
        
        self.update_stop_sensors()
        self.spin_x.valueChanged.connect(self.update_visuals)
        self.spin_y.valueChanged.connect(self.update_visuals)
        self.spin_z.valueChanged.connect(self.update_visuals)
        self.arrow = None; self.update_visuals(); self.validate()

    def validate(self):
        valid = is_valid_aas_id(self.edit_pin.text())
        self.edit_pin.setStyleSheet(VALID_STYLE if valid else ERROR_STYLE)
        self.wizard.update_validation_ui()

    def activate(self):
        self.wizard.current_config_widget = self
        for w in self.wizard.actuator_widgets + self.wizard.sensor_widgets:
            w.setProperty("active", "false")
            if isinstance(w, ActuatorWidget): w.hide_visuals()
            w.style().unpolish(w); w.style().polish(w)
        self.setProperty("active", "true")
        self.style().unpolish(self); self.style().polish(self)
        self.update_visuals()

    def mousePressEvent(self, event):
        self.activate()
        super().mousePressEvent(event)

    def update_stop_sensors(self):
        current = self.combo_stop_sens.currentText()
        self.combo_stop_sens.clear()
        self.combo_stop_sens.addItem("")
        for sw in self.wizard.sensor_widgets:
            pin = sw.edit_pin.text()
            if pin: self.combo_stop_sens.addItem(pin)
        self.combo_stop_sens.setCurrentText(current)

    def set_node(self, name):
        self.edit_node.setPlaceholderText("")
        self.edit_node.setText(name)
        self.update_visuals()

    def hide_visuals(self):
        if self.arrow: self.wizard.plotter.remove_actor(self.arrow); self.arrow = None

    def update_visuals(self):
        self.hide_visuals()
        if self.property("active") != "true": return
        raw_axis = [self.spin_x.value(), self.spin_y.value(), self.spin_z.value()]
        # Adjust visual axis to match Unity's coordinate swap (Y and Z swapped)
        vis_axis = [raw_axis[0], raw_axis[2], raw_axis[1]]
        if any(raw_axis):
            scale = 1.0; node = self.edit_node.text(); pos = [0,0,0]
            if node in self.wizard.meshes:
                family = self.wizard.get_node_family(node)
                all_meshes = [self.wizard.meshes[n] for n in family if n in self.wizard.meshes]
                if all_meshes:
                    b = np.array([m.bounds for m in all_meshes])
                    min_b = np.min(b[:, [0, 2, 4]], axis=0); max_b = np.max(b[:, [1, 3, 5]], axis=0)
                    scale = max(max_b - min_b) * 1.5; pos = (min_b + max_b) / 2.0
            self.arrow = self.wizard.plotter.add_arrows(np.array([pos]), np.array([vis_axis]), mag=scale, color="yellow")

    def get_data(self):
        return { "pin_id": self.edit_pin.text(), "node": self.edit_node.text(), "behavior": self.combo_behavior.currentText(), "stop_sensor": self.combo_stop_sens.currentText(), "axis": [self.spin_x.value(), self.spin_y.value(), self.spin_z.value()], "speed": self.spin_speed.value(), "visible": self.check_visible.isChecked() }

class SensorWidget(QGroupBox):
    def __init__(self, parent_wizard):
        super().__init__("Sensor Configuration")
        self.wizard = parent_wizard
        layout = QFormLayout(self); layout.setSpacing(5); layout.setContentsMargins(10, 15, 10, 10)
        
        self.edit_pin = QLineEdit("OUT_Sensor")
        self.edit_pin.textChanged.connect(self.on_pin_changed)
        
        self.edit_node = QLineEdit("")
        self.edit_node.setReadOnly(True)
        self.edit_node.setPlaceholderText("Select node in Tree or 3D...")
        
        self.check_visible = QCheckBox("Visible Trigger Zone")
        self.check_visible.setChecked(False)
        self.check_active_low = QCheckBox("Active Low")
        self.check_snap = QCheckBox("Snap Product to Sensor Center")
        self.check_snap.setChecked(False)
        
        self.combo_behavior = QComboBox(); self.combo_behavior.addItems(["TriggerZone", "Presence", "Proximity"])
        self.edit_filter = QLineEdit("Metal")
        
        layout.addRow("Pin ID:", self.edit_pin)
        layout.addRow("Detection Node:", self.edit_node)
        layout.addRow("Behavior:", self.combo_behavior)
        layout.addRow("Target Filter:", self.edit_filter)
        layout.addRow(self.check_visible)
        layout.addRow(self.check_active_low)
        layout.addRow(self.check_snap)
        
        btn_del = QPushButton("Delete")
        btn_del.setStyleSheet("background-color: #a93226;")
        btn_del.clicked.connect(lambda: self.wizard.remove_sensor(self))
        layout.addRow(btn_del)
        self.validate()

    def on_pin_changed(self):
        self.validate()
        self.wizard.update_all_actuator_dropdowns()

    def validate(self):
        valid = is_valid_aas_id(self.edit_pin.text())
        self.edit_pin.setStyleSheet(VALID_STYLE if valid else ERROR_STYLE)
        self.wizard.update_validation_ui()

    def activate(self):
        self.wizard.current_config_widget = self
        for w in self.wizard.actuator_widgets + self.wizard.sensor_widgets:
            w.setProperty("active", "false")
            if isinstance(w, ActuatorWidget): w.hide_visuals()
            w.style().unpolish(w); w.style().polish(w)
        self.setProperty("active", "true")
        self.style().unpolish(self); self.style().polish(self)

    def mousePressEvent(self, event):
        self.activate()
        super().mousePressEvent(event)

    def set_node(self, name):
        self.edit_node.setPlaceholderText("")
        self.edit_node.setText(name)

    def get_data(self):
        return { 
            "pin_id": self.edit_pin.text(), 
            "node": self.edit_node.text(), 
            "behavior": self.combo_behavior.currentText(), 
            "target_filter": self.edit_filter.text(), 
            "visible": self.check_visible.isChecked(), 
            "active_low": self.check_active_low.isChecked(),
            "snap_product": self.check_snap.isChecked()
        }

class TriggerRow(QWidget):
    def __init__(self, parent_wizard, sensor_list, initial_sensor="", initial_value=True, on_delete=None, on_changed=None):
        super().__init__()
        self.on_changed = on_changed
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(5)
        
        self.combo_sensor = QComboBox()
        self.combo_sensor.addItems(sensor_list)
        if initial_sensor in sensor_list:
            self.combo_sensor.setCurrentText(initial_sensor)
        
        self.combo_value = QComboBox()
        self.combo_value.addItems(["true", "false"])
        self.combo_value.setCurrentText("true" if initial_value else "false")
        
        btn_del = QPushButton("❌")
        btn_del.setFixedWidth(30)
        btn_del.setStyleSheet("background-color: #a93226; padding: 2px;")
        if on_delete:
            btn_del.clicked.connect(on_delete)
            
        layout.addWidget(self.combo_sensor, 2)
        layout.addWidget(self.combo_value, 1)
        layout.addWidget(btn_del)
        
        self.combo_sensor.currentTextChanged.connect(self._trigger_change)
        self.combo_value.currentTextChanged.connect(self._trigger_change)
        
    def _trigger_change(self):
        if self.on_changed:
            self.on_changed()
            
    def get_data(self):
        return {
            "sensor": self.combo_sensor.currentText(),
            "value": self.combo_value.currentText() == "true"
        }

class ConveyorWizard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Conveyor Wizard")
        self.config_data = {"kit_name": "", "aas_id": "", "description": "", "components": []}
        self.logic_rules = {"start": [], "sequences": []}
        self.glb_path = None; self.meshes = {}; self.actors = {}; self.actuator_widgets = []; self.sensor_widgets = []; 
        self.current_config_widget = None
        self.apply_styles(); self.setup_ui()
        self.showMaximized()
        
    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QWidget { background-color: #1e1e1e; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; }
            QLabel { font-size: 13px; font-weight: 500; }
            QLineEdit, QDoubleSpinBox, QComboBox, QTextEdit { 
                background-color: #2d2d2d; border: 1px solid #3d3d3d; border-radius: 4px; padding: 6px; color: white; 
            }
            QPushButton { background-color: #007acc; color: white; border: none; border-radius: 4px; padding: 8px 16px; font-weight: bold; }
            QPushButton:hover { background-color: #008be5; }
            QGroupBox { border: 1px solid #3d3d3d; border-radius: 8px; margin-top: 15px; padding-top: 20px; font-weight: bold; background-color: #252526; }
            QGroupBox[active="true"] { border: 2px solid #007acc; background-color: #2d2d30; }
            QTreeWidget { background-color: #252526; border: 1px solid #3d3d3d; border-radius: 4px; }
            QTreeWidget::item:selected { background-color: #094771; }
            QSplitter::handle { background-color: #333; }
            QScrollArea { border: none; background-color: transparent; }
        """)

    def setup_ui(self):
        central = QWidget(); self.setCentralWidget(central); main_layout = QVBoxLayout(central); main_layout.setContentsMargins(0, 0, 0, 0)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        self.wizard_panel = QWidget(); self.wizard_panel.setMinimumWidth(400); self.wizard_layout = QVBoxLayout(self.wizard_panel)
        self.step_label = QLabel("Step 1 of 6: Model Selection"); self.step_label.setStyleSheet("font-size: 20px; color: #007acc; margin-bottom: 5px;")
        self.wizard_layout.addWidget(self.step_label); self.stack = QStackedWidget(); self.wizard_layout.addWidget(self.stack); self.setup_steps()
        
        self.lbl_global_error = QLabel(VALIDATION_MSG); self.lbl_global_error.setStyleSheet("color: #e74c3c; font-weight: bold; background-color: #2d1e1e; padding: 10px; border-radius: 4px;")
        self.lbl_global_error.setVisible(False); self.wizard_layout.addWidget(self.lbl_global_error)

        nav_layout = QHBoxLayout(); self.btn_prev = QPushButton("← Back"); self.btn_prev.setMinimumHeight(40); self.btn_prev.clicked.connect(self.prev_step); self.btn_prev.setEnabled(False)
        self.btn_next = QPushButton("Next →"); self.btn_next.setMinimumHeight(40); self.btn_next.clicked.connect(self.next_step)
        nav_layout.addWidget(self.btn_prev); nav_layout.addWidget(self.btn_next); self.wizard_layout.addLayout(nav_layout)
        
        self.viewer_container = QWidget(); viewer_layout = QVBoxLayout(self.viewer_container); viewer_layout.setContentsMargins(0, 0, 0, 0)
        self.plotter = BackgroundPlotter(show=False); self.plotter.set_background("#161616")
        
        # NUCLEAR OPTION FOR HELP TEXT
        self.plotter.enable_mesh_picking(callback=self.on_mesh_picked, show=False, show_message=False, left_clicking=True)
        self.cleanup_timer = QTimer(); self.cleanup_timer.timeout.connect(self.kill_overlays); self.cleanup_timer.start(200)
        
        viewer_layout.addWidget(self.plotter.interactor)
        try: self.plotter.camera.up = (0, 1, 0); self.plotter.enable_terrain_style()
        except: pass

        self.node_sidebar = QGroupBox("Model Structure"); self.node_sidebar.setMinimumWidth(220); side_vbox = QVBoxLayout(self.node_sidebar)
        self.node_tree = QTreeWidget(); self.node_tree.setHeaderLabel("Hierarchy"); self.node_tree.itemClicked.connect(self.on_tree_item_clicked); self.node_tree.mousePressEvent = self.tree_mouse_press; side_vbox.addWidget(self.node_tree)

        self.splitter.addWidget(self.wizard_panel); self.splitter.addWidget(self.viewer_container); self.splitter.addWidget(self.node_sidebar)
        self.splitter.setStretchFactor(1, 4); main_layout.addWidget(self.splitter)

    def kill_overlays(self):
        try:
            self.plotter.disable_picking_help()
            for actor_name in list(self.plotter.renderer.actors.keys()):
                if any(x in actor_name.lower() for x in ["text", "message", "pick", "prompt", "info"]): self.plotter.remove_actor(actor_name)
        except: pass

    def tree_mouse_press(self, event):
        item = self.node_tree.itemAt(event.pos())
        if not item: self.node_tree.clearSelection(); self.deselect_all()
        QTreeWidget.mousePressEvent(self.node_tree, event)

    def deselect_all(self):
        for actor in self.actors.values(): actor.prop.opacity = 1.0



    def setup_steps(self):
        # P1: Model Selection
        self.page1 = QWidget(); l1 = QVBoxLayout(self.page1); l1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        il = QLabel("📁"); il.setAlignment(Qt.AlignmentFlag.AlignCenter); il.setStyleSheet("font-size: 60px;")
        
        bl = QVBoxLayout(); bl.setSpacing(10); bl.setContentsMargins(50, 0, 50, 0)
        self.btn_select_glb = QPushButton("Select GLB File"); self.btn_select_glb.setMinimumHeight(55); self.btn_select_glb.clicked.connect(self.browse_glb)
        self.btn_manage_aas = QPushButton("Manage Deployed AAS"); self.btn_manage_aas.setMinimumHeight(55); self.btn_manage_aas.setStyleSheet("background-color: #27ae60;")
        self.btn_manage_aas.clicked.connect(self.manage_deployed_aas)
        self.btn_preview_layout = QPushButton("Preview Deployed Layout"); self.btn_preview_layout.setMinimumHeight(55); self.btn_preview_layout.setStyleSheet("background-color: #8e44ad;")
        self.btn_preview_layout.clicked.connect(self.preview_deployed_layout)
        bl.addWidget(self.btn_select_glb); bl.addWidget(self.btn_manage_aas); bl.addWidget(self.btn_preview_layout)
        
        self.lbl_glb_path = QLabel("No file selected")
        l1.addWidget(il); l1.addLayout(bl); l1.addWidget(self.lbl_glb_path); self.stack.addWidget(self.page1)

        # P2: Basic & Transform
        self.page2 = QWidget(); l2 = QVBoxLayout(self.page2); info_group = QGroupBox("System Info"); ifl = QFormLayout(info_group)
        self.edit_kit_name = QLineEdit("ConveyorKit"); self.edit_aas_id = QLineEdit("Conveyor_01"); self.edit_desc = QLineEdit("Standard Conveyor System")
        self.edit_aas_id.textChanged.connect(self.update_validation_ui)
        self.check_is_dynamic = QCheckBox("Is Dynamic (adds Rigidbody/Physics in Unity)")
        ifl.addRow("Kit Name:", self.edit_kit_name); ifl.addRow("AAS ID:", self.edit_aas_id); ifl.addRow("Description:", self.edit_desc)
        ifl.addRow("", self.check_is_dynamic)
        
        trans_group = QGroupBox("System Transform"); tfl = QFormLayout(trans_group)
        self.sys_pos = [QDoubleSpinBox() for _ in range(3)]; self.sys_rot = [QDoubleSpinBox() for _ in range(3)]; self.sys_scale = [QDoubleSpinBox() for _ in range(3)]
        pos_l = QHBoxLayout(); rot_l = QHBoxLayout(); sca_l = QHBoxLayout()
        for i in range(3): 
            self.sys_pos[i].setRange(-100, 100); self.sys_pos[i].setSingleStep(0.1); self.sys_pos[i].setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons); pos_l.addWidget(self.sys_pos[i])
            self.sys_rot[i].setRange(-360, 360); self.sys_rot[i].setSingleStep(5.0); self.sys_rot[i].setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons); rot_l.addWidget(self.sys_rot[i])
            self.sys_scale[i].setRange(0, 100); self.sys_scale[i].setValue(1.0); self.sys_scale[i].setSingleStep(0.1); self.sys_scale[i].setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons); sca_l.addWidget(self.sys_scale[i])
        tfl.addRow("Position:", pos_l); tfl.addRow("Rotation:", rot_l); tfl.addRow("Scale:", sca_l)
        l2.addWidget(info_group); l2.addWidget(trans_group); l2.addStretch(); self.stack.addWidget(self.page2)
        
        # P3: Sensors
        self.page3 = QWidget(); l3 = QVBoxLayout(self.page3); self.scroll_sens = QScrollArea(); self.scroll_sens.setWidgetResizable(True); self.sens_container = QWidget(); self.sens_layout = QVBoxLayout(self.sens_container); self.scroll_sens.setWidget(self.sens_container)
        l3.addWidget(self.scroll_sens); bs = QPushButton("➕ Add Sensor"); bs.clicked.connect(self.add_sensor); l3.addWidget(bs); self.stack.addWidget(self.page3)

        # P4: Actuators
        self.page4 = QWidget(); l4 = QVBoxLayout(self.page4); self.scroll_act = QScrollArea(); self.scroll_act.setWidgetResizable(True); self.act_container = QWidget(); self.act_layout = QVBoxLayout(self.act_container); self.scroll_act.setWidget(self.act_container)
        l4.addWidget(self.scroll_act); ba = QPushButton("➕ Add Actuator"); ba.clicked.connect(self.add_actuator); l4.addWidget(ba); self.stack.addWidget(self.page4)
        
        # P5: Control Logic
        self.page5 = QWidget()
        self.setup_control_logic_page()
        self.stack.addWidget(self.page5)
        
        # P6: Preview
        self.page6 = QWidget()
        l6 = QVBoxLayout(self.page6)
        self.json_preview = QTextEdit()
        self.json_preview.setReadOnly(True)
        l6.addWidget(self.json_preview)
        self.stack.addWidget(self.page6)

    def setup_control_logic_page(self):
        l5 = QVBoxLayout(self.page5)
        l5.setContentsMargins(10, 10, 10, 10)
        l5.setSpacing(10)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        l5.addWidget(splitter)
        
        # Panel A: Left (Sequences List)
        panel_a = QGroupBox("Sequences")
        layout_a = QVBoxLayout(panel_a)
        layout_a.setContentsMargins(10, 15, 10, 10)
        self.list_sequences = QListWidget()
        self.list_sequences.addItem("Start Sequence")
        layout_a.addWidget(self.list_sequences)
        
        btn_layout_a = QHBoxLayout()
        self.btn_add_seq = QPushButton("Add Sequence")
        self.btn_del_seq = QPushButton("Delete Sequence")
        self.btn_del_seq.setStyleSheet("background-color: #a93226;")
        btn_layout_a.addWidget(self.btn_add_seq)
        btn_layout_a.addWidget(self.btn_del_seq)
        layout_a.addLayout(btn_layout_a)
        
        # Panel B: Middle (Trigger Conditions)
        self.group_triggers = QGroupBox("Trigger Conditions")
        layout_b = QVBoxLayout(self.group_triggers)
        layout_b.setContentsMargins(10, 15, 10, 10)
        
        op_layout = QHBoxLayout()
        op_layout.addWidget(QLabel("Operator:"))
        self.combo_trigger_op = QComboBox()
        self.combo_trigger_op.addItems(["AND", "OR"])
        op_layout.addWidget(self.combo_trigger_op)
        op_layout.addStretch()
        layout_b.addLayout(op_layout)
        
        self.scroll_triggers = QScrollArea()
        self.scroll_triggers.setWidgetResizable(True)
        self.triggers_container = QWidget()
        self.triggers_layout = QVBoxLayout(self.triggers_container)
        self.triggers_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.triggers_layout.setContentsMargins(0, 0, 0, 0)
        self.triggers_layout.setSpacing(5)
        self.scroll_triggers.setWidget(self.triggers_container)
        layout_b.addWidget(self.scroll_triggers)
        
        self.btn_add_trigger = QPushButton("➕ Add Trigger Condition")
        layout_b.addWidget(self.btn_add_trigger)
        
        # Panel C: Right (Sequence Steps)
        self.group_steps = QGroupBox("Sequence Steps")
        layout_c = QVBoxLayout(self.group_steps)
        layout_c.setContentsMargins(10, 15, 10, 10)
        
        self.list_steps = QListWidget()
        layout_c.addWidget(self.list_steps)
        
        btn_add_step_layout = QHBoxLayout()
        self.btn_add_set_act = QPushButton("Add Set Actuator")
        self.btn_add_wait_until = QPushButton("Add Wait Until")
        self.btn_add_wait_time = QPushButton("Add Wait Time")
        btn_add_step_layout.addWidget(self.btn_add_set_act)
        btn_add_step_layout.addWidget(self.btn_add_wait_until)
        btn_add_step_layout.addWidget(self.btn_add_wait_time)
        layout_c.addLayout(btn_add_step_layout)
        
        btn_control_layout = QHBoxLayout()
        self.btn_move_up = QPushButton("Move Up")
        self.btn_move_down = QPushButton("Move Down")
        self.btn_delete_step = QPushButton("Delete Step")
        self.btn_delete_step.setStyleSheet("background-color: #a93226;")
        btn_control_layout.addWidget(self.btn_move_up)
        btn_control_layout.addWidget(self.btn_move_down)
        btn_control_layout.addWidget(self.btn_delete_step)
        layout_c.addLayout(btn_control_layout)
        
        # Bottom Edit Pane
        self.group_step_edit = QGroupBox("Edit Selected Step")
        self.step_edit_layout = QVBoxLayout(self.group_step_edit)
        self.step_edit_layout.setContentsMargins(10, 15, 10, 10)
        self.step_edit_stack = QStackedWidget()
        self.step_edit_layout.addWidget(self.step_edit_stack)
        layout_c.addWidget(self.group_step_edit)
        
        # Add to splitter
        splitter.addWidget(panel_a)
        splitter.addWidget(self.group_triggers)
        splitter.addWidget(self.group_steps)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 2)
        
        # Step Edit Stack Pages
        # Page 0: Empty
        page_empty = QWidget()
        layout_empty = QVBoxLayout(page_empty)
        lbl_empty = QLabel("Select a step to edit properties")
        lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_empty.addWidget(lbl_empty)
        self.step_edit_stack.addWidget(page_empty)
        
        # Page 1: set_actuator
        page_actuator = QWidget()
        layout_actuator = QFormLayout(page_actuator)
        layout_actuator.setContentsMargins(0, 0, 0, 0)
        layout_actuator.setSpacing(5)
        self.edit_step_actuator_combo = QComboBox()
        self.edit_step_actuator_val = QCheckBox("Active / On")
        layout_actuator.addRow("Actuator:", self.edit_step_actuator_combo)
        layout_actuator.addRow("Target State:", self.edit_step_actuator_val)
        self.step_edit_stack.addWidget(page_actuator)
        
        # Page 2: wait_time
        page_time = QWidget()
        layout_time = QFormLayout(page_time)
        layout_time.setContentsMargins(0, 0, 0, 0)
        layout_time.setSpacing(5)
        self.edit_step_wait_time_spin = QDoubleSpinBox()
        self.edit_step_wait_time_spin.setRange(0.0, 3600.0)
        self.edit_step_wait_time_spin.setSingleStep(0.1)
        self.edit_step_wait_time_spin.setSuffix(" seconds")
        self.edit_step_wait_time_spin.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        layout_time.addRow("Delay:", self.edit_step_wait_time_spin)
        self.step_edit_stack.addWidget(page_time)
        
        # Page 3: wait_until
        page_until = QWidget()
        layout_until = QVBoxLayout(page_until)
        layout_until.setContentsMargins(0, 0, 0, 0)
        layout_until.setSpacing(5)
        
        until_op_layout = QHBoxLayout()
        until_op_layout.addWidget(QLabel("Operator:"))
        self.edit_step_wait_until_op = QComboBox()
        self.edit_step_wait_until_op.addItems(["AND", "OR"])
        until_op_layout.addWidget(self.edit_step_wait_until_op)
        until_op_layout.addStretch()
        layout_until.addLayout(until_op_layout)
        
        self.scroll_step_wait_until = QScrollArea()
        self.scroll_step_wait_until.setWidgetResizable(True)
        self.scroll_step_wait_until.setMinimumHeight(100)
        self.step_wait_until_container = QWidget()
        self.step_wait_until_layout = QVBoxLayout(self.step_wait_until_container)
        self.step_wait_until_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.step_wait_until_layout.setContentsMargins(0, 0, 0, 0)
        self.step_wait_until_layout.setSpacing(5)
        self.scroll_step_wait_until.setWidget(self.step_wait_until_container)
        layout_until.addWidget(self.scroll_step_wait_until)
        
        self.btn_add_step_wait_until_cond = QPushButton("➕ Add Sensor Condition")
        layout_until.addWidget(self.btn_add_step_wait_until_cond)
        self.step_edit_stack.addWidget(page_until)
        
        # Connections
        self.list_sequences.currentRowChanged.connect(self.on_sequence_selected)
        self.btn_add_seq.clicked.connect(self.add_sequence)
        self.btn_del_seq.clicked.connect(self.delete_sequence)
        
        self.combo_trigger_op.currentTextChanged.connect(self.save_trigger_changes)
        self.btn_add_trigger.clicked.connect(self.add_trigger_condition)
        
        self.list_steps.currentRowChanged.connect(self.update_step_edit_pane)
        self.btn_add_set_act.clicked.connect(self.add_set_actuator_step)
        self.btn_add_wait_time.clicked.connect(self.add_wait_time_step)
        self.btn_add_wait_until.clicked.connect(self.add_wait_until_step)
        
        self.btn_move_up.clicked.connect(self.move_step_up)
        self.btn_move_down.clicked.connect(self.move_step_down)
        self.btn_delete_step.clicked.connect(self.delete_step)
        
        self.edit_step_actuator_combo.currentTextChanged.connect(self.save_current_step_changes)
        self.edit_step_actuator_val.toggled.connect(self.save_current_step_changes)
        self.edit_step_wait_time_spin.valueChanged.connect(self.save_current_step_changes)
        self.edit_step_wait_until_op.currentTextChanged.connect(self.save_current_step_changes)
        self.btn_add_step_wait_until_cond.clicked.connect(self.add_step_condition)
        
        # Initialize visibility & status
        self.group_triggers.setVisible(False)
        self.btn_del_seq.setEnabled(False)
        self.step_edit_stack.setCurrentIndex(0)

    def refresh_logic_dropdowns(self):
        sensors = [sw.edit_pin.text() for sw in self.sensor_widgets if sw.edit_pin.text()]
        actuators = [aw.edit_pin.text() for aw in self.actuator_widgets if aw.edit_pin.text()]
        
        # Update sequence triggers
        for i in range(self.triggers_layout.count()):
            w = self.triggers_layout.itemAt(i).widget()
            if isinstance(w, TriggerRow):
                curr_text = w.combo_sensor.currentText()
                w.combo_sensor.blockSignals(True)
                w.combo_sensor.clear()
                w.combo_sensor.addItems(sensors)
                w.combo_sensor.setCurrentText(curr_text)
                w.combo_sensor.blockSignals(False)
                
        # Update step actuator dropdown
        curr_act = self.edit_step_actuator_combo.currentText()
        self.edit_step_actuator_combo.blockSignals(True)
        self.edit_step_actuator_combo.clear()
        self.edit_step_actuator_combo.addItems(actuators)
        self.edit_step_actuator_combo.setCurrentText(curr_act)
        self.edit_step_actuator_combo.blockSignals(False)
        
        # Update step wait_until sensor dropdowns
        for i in range(self.step_wait_until_layout.count()):
            w = self.step_wait_until_layout.itemAt(i).widget()
            if isinstance(w, TriggerRow):
                curr_text = w.combo_sensor.currentText()
                w.combo_sensor.blockSignals(True)
                w.combo_sensor.clear()
                w.combo_sensor.addItems(sensors)
                w.combo_sensor.setCurrentText(curr_text)
                w.combo_sensor.blockSignals(False)

    def get_current_steps_list(self):
        row = self.list_sequences.currentRow()
        if row == 0:
            return self.logic_rules["start"]
        elif row > 0 and (row - 1) < len(self.logic_rules["sequences"]):
            return self.logic_rules["sequences"][row - 1]["steps"]
        return None

    def refresh_steps_list(self):
        self.list_steps.blockSignals(True)
        self.list_steps.clear()
        steps = self.get_current_steps_list()
        if steps is not None:
            for step in steps:
                text = self.get_step_display_text(step)
                self.list_steps.addItem(text)
        self.list_steps.blockSignals(False)
        self.update_step_edit_pane()

    def get_step_display_text(self, step):
        t = step.get("type")
        if t == "set_actuator":
            act = step.get("actuator", "None")
            val = step.get("value", False)
            return f"Set Actuator: {act} -> {val}"
        elif t == "wait_time":
            val = step.get("seconds", 0.0)
            return f"Wait Time: {val}s"
        elif t == "wait_until":
            op = step.get("operator", "AND")
            conds = step.get("conditions", [])
            cond_str = ", ".join([f"{c.get('sensor')}=={c.get('value')}" for c in conds])
            return f"Wait Until: {op} ({cond_str})"
        return "Unknown Step"

    def block_step_edit_signals(self, block):
        self.edit_step_actuator_combo.blockSignals(block)
        self.edit_step_actuator_val.blockSignals(block)
        self.edit_step_wait_time_spin.blockSignals(block)
        self.edit_step_wait_until_op.blockSignals(block)

    def update_step_edit_pane(self):
        step_row = self.list_steps.currentRow()
        steps = self.get_current_steps_list()
        
        if steps is None or step_row < 0 or step_row >= len(steps):
            self.step_edit_stack.setCurrentIndex(0)
            return
            
        step = steps[step_row]
        t = step.get("type")
        
        self.block_step_edit_signals(True)
        
        if t == "set_actuator":
            self.step_edit_stack.setCurrentIndex(1)
            self.edit_step_actuator_combo.clear()
            actuators = [aw.edit_pin.text() for aw in self.actuator_widgets if aw.edit_pin.text()]
            self.edit_step_actuator_combo.addItems(actuators)
            self.edit_step_actuator_combo.setCurrentText(step.get("actuator", ""))
            self.edit_step_actuator_val.setChecked(bool(step.get("value", False)))
            
        elif t == "wait_time":
            self.step_edit_stack.setCurrentIndex(2)
            self.edit_step_wait_time_spin.setValue(float(step.get("seconds", 0.0)))
            
        elif t == "wait_until":
            self.step_edit_stack.setCurrentIndex(3)
            self.edit_step_wait_until_op.setCurrentText(step.get("operator", "AND"))
            while self.step_wait_until_layout.count() > 0:
                child = self.step_wait_until_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
                    
            sensors = [sw.edit_pin.text() for sw in self.sensor_widgets if sw.edit_pin.text()]
            for cond in step.get("conditions", []):
                row_widget = TriggerRow(
                    self,
                    sensors,
                    initial_sensor=cond.get("sensor", ""),
                    initial_value=cond.get("value", True),
                    on_delete=lambda w=None: self.delete_step_condition(row_widget),
                    on_changed=self.save_current_step_changes
                )
                self.step_wait_until_layout.addWidget(row_widget)
                
        else:
            self.step_edit_stack.setCurrentIndex(0)
            
        self.block_step_edit_signals(False)

    def delete_step_condition(self, row_widget):
        row_widget.deleteLater()
        QTimer.singleShot(50, self.save_current_step_changes)

    def save_current_step_changes(self):
        step_row = self.list_steps.currentRow()
        steps = self.get_current_steps_list()
        
        if steps is None or step_row < 0 or step_row >= len(steps):
            return
            
        step = steps[step_row]
        t = step.get("type")
        
        if t == "set_actuator":
            step["actuator"] = self.edit_step_actuator_combo.currentText()
            step["value"] = self.edit_step_actuator_val.isChecked()
        elif t == "wait_time":
            step["seconds"] = self.edit_step_wait_time_spin.value()
        elif t == "wait_until":
            step["operator"] = self.edit_step_wait_until_op.currentText()
            conds = []
            for i in range(self.step_wait_until_layout.count()):
                w = self.step_wait_until_layout.itemAt(i).widget()
                if isinstance(w, TriggerRow):
                    conds.append(w.get_data())
            step["conditions"] = conds
            
        self.list_steps.item(step_row).setText(self.get_step_display_text(step))
        self.update_json_preview()

    def save_trigger_changes(self):
        row = self.list_sequences.currentRow()
        if row <= 0:
            return
            
        seq_idx = row - 1
        if seq_idx < 0 or seq_idx >= len(self.logic_rules["sequences"]):
            return
            
        seq = self.logic_rules["sequences"][seq_idx]
        if "trigger" not in seq or not isinstance(seq["trigger"], dict):
            seq["trigger"] = {"operator": "AND", "conditions": []}
            
        seq["trigger"]["operator"] = self.combo_trigger_op.currentText()
        
        triggers = []
        for i in range(self.triggers_layout.count()):
            w = self.triggers_layout.itemAt(i).widget()
            if isinstance(w, TriggerRow):
                triggers.append(w.get_data())
        seq["trigger"]["conditions"] = triggers
        
        self.update_json_preview()

    def add_trigger_condition(self):
        row = self.list_sequences.currentRow()
        if row <= 0:
            return
            
        sensors = [sw.edit_pin.text() for sw in self.sensor_widgets if sw.edit_pin.text()]
        row_widget = TriggerRow(
            self,
            sensors,
            initial_sensor="",
            initial_value=True,
            on_delete=lambda w=None: self.delete_trigger_condition(row_widget),
            on_changed=self.save_trigger_changes
        )
        self.triggers_layout.addWidget(row_widget)
        self.save_trigger_changes()
        
    def delete_trigger_condition(self, row_widget):
        row_widget.deleteLater()
        QTimer.singleShot(50, self.save_trigger_changes)

    def on_sequence_selected(self, row):
        self.save_current_step_changes()
        
        if row == 0:
            self.group_triggers.setVisible(False)
            self.refresh_steps_list()
        elif row > 0 and (row - 1) < len(self.logic_rules["sequences"]):
            self.group_triggers.setVisible(True)
            seq = self.logic_rules["sequences"][row - 1]
            if "trigger" not in seq or not isinstance(seq["trigger"], dict):
                seq["trigger"] = {"operator": "AND", "conditions": []}
            
            self.combo_trigger_op.blockSignals(True)
            self.combo_trigger_op.setCurrentText(seq["trigger"].get("operator", "AND"))
            self.combo_trigger_op.blockSignals(False)
            
            while self.triggers_layout.count() > 0:
                child = self.triggers_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
                    
            sensors = [sw.edit_pin.text() for sw in self.sensor_widgets if sw.edit_pin.text()]
            for cond in seq["trigger"].get("conditions", []):
                row_widget = TriggerRow(
                    self,
                    sensors,
                    initial_sensor=cond.get("sensor", ""),
                    initial_value=cond.get("value", True),
                    on_delete=lambda w=None: self.delete_trigger_condition(row_widget),
                    on_changed=self.save_trigger_changes
                )
                self.triggers_layout.addWidget(row_widget)
                
            self.refresh_steps_list()
        else:
            self.group_triggers.setVisible(False)
            self.list_steps.clear()
            self.step_edit_stack.setCurrentIndex(0)
            
        self.btn_del_seq.setEnabled(row > 0)

    def add_sequence(self):
        name, ok = QInputDialog.getText(self, "Add Sequence", "Enter sequence name:")
        if ok and name.strip():
            name = name.strip()
            existing = ["Start Sequence"] + [s["name"] for s in self.logic_rules["sequences"]]
            if name in existing:
                QMessageBox.warning(self, "Warning", "A sequence with this name already exists.")
                return
            
            self.logic_rules["sequences"].append({
                "name": name,
                "trigger": {"operator": "AND", "conditions": []},
                "steps": []
            })
            self.list_sequences.addItem(name)
            self.list_sequences.setCurrentRow(self.list_sequences.count() - 1)
            self.update_json_preview()

    def delete_sequence(self):
        row = self.list_sequences.currentRow()
        if row <= 0:
            QMessageBox.warning(self, "Warning", "Cannot delete the permanent Start Sequence.")
            return
            
        seq_idx = row - 1
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete sequence '{self.logic_rules['sequences'][seq_idx]['name']}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            del self.logic_rules["sequences"][seq_idx]
            self.list_sequences.takeItem(row)
            self.list_sequences.setCurrentRow(row - 1)
            self.update_json_preview()

    def add_set_actuator_step(self):
        steps = self.get_current_steps_list()
        if steps is not None:
            actuators = [aw.edit_pin.text() for aw in self.actuator_widgets if aw.edit_pin.text()]
            act = actuators[0] if actuators else ""
            steps.append({
                "type": "set_actuator",
                "actuator": act,
                "value": False
            })
            self.refresh_steps_list()
            self.list_steps.setCurrentRow(len(steps) - 1)
            self.update_json_preview()

    def add_wait_time_step(self):
        steps = self.get_current_steps_list()
        if steps is not None:
            steps.append({
                "type": "wait_time",
                "seconds": 1.0
            })
            self.refresh_steps_list()
            self.list_steps.setCurrentRow(len(steps) - 1)
            self.update_json_preview()

    def add_wait_until_step(self):
        steps = self.get_current_steps_list()
        if steps is not None:
            steps.append({
                "type": "wait_until",
                "operator": "AND",
                "conditions": []
            })
            self.refresh_steps_list()
            self.list_steps.setCurrentRow(len(steps) - 1)
            self.update_json_preview()

    def add_step_condition(self):
        step_row = self.list_steps.currentRow()
        steps = self.get_current_steps_list()
        if steps is None or step_row < 0 or step_row >= len(steps):
            return
        step = steps[step_row]
        if step.get("type") != "wait_until":
            return
            
        sensors = [sw.edit_pin.text() for sw in self.sensor_widgets if sw.edit_pin.text()]
        row_widget = TriggerRow(
            self,
            sensors,
            initial_sensor="",
            initial_value=True,
            on_delete=lambda w=None: self.delete_step_condition(row_widget),
            on_changed=self.save_current_step_changes
        )
        self.step_wait_until_layout.addWidget(row_widget)
        self.save_current_step_changes()

    def move_step_up(self):
        step_row = self.list_steps.currentRow()
        steps = self.get_current_steps_list()
        if steps is not None and step_row > 0:
            steps[step_row], steps[step_row - 1] = steps[step_row - 1], steps[step_row]
            self.refresh_steps_list()
            self.list_steps.setCurrentRow(step_row - 1)
            self.update_json_preview()

    def move_step_down(self):
        step_row = self.list_steps.currentRow()
        steps = self.get_current_steps_list()
        if steps is not None and 0 <= step_row < len(steps) - 1:
            steps[step_row], steps[step_row + 1] = steps[step_row + 1], steps[step_row]
            self.refresh_steps_list()
            self.list_steps.setCurrentRow(step_row + 1)
            self.update_json_preview()

    def delete_step(self):
        step_row = self.list_steps.currentRow()
        steps = self.get_current_steps_list()
        if steps is not None and 0 <= step_row < len(steps):
            reply = QMessageBox.question(
                self, "Confirm Delete",
                "Are you sure you want to delete this step?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                del steps[step_row]
                self.refresh_steps_list()
                if step_row < len(steps):
                    self.list_steps.setCurrentRow(step_row)
                elif len(steps) > 0:
                    self.list_steps.setCurrentRow(len(steps) - 1)
                self.update_json_preview()

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

        def refresh_list(initial_shells=None):
            list_widget.clear()
            try:
                if initial_shells is not None:
                    curr_shells = initial_shells
                else:
                    res_refresh = requests.get("http://localhost:8082/shell-descriptors", timeout=5)
                    curr_shells = res_refresh.json().get("result", [])
                for s in curr_shells:
                    item = QListWidgetItem(f"{s.get('idShort')} ({s.get('id')})")
                    item.setData(Qt.ItemDataRole.UserRole, s)
                    list_widget.addItem(item)
            except Exception as e:
                QMessageBox.warning(dlg, "Error", f"Failed to refresh list: {e}")

        refresh_list(initial_shells=shells)

        btn_layout = QHBoxLayout()
        btn_clone = QPushButton("Clone & Edit")
        btn_clone.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; min-height: 35px;")
        
        btn_backup = QPushButton("Backup Selected")
        btn_backup.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold; min-height: 35px;")
        
        btn_backup_all = QPushButton("Backup All")
        btn_backup_all.setStyleSheet("background-color: #34495e; color: white; font-weight: bold; min-height: 35px;")
        
        btn_restore = QPushButton("Restore (Upload)")
        btn_restore.setStyleSheet("background-color: #16a085; color: white; font-weight: bold; min-height: 35px;")
        
        btn_delete = QPushButton("Delete AAS")
        btn_delete.setStyleSheet("background-color: #c0392b; color: white; font-weight: bold; min-height: 35px;")
        
        btn_close = QPushButton("Close")
        btn_close.setStyleSheet("min-height: 35px;")

        btn_layout.addWidget(btn_clone)
        btn_layout.addWidget(btn_backup)
        btn_layout.addWidget(btn_backup_all)
        btn_layout.addWidget(btn_restore)
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
                self.delete_aas_by_id(shell_id)
                while QApplication.overrideCursor() is not None:
                    QApplication.restoreOverrideCursor()
                QMessageBox.information(dlg, "Success", f"AAS '{id_short}' and its associated submodels deleted successfully.")
                refresh_list()
            except Exception as e:
                while QApplication.overrideCursor() is not None:
                    QApplication.restoreOverrideCursor()
                traceback.print_exc()
                QMessageBox.critical(dlg, "Error", f"Failed to delete AAS: {e}")
            finally:
                while QApplication.overrideCursor() is not None:
                    QApplication.restoreOverrideCursor()

        def get_backup_data(shell_desc):
            shell_id = shell_desc.get("id")
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
            is_dynamic = False
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
                        elif sel["idShort"] == "DynamicObject" and sel["modelType"] == "Property":
                            is_dynamic = str(sel.get("value", "False")).lower() == "true"

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
                            "active_low": str(params.get("ActiveLow", "False")).lower() == "true",
                            "snap_product": "SnapTarget" in params
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
            return {
                "version": "1.0",
                "kit_name": kit_name,
                "aas_id": shell_desc.get("id", f"https://acplt.org/AAS_{kit_name}"),
                "description": description,
                "config_data": {
                    "kit_name": kit_name,
                    "aas_id": kit_name,
                    "description": description,
                    "dynamic": is_dynamic,
                    "pos": pos_val,
                    "rot": rot_val,
                    "scale": scale_val,
                    "actuators": actuators,
                    "sensors": sensors
                },
                "glb_filename": f"{kit_name}.glb",
                "glb_base64": base64.b64encode(glb_bytes).decode('utf-8')
            }

        def on_backup_clicked():
            item = list_widget.currentItem()
            if not item:
                QMessageBox.warning(dlg, "Warning", "Please select an AAS to backup.")
                return
            shell_desc = item.data(Qt.ItemDataRole.UserRole)
            id_short = shell_desc.get("idShort", "Unknown")

            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            try:
                backup_data = get_backup_data(shell_desc)
                while QApplication.overrideCursor() is not None:
                    QApplication.restoreOverrideCursor()

                save_path, _ = QFileDialog.getSaveFileName(dlg, "Save AAS Backup", f"{id_short}_backup.json", "JSON Files (*.json)")
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

        def on_backup_all_clicked():
            if list_widget.count() == 0:
                QMessageBox.warning(dlg, "Warning", "No active AAS kits to backup.")
                return

            dest_dir = QFileDialog.getExistingDirectory(dlg, "Select Directory to Save Backups")
            if not dest_dir:
                return

            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            success_count = 0
            fail_messages = []
            
            try:
                for i in range(list_widget.count()):
                    item = list_widget.item(i)
                    shell_desc = item.data(Qt.ItemDataRole.UserRole)
                    id_short = shell_desc.get("idShort", f"Kit_{i}")
                    
                    try:
                        backup_data = get_backup_data(shell_desc)
                        save_path = os.path.join(dest_dir, f"{id_short}_backup.json")
                        with open(save_path, "w", encoding="utf-8") as f:
                            json.dump(backup_data, f, indent=2)
                        success_count += 1
                    except Exception as e:
                        fail_messages.append(f"{id_short}: {e}")
                        
                while QApplication.overrideCursor() is not None:
                    QApplication.restoreOverrideCursor()
                
                if success_count > 0:
                    msg = f"Successfully backed up {success_count} kits to:\n{dest_dir}"
                    if fail_messages:
                        msg += "\n\nFailures:\n" + "\n".join(fail_messages)
                    QMessageBox.information(dlg, "Backup All Success", msg)
                else:
                    QMessageBox.warning(dlg, "Backup All Failed", "Failed to backup any kits.\n\nErrors:\n" + "\n".join(fail_messages))
            except Exception as e:
                while QApplication.overrideCursor() is not None:
                    QApplication.restoreOverrideCursor()
                QMessageBox.critical(dlg, "Error", f"An unexpected error occurred during Backup All: {e}")
            finally:
                while QApplication.overrideCursor() is not None:
                    QApplication.restoreOverrideCursor()

        def on_restore_clicked():
            open_paths, _ = QFileDialog.getOpenFileNames(dlg, "Open AAS Backup(s)", "", "JSON Files (*.json)")
            if not open_paths:
                return

            def process_backup_file(path):
                with open(path, "r", encoding="utf-8") as f:
                    b_data = json.load(f)
                
                cfg_data = b_data.get("config_data")
                glb_b64 = b_data.get("glb_base64", "")
                if not cfg_data:
                    raise Exception("Invalid backup file: config_data missing.")
                
                import tempfile
                tp = os.path.join(tempfile.gettempdir(), b_data.get("glb_filename", "restored.glb"))
                glb_bytes = base64.b64decode(glb_b64.encode('utf-8'))
                with open(tp, "wb") as f:
                    f.write(glb_bytes)
                cfg_data["glb_path"] = tp
                return cfg_data

            if len(open_paths) == 1:
                # Single-file restore flow
                path = open_paths[0]
                try:
                    config_data = process_backup_file(path)
                except Exception as e:
                    QMessageBox.critical(dlg, "Error", f"Failed to parse backup file: {e}")
                    return

                reply = QMessageBox.question(
                    dlg, "Restore Options",
                    "Would you like to load this backup into the Wizard for editing (Yes) or deploy it directly to the server (No)?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
                )
                if reply == QMessageBox.StandardButton.Cancel:
                    return

                if reply == QMessageBox.StandardButton.Yes:
                    self.restore_wizard_state(config_data)
                    dlg.accept()
                    QMessageBox.information(self, "Success", "Backup loaded into Wizard successfully.")
                else:
                    QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                    try:
                        curr_state = self.save_wizard_state()
                        self.restore_wizard_state(config_data)
                        self.deploy_to_aas()
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
            else:
                # Multiple-file restore flow: deploy directly to server
                reply = QMessageBox.question(
                    dlg, "Restore Multiple Backups",
                    f"You have selected {len(open_paths)} backup files. These will be deployed directly to the BaSyx server. Do you want to proceed?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return

                QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                success_count = 0
                fail_messages = []
                curr_state = self.save_wizard_state()
                
                try:
                    for path in open_paths:
                        fn = os.path.basename(path)
                        try:
                            config_data = process_backup_file(path)
                            self.restore_wizard_state(config_data)
                            self.deploy_to_aas()
                            success_count += 1
                        except Exception as e:
                            fail_messages.append(f"{fn}: {e}")
                    
                    self.restore_wizard_state(curr_state)
                    
                    while QApplication.overrideCursor() is not None:
                        QApplication.restoreOverrideCursor()

                    if success_count > 0:
                        msg = f"Successfully deployed {success_count} backups directly to BaSyx!"
                        if fail_messages:
                            msg += "\n\nFailures:\n" + "\n".join(fail_messages)
                        QMessageBox.information(dlg, "Restore Multiple Success", msg)
                        refresh_list()
                    else:
                        QMessageBox.warning(dlg, "Restore Multiple Failed", "Failed to restore any backups.\n\nErrors:\n" + "\n".join(fail_messages))
                except Exception as e:
                    self.restore_wizard_state(curr_state)
                    while QApplication.overrideCursor() is not None:
                        QApplication.restoreOverrideCursor()
                    QMessageBox.critical(dlg, "Error", f"An unexpected error occurred during restore: {e}")
                finally:
                    while QApplication.overrideCursor() is not None:
                        QApplication.restoreOverrideCursor()

        btn_clone.clicked.connect(on_clone_clicked)
        btn_backup.clicked.connect(on_backup_clicked)
        btn_backup_all.clicked.connect(on_backup_all_clicked)
        btn_restore.clicked.connect(on_restore_clicked)
        btn_delete.clicked.connect(on_delete_clicked)
        btn_close.clicked.connect(dlg.reject)

        dlg.exec()

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
        self.plotter.enable_eye_dome_lighting()
        self.plotter.enable_shadows()
        self.kill_overlays()
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

                beh_data = next((v for k,v in submodels_data.items() if "BehaviorMapping" in k or "Behavior" in k), None)
                hidden_nodes = set()
                if beh_data:
                    act_types = ["Conveyor", "RotateContinuous", "TranslateContinuous", "Piston", "Linear"]
                    sens_types = ["TriggerZone", "Presence", "Proximity"]
                    for el in beh_data.get("submodelElements", []):
                        if el["modelType"] == "SubmodelElementCollection":
                            props = {p["idShort"]: p.get("value") for p in el.get("value", []) if p["modelType"] == "Property"}
                            params = {}
                            for p in el.get("value", []):
                                if p["idShort"] == "Parameters":
                                    params = {pp["idShort"]: pp.get("value") for pp in p.get("value", []) if pp["modelType"] == "Property"}
                            b_type = props.get("Type", "")
                            node = props.get("Component", "")
                            if b_type in act_types:
                                visible = str(params.get("Visible", "True")).lower() == "true"
                                if not visible and node: hidden_nodes.add(node)
                            elif b_type in sens_types:
                                visible = str(params.get("Visible", "False")).lower() == "true"
                                if not visible and node: hidden_nodes.add(node)

                # Parse transform
                pos_val = [0.0]*3; rot_val = [0.0]*3; scale_val = [1.0]*3
                mesh_href = None
                coll_id_short = None
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
                        
                        # Load geometry
                        scene = trimesh.load(tp, process=False)
                        
                        # Build transformation matrix M = T * R * S
                        T = tf.translation_matrix(pos_val)
                        R = tf.euler_matrix(np.radians(rot_val[0]), np.radians(rot_val[1]), np.radians(rot_val[2]), 'sxyz')
                        S = np.diag([scale_val[0], scale_val[1], scale_val[2], 1.0])
                        M = tf.concatenate_matrices(T, R, S)
                        
                        if isinstance(scene, trimesh.Scene):
                            # Gather material metadata
                            geo_mats = {}
                            for gn, mesh in scene.geometry.items():
                                tx = None; cl = None; mt = 0.0; rg = 0.5
                                if hasattr(mesh, 'visual') and hasattr(mesh.visual, 'material'):
                                    mat = mesh.visual.material; img = getattr(mat, 'image', getattr(mat, 'baseColorTexture', None))
                                    if img:
                                        try: tx = pv.Texture(np.array(img))
                                        except: pass
                                    if hasattr(mat, 'baseColorFactor') and mat.baseColorFactor is not None:
                                        cl = mat.baseColorFactor[:3]
                                    mt = getattr(mat, 'metallicFactor', 0.0)
                                    rg = getattr(mat, 'roughnessFactor', 0.5)
                                geo_mats[gn] = (tx, cl, mt, rg)
                            
                            # Recursively add nodes with graph transforms + global matrix
                            root_nodes = [node for node in scene.graph.nodes if scene.graph.transforms.parents.get(node) is None]
                            
                            def is_hidden(node):
                                curr = node
                                while curr is not None:
                                    if curr in hidden_nodes:
                                        return True
                                    curr = scene.graph.transforms.parents.get(curr)
                                return False

                            def add_preview_node(node):
                                if node in scene.graph.nodes_geometry:
                                    if not is_hidden(node):
                                        node_tf, gn = scene.graph[node]
                                        mi = scene.geometry[gn].copy()
                                        combined_tf = M @ node_tf
                                        mi.apply_transform(combined_tf)
                                        pm = pv.wrap(mi)
                                        tx, cl, mt, rg = geo_mats.get(gn, (None, None, 0.0, 0.5))
                                        self.plotter.add_mesh(pm, texture=tx, color=cl if not tx else None, smooth_shading=True, pbr=True, metallic=mt, roughness=rg)
                                for c in scene.graph.transforms.children.get(node, []):
                                    add_preview_node(c)
                                    
                            for r in root_nodes:
                                add_preview_node(r)
                        elif isinstance(scene, trimesh.Trimesh):
                            pm = pv.wrap(scene)
                            pm.transform(M)
                            self.plotter.add_mesh(pm, pbr=True)
                        
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

    def load_cloned_aas(self, shell_desc):
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            shell_id = shell_desc.get("id")
            encoded_shell_id = base64.urlsafe_b64encode(shell_id.encode()).decode().rstrip("=")
            
            # Fetch the actual shell from the repository
            shell_res = requests.get(f"http://localhost:8081/shells/{encoded_shell_id}", timeout=5)
            if shell_res.status_code != 200: raise Exception(f"Failed to fetch Shell from repository (Code {shell_res.status_code})")
            shell_data = shell_res.json()
            
            # Extract Submodel References directly from the Shell
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

            # Look for submodels by parsing the actual Submodel IDs/data we just fetched
            # We don't rely on 'GeometryData' strictly; we look for anything that looks like VisualStructure
            vis_data = next((v for k,v in submodels_data.items() if "VisualStructure" in k or "Visual" in k), None)
            beh_data = next((v for k,v in submodels_data.items() if "BehaviorMapping" in k or "Behavior" in k), None)
            
            if not all([vis_data, beh_data]): raise Exception(f"AAS is missing required Kit submodels. Found: {list(submodels_data.keys())}")
                
            # Basic Info
            self.edit_kit_name.setText(shell_desc.get("idShort", "ClonedKit"))
            self.edit_aas_id.setText(shell_desc.get("idShort", "ClonedKit"))
            
            # Fetch description from configuration if available
            desc = ""
            if "KitConfiguration" in submodels_data:
                cfg = submodels_data["KitConfiguration"]
                for el in cfg.get("submodelElements", []):
                    if el["idShort"] == "Description":
                        desc = el.get("value", "")
            self.edit_desc.setText(desc)
            
            # Transform & Mesh
            mesh_href = None
            for el in vis_data.get("submodelElements", []):
                if el["modelType"] == "SubmodelElementCollection": 
                    for sel in el.get("value", []):
                        if sel["idShort"] == "Transform":
                            for t in sel.get("value", []):
                                v = float(t.get("value", 0))
                                if t["idShort"] == "PosX": self.sys_pos[0].setValue(v)
                                elif t["idShort"] == "PosY": self.sys_pos[1].setValue(v)
                                elif t["idShort"] == "PosZ": self.sys_pos[2].setValue(v)
                                elif t["idShort"] == "RotX": self.sys_rot[0].setValue(v)
                                elif t["idShort"] == "RotY": self.sys_rot[1].setValue(v)
                                elif t["idShort"] == "RotZ": self.sys_rot[2].setValue(v)
                                elif t["idShort"] == "ScaleX": self.sys_scale[0].setValue(v)
                                elif t["idShort"] == "ScaleY": self.sys_scale[1].setValue(v)
                                elif t["idShort"] == "ScaleZ": self.sys_scale[2].setValue(v)
                        elif sel["idShort"] == "Mesh" and sel["modelType"] == "File":
                            mesh_href = sel.get("value")
                        elif sel["idShort"] == "DynamicObject" and sel["modelType"] == "Property":
                            is_dyn = str(sel.get("value", "False")).lower() == "true"
                            self.check_is_dynamic.setChecked(is_dyn)

            # Behavior
            for w in list(self.actuator_widgets): self.remove_actuator(w)
            for w in list(self.sensor_widgets): self.remove_sensor(w)
            
            act_types = ["Conveyor", "RotateContinuous", "TranslateContinuous", "Piston", "Linear"]
            sens_types = ["TriggerZone", "Presence", "Proximity"]
            
            for el in beh_data.get("submodelElements", []):
                if el["modelType"] == "SubmodelElementCollection":
                    props = {p["idShort"]: p.get("value") for p in el.get("value", []) if p["modelType"] == "Property"}
                    params = {}
                    for p in el.get("value", []):
                        if p["idShort"] == "Parameters": params = {pp["idShort"]: pp.get("value") for pp in p.get("value", []) if pp["modelType"] == "Property"}
                            
                    b_type = props.get("Type", ""); pin_id = props.get("PinID", ""); node = props.get("Component", "")
                    
                    if b_type in act_types:
                        self.add_actuator(); w = self.actuator_widgets[-1]
                        w.edit_pin.setText(pin_id); w.edit_node.setText(node); w.combo_behavior.setCurrentText(b_type)
                        w.spin_x.setValue(float(params.get("AxisX", 0))); w.spin_y.setValue(float(params.get("AxisY", 0))); w.spin_z.setValue(float(params.get("AxisZ", 0)))
                        w.spin_speed.setValue(float(params.get("Speed", 1.0))); w.check_visible.setChecked(str(params.get("Visible", "True")).lower() == "true")
                        if "StopSensorComponent" in params: w.combo_stop_sens.setCurrentText(params["StopSensorComponent"])
                    elif b_type in sens_types:
                        self.add_sensor(); w = self.sensor_widgets[-1]
                        w.edit_pin.setText(pin_id); w.edit_node.setText(node); w.combo_behavior.setCurrentText(b_type)
                        w.edit_filter.setText(params.get("TargetFilter", "Metal"))
                        w.check_visible.setChecked(str(params.get("Visible", "False")).lower() == "true")
                        w.check_active_low.setChecked(str(params.get("ActiveLow", "False")).lower() == "true")
                        w.check_snap.setChecked("SnapTarget" in params)
            self.update_all_actuator_dropdowns()
            
            # Mesh Download
            if mesh_href:
                # the href is typically a base64 encoded endpoint in basyx, or direct url
                # since we know the visual structure id, we can reconstruct the API call to get the attachment
                vis_id = vis_data.get("id")
                encoded_vis_id = base64.urlsafe_b64encode(vis_id.encode()).decode().rstrip("=")
                
                # Find the collection that has the Mesh
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
                        import tempfile
                        tp = os.path.join(tempfile.gettempdir(), f"{shell_desc['idShort']}_cloned.glb")
                        with open(tp, "wb") as f: f.write(m_res.content)
                        self.glb_path = tp; self.lbl_glb_path.setText(f"[Cloned] {shell_desc['idShort']}.glb"); self.load_model(tp)

            self.stack.setCurrentIndex(1); self.update_nav()
            while QApplication.overrideCursor() is not None:
                QApplication.restoreOverrideCursor()
            QMessageBox.information(self, "Success", "AAS Cloned successfully! You can now edit and deploy as a new Kit.")
        except Exception as e:
            while QApplication.overrideCursor() is not None:
                QApplication.restoreOverrideCursor()
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to clone AAS: {e}")
        finally:
            while QApplication.overrideCursor() is not None: QApplication.restoreOverrideCursor()

    def save_wizard_state(self):
        return {
            "kit_name": self.edit_kit_name.text(),
            "aas_id": self.edit_aas_id.text(),
            "description": self.edit_desc.text(),
            "dynamic": self.check_is_dynamic.isChecked(),
            "glb_path": self.glb_path,
            "pos": [self.sys_pos[i].value() for i in range(3)],
            "rot": [self.sys_rot[i].value() for i in range(3)],
            "scale": [self.sys_scale[i].value() for i in range(3)],
            "actuators": [w.get_data() for w in self.actuator_widgets],
            "sensors": [w.get_data() for w in self.sensor_widgets],
            "control_logic": self.logic_rules
        }

    def restore_wizard_state(self, state, config_dir=None):
        self.glb_path = state.get("glb_path")
        
        components = state.get("components", [])
        if components:
            comp = components[0]
            pos = comp.get("position", [0.0, 0.0, 0.0])
            rot = comp.get("rotation", [0.0, 0.0, 0.0])
            scale = comp.get("scale", [1.0, 1.0, 1.0])
            is_dynamic = comp.get("dynamic", state.get("dynamic", False))
            actuators = comp.get("actuators", [])
            sensors = comp.get("sensors", [])
            mesh_name = comp.get("mesh")
            if mesh_name and not self.glb_path:
                if config_dir:
                    candidate = os.path.join(config_dir, mesh_name)
                    if os.path.exists(candidate):
                        self.glb_path = candidate
                if not self.glb_path and os.path.exists(mesh_name):
                    self.glb_path = os.path.abspath(mesh_name)
        else:
            pos = state.get("pos", state.get("position", [0.0, 0.0, 0.0]))
            rot = state.get("rot", state.get("rotation", [0.0, 0.0, 0.0]))
            scale = state.get("scale", [1.0, 1.0, 1.0])
            is_dynamic = state.get("dynamic", False)
            actuators = state.get("actuators", [])
            sensors = state.get("sensors", [])

        self.lbl_glb_path.setText(os.path.basename(self.glb_path) if self.glb_path else "No file selected")
        if self.glb_path and os.path.exists(self.glb_path):
            self.load_model(self.glb_path)

        self.edit_kit_name.setText(state.get("kit_name", ""))
        self.edit_aas_id.setText(state.get("aas_id", ""))
        self.edit_desc.setText(state.get("description", ""))
        self.check_is_dynamic.setChecked(is_dynamic)

        for i in range(3):
            self.sys_pos[i].setValue(pos[i])
            self.sys_rot[i].setValue(rot[i])
            self.sys_scale[i].setValue(scale[i])
            
        for w in list(self.actuator_widgets): self.remove_actuator(w)
        for w in list(self.sensor_widgets): self.remove_sensor(w)
        
        for act in actuators:
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
            
        for sns in sensors:
            self.add_sensor(); w = self.sensor_widgets[-1]
            w.edit_pin.setText(sns.get("pin_id", ""))
            w.edit_node.setText(sns.get("node", ""))
            w.combo_behavior.setCurrentText(sns.get("behavior", ""))
            w.edit_filter.setText(sns.get("target_filter", "Metal"))
            w.check_visible.setChecked(sns.get("visible", False))
            w.check_active_low.setChecked(sns.get("active_low", False))
            w.check_snap.setChecked(sns.get("snap_product", False))
            
        self.update_all_actuator_dropdowns()

        for i, act in enumerate(actuators):
            if i < len(self.actuator_widgets) and "stop_sensor" in act:
                self.actuator_widgets[i].combo_stop_sens.setCurrentText(act["stop_sensor"])

        # Restore logic rules
        self.logic_rules = state.get("control_logic", {"start": [], "sequences": []})
        self.list_sequences.blockSignals(True)
        self.list_sequences.clear()
        self.list_sequences.addItem("Start Sequence")
        for seq in self.logic_rules.get("sequences", []):
            self.list_sequences.addItem(seq.get("name", "Custom Sequence"))
        self.list_sequences.setCurrentRow(0)
        self.list_sequences.blockSignals(False)
        self.on_sequence_selected(0)

    def reset_wizard(self):
        # 1. Clear GLB model path
        self.glb_path = None
        self.lbl_glb_path.setText("No file selected")
        
        # 2. Reset text fields
        self.edit_kit_name.setText("ConveyorKit")
        self.edit_aas_id.setText("Conveyor_01")
        self.edit_desc.setText("Standard Conveyor System")
        self.check_is_dynamic.setChecked(False)
        
        # 3. Reset transforms
        for i in range(3):
            self.sys_pos[i].setValue(0.0)
            self.sys_rot[i].setValue(0.0)
            self.sys_scale[i].setValue(1.0)
            
        # 4. Remove all actuators and sensors
        for w in list(self.actuator_widgets):
            self.remove_actuator(w)
        for w in list(self.sensor_widgets):
            self.remove_sensor(w)
            
        # 5. Clear plotter and node tree
        self.plotter.clear()
        self.node_tree.clear()
        self.meshes = {}
        self.actors = {}
        
        # Reset control logic
        self.logic_rules = {"start": [], "sequences": []}
        self.list_sequences.blockSignals(True)
        self.list_sequences.clear()
        self.list_sequences.addItem("Start Sequence")
        self.list_sequences.setCurrentRow(0)
        self.list_sequences.blockSignals(False)
        self.on_sequence_selected(0)

        # 6. Update UI
        self.update_validation_ui()

    def delete_aas_by_id(self, shell_id):
        encoded_shell_id = base64.urlsafe_b64encode(shell_id.encode()).decode().rstrip("=")
        def checked_delete(url):
            r = requests.delete(url, timeout=5)
            if r.status_code not in [200, 204, 404]:
                raise Exception(f"Delete failed with status {r.status_code} for {url}")

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
                    checked_delete(f"http://localhost:8081/submodels/{encoded_sm_id}")
                    # Delete from registry
                    checked_delete(f"http://localhost:8083/submodel-descriptors/{encoded_sm_id}")
        
        # Delete shell from repository
        checked_delete(f"http://localhost:8081/shells/{encoded_shell_id}")
        
        # Delete shell descriptor from registry
        checked_delete(f"http://localhost:8082/shell-descriptors/{encoded_shell_id}")

    def update_validation_ui(self):
        valid_aas = is_valid_aas_id(self.edit_aas_id.text())
        self.edit_aas_id.setStyleSheet(VALID_STYLE if valid_aas else ERROR_STYLE)
        overall_valid = valid_aas
        for w in self.actuator_widgets + self.sensor_widgets:
            if not is_valid_aas_id(w.edit_pin.text()): overall_valid = False; break
        self.lbl_global_error.setVisible(not overall_valid)
        self.btn_next.setEnabled(overall_valid)

    def add_actuator(self):
        w = ActuatorWidget(self); self.actuator_widgets.append(w); self.act_layout.addWidget(w); w.activate()
    def remove_actuator(self, w):
        if w.arrow: self.plotter.remove_actor(w.arrow)
        self.actuator_widgets.remove(w); w.deleteLater(); self.current_config_widget = None; self.update_validation_ui()
    def add_sensor(self):
        w = SensorWidget(self); self.sensor_widgets.append(w); self.sens_layout.addWidget(w); self.update_all_actuator_dropdowns(); w.activate()
    def remove_sensor(self, w):
        self.sensor_widgets.remove(w); w.deleteLater(); self.current_config_widget = None; self.update_all_actuator_dropdowns(); self.update_validation_ui()

    def update_all_actuator_dropdowns(self):
        for aw in self.actuator_widgets: aw.update_stop_sensors()

    def on_mesh_picked(self, mesh):
        for n, m in self.meshes.items():
            if m == mesh:
                self.select_node(n)
                if self.current_config_widget: self.current_config_widget.set_node(n)
                break

    def on_tree_item_clicked(self, it, col):
        name = it.text(0)
        self.select_node(name)
        if self.current_config_widget: self.current_config_widget.set_node(name)

    def select_node(self, n):
        family = self.get_node_family(n)
        for name, actor in self.actors.items(): actor.prop.opacity = 1.0 if name in family else 0.15

    def get_node_family(self, name):
        f = {name}
        if hasattr(self, 'scene_graph'):
            for c in self.scene_graph.transforms.children.get(name, []): f.update(self.get_node_family(c))
        return f
    def browse_glb(self):
        p, _ = QFileDialog.getOpenFileName(self, "Select GLB", "", "GLB Files (*.glb)")
        if p: 
            self.glb_path = p; self.lbl_glb_path.setText(os.path.basename(p)); self.load_model(p)
            
    def load_model(self, path):
        self.plotter.clear(); self.meshes = {}; self.actors = {}; self.node_tree.clear(); self.plotter.camera.up = (0, 1, 0)
        self.plotter.enable_eye_dome_lighting(); self.plotter.enable_shadows()
        self.kill_overlays()
        try:
            scene = trimesh.load(path, process=False)
            if isinstance(scene, trimesh.Scene):
                self.scene_graph = scene.graph; geo_mats = {}
                for gn, mesh in scene.geometry.items():
                    tx = None; cl = None; mt = 0.0; rg = 0.5
                    if hasattr(mesh, 'visual') and hasattr(mesh.visual, 'material'):
                        mat = mesh.visual.material; img = getattr(mat, 'image', getattr(mat, 'baseColorTexture', None))
                        if img:
                            try: tx = pv.Texture(np.array(img))
                            except: pass
                        if hasattr(mat, 'baseColorFactor') and mat.baseColorFactor is not None: cl = mat.baseColorFactor[:3]
                        mt = getattr(mat, 'metallicFactor', 0.0); rg = getattr(mat, 'roughnessFactor', 0.5)
                    geo_mats[gn] = (tx, cl, mt, rg)
                root_nodes = [n for n in scene.graph.nodes if scene.graph.transforms.parents.get(n) is None]
                for r in root_nodes: self.add_tree_node(r, None, scene, geo_mats)
            else:
                pm = pv.wrap(scene); self.meshes["Main"] = pm; self.actors["Main"] = self.plotter.add_mesh(pm, name="Main", pbr=True); QTreeWidgetItem(self.node_tree, ["Main"])
            self.plotter.reset_camera(); self.plotter.add_axes()
        except Exception as e: QMessageBox.critical(self, "Error", str(e)); traceback.print_exc()

    def add_tree_node(self, n, pi, scene, gm):
        it = QTreeWidgetItem(pi or self.node_tree, [n])
        if n in scene.graph.nodes_geometry:
            tf, gn = scene.graph[n]; mi = scene.geometry[gn].copy(); mi.apply_transform(tf); pm = pv.wrap(mi); self.meshes[n] = pm
            tx, cl, mt, rg = gm.get(gn, (None, None, 0.0, 0.5))
            ac = self.plotter.add_mesh(pm, name=n, texture=tx, color=cl if not tx else None, smooth_shading=True, pbr=True, metallic=mt, roughness=rg)
            self.actors[n] = ac; it.setForeground(0, QColor("#007acc"))
        for c in scene.graph.transforms.children.get(n, []): self.add_tree_node(c, it, scene, gm)
        if pi is None: it.setExpanded(True)

    def next_step(self):
        idx = self.stack.currentIndex()
        if idx < self.stack.count() - 1: self.stack.setCurrentIndex(idx + 1); self.update_nav()
        else: self.deploy_to_aas()
    def prev_step(self):
        idx = self.stack.currentIndex(); self.stack.setCurrentIndex(idx - 1); self.update_nav()
    def update_nav(self):
        idx = self.stack.currentIndex(); self.btn_prev.setEnabled(idx > 0)
        titles = ["Model Selection", "Basic Info & Transform", "Configure Sensors", "Configure Actuators", "Control Logic", "Review & Deploy"]
        self.step_label.setText(f"Step {idx+1} of 6: {titles[idx]}")
        if idx != 5:
            for w in self.actuator_widgets:
                if w.arrow: self.plotter.remove_actor(w.arrow); w.arrow = None
        elif idx == 5:
            for w in self.actuator_widgets: w.update_visuals()
            
        if idx == 4:
            self.refresh_logic_dropdowns()
            
        self.btn_next.setText("Deploy to AAS" if idx == self.stack.count() - 1 else "Next →"); self.update_json_preview()
            
    def update_json_preview(self):
        self.config_data = {
            "kit_name": self.edit_kit_name.text(),
            "aas_id": self.edit_aas_id.text(),
            "description": self.edit_desc.text(),
            "control_logic": self.logic_rules
        }
        
        comp_name = "Product_ConveyorSystem" if self.check_is_dynamic.isChecked() else "ConveyorSystem"
        comp = {
            "name": comp_name,
            "mesh": os.path.basename(self.glb_path) if self.glb_path else "",
            "parent": None,
            "position": [s.value() for s in self.sys_pos],
            "rotation": [s.value() for s in self.sys_rot],
            "scale": [s.value() for s in self.sys_scale],
            "dynamic": self.check_is_dynamic.isChecked(),
            "actuators": [w.get_data() for w in self.actuator_widgets],
            "sensors": [w.get_data() for w in self.sensor_widgets]
        }
        self.config_data["components"] = [comp]
        self.json_preview.setText(json.dumps(self.config_data, indent=2))

    def deploy_to_aas(self):
        self.update_json_preview()
        if not self.glb_path: return QMessageBox.warning(self, "Error", "Select model.")
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.btn_next.setEnabled(False); self.btn_next.setText("Deploying...")
        try:
            kn = self.edit_kit_name.text(); aid = self.edit_aas_id.text(); kfn = sanitize_aas_id(kn)
            shell = model.AssetAdministrationShell(asset_information=model.AssetInformation(asset_kind=model.AssetKind.INSTANCE, global_asset_id=f"http://acplt.org/Assets/{kfn}"), id_=f"https://acplt.org/AAS_{kfn}", id_short=aid)
            vs = model.Submodel(id_=f"https://acplt.org/Submodels/Visual_{kfn}", id_short="VisualStructure")
            vp = model.Submodel(id_=f"https://acplt.org/Submodels/Pins_{kfn}", id_short="VirtualPins")
            bm = model.Submodel(id_=f"https://acplt.org/Submodels/Behavior_{kfn}", id_short="BehaviorMapping")
            ic = model.SubmodelElementCollection(id_short="Inputs"); oc = model.SubmodelElementCollection(id_short="Outputs")
            vp.submodel_element.add(ic); vp.submodel_element.add(oc)
            for c in self.config_data["components"]:
                cc = model.SubmodelElementCollection(id_short=sanitize_aas_id(c["name"])); mf = c.get("mesh", "")
                if mf: cc.value.add(model.File(id_short="Mesh", content_type="application/octet-stream", value=mf))
                cc.value.add(model.Property(id_short="Parent", value_type=model.datatypes.String, value=c.get("parent", "")))
                is_prod = c.get("dynamic", False) or (c["name"] == "Product_ConveyorSystem") or self.check_is_dynamic.isChecked()
                cc.value.add(model.Property(id_short="DynamicObject", value_type=model.datatypes.Boolean, value=is_prod))
                tc = model.SubmodelElementCollection(id_short="Transform"); ps = c.get("position", [0,0,0]); rt = c.get("rotation", [0,0,0]); sc = c.get("scale", [1,1,1])
                for i, a in enumerate(["X", "Y", "Z"]): tc.value.add(model.Property(id_short=f"Pos{a}", value_type=model.datatypes.Double, value=float(ps[i])))
                for i, a in enumerate(["X", "Y", "Z"]): tc.value.add(model.Property(id_short=f"Rot{a}", value_type=model.datatypes.Double, value=float(rt[i])))
                for i, a in enumerate(["X", "Y", "Z"]): tc.value.add(model.Property(id_short=f"Scale{a}", value_type=model.datatypes.Double, value=float(sc[i])))
                cc.value.add(tc); vs.submodel_element.add(cc)
                for act in c.get("actuators", []):
                    pid = act["pin_id"]; tco = act.get("node", c["name"]); ep = [p.id_short for p in ic.value]
                    safe_pid = sanitize_aas_id(pid)
                    if safe_pid not in ep: ic.value.add(model.Property(id_short=safe_pid, value_type=model.datatypes.Boolean, value=False))
                    bc = model.SubmodelElementCollection(id_short=sanitize_aas_id(f"{pid}_{tco}")); bc.value.add(model.Property(id_short="PinID", value_type=model.datatypes.String, value=pid))
                    bc.value.add(model.Property(id_short="Component", value_type=model.datatypes.String, value=tco)); bc.value.add(model.Property(id_short="Type", value_type=model.datatypes.String, value=act.get("behavior")))
                    pc = model.SubmodelElementCollection(id_short="Parameters")
                    if "axis" in act:
                        for i, a in enumerate(["X", "Y", "Z"]): pc.value.add(model.Property(id_short=f"Axis{a}", value_type=model.datatypes.Double, value=float(act["axis"][i])))
                    if "speed" in act: pc.value.add(model.Property(id_short="Speed", value_type=model.datatypes.Double, value=float(act["speed"])))
                    if "visible" in act: pc.value.add(model.Property(id_short="Visible", value_type=model.datatypes.Boolean, value=bool(act["visible"])))
                    if "stop_sensor" in act and act["stop_sensor"]: pc.value.add(model.Property(id_short="StopSensorComponent", value_type=model.datatypes.String, value=act["stop_sensor"]))
                    bc.value.add(pc); bm.submodel_element.add(bc)
                for sns in c.get("sensors", []):
                    pid = sns["pin_id"]; tco = sns.get("node", c["name"]); ep = [p.id_short for p in oc.value]; safe_pid = sanitize_aas_id(pid)
                    if safe_pid not in ep: oc.value.add(model.Property(id_short=safe_pid, value_type=model.datatypes.Boolean, value=False))
                    bc = model.SubmodelElementCollection(id_short=sanitize_aas_id(f"{pid}_{tco}")); bc.value.add(model.Property(id_short="PinID", value_type=model.datatypes.String, value=pid)); bc.value.add(model.Property(id_short="Component", value_type=model.datatypes.String, value=tco)); bc.value.add(model.Property(id_short="Type", value_type=model.datatypes.String, value=sns.get("behavior")))
                    pc = model.SubmodelElementCollection(id_short="Parameters")
                    if "target_filter" in sns: pc.value.add(model.Property(id_short="TargetFilter", value_type=model.datatypes.String, value=sns["target_filter"]))
                    if "visible" in sns: pc.value.add(model.Property(id_short="Visible", value_type=model.datatypes.Boolean, value=bool(sns["visible"])))
                    if "active_low" in sns: pc.value.add(model.Property(id_short="ActiveLow", value_type=model.datatypes.Boolean, value=bool(sns["active_low"])))
                    if sns.get("snap_product"): pc.value.add(model.Property(id_short="SnapTarget", value_type=model.datatypes.String, value="Product_ConveyorSystem"))
                    bc.value.add(pc); bm.submodel_element.add(bc)
            shell.submodel.add(model.ModelReference.from_referable(vs)); shell.submodel.add(model.ModelReference.from_referable(vp)); shell.submodel.add(model.ModelReference.from_referable(bm))
            obj_store = model.DictObjectStore(); obj_store.add(shell); obj_store.add(vs); obj_store.add(vp); obj_store.add(bm); fr = RobustFileRepo()
            import tempfile
            import time
            bd = os.path.dirname(self.glb_path)
            ae = ['.obj', '.mtl', '.stl', '.png', '.jpg', '.jpeg', '.dae', '.fbx', '.glb', '.gltf', '.bin']
            is_temp_dir = os.path.abspath(bd) == os.path.abspath(tempfile.gettempdir())
            
            if is_temp_dir:
                fn = os.path.basename(self.glb_path)
                with open(self.glb_path, 'rb') as tf:
                    co = tf.read()
                ap = posixpath.normpath(posixpath.join("/aasx/kit", fn))
                fr.add_file(ap, co)
            else:
                for r, d, fs in os.walk(bd):
                    for f in fs:
                        if any(f.lower().endswith(ext) for ext in ae):
                            lp = os.path.join(r, f); rp = os.path.relpath(lp, bd).replace("\\", "/")
                            with open(lp, 'rb') as tf:
                                co = tf.read()
                            ap = posixpath.normpath(posixpath.join("/aasx/kit", rp)); fr.add_file(ap, co)
            for sm in [vs, vp, bm]:
                for el in sm.submodel_element:
                    if isinstance(el, model.File) and el.value and not el.value.startswith("/aasx/"): el.value = posixpath.normpath(posixpath.join("/aasx/kit", el.value))
                    elif isinstance(el, model.SubmodelElementCollection):
                        for se in el.value:
                            if isinstance(se, model.File) and se.value and not se.value.startswith("/aasx/"): se.value = posixpath.normpath(posixpath.join("/aasx/kit", se.value))
            os.makedirs("aasx_packages", exist_ok=True); out = os.path.join("aasx_packages", f"{kfn}_Kit.aasx")
            with aasx.AASXWriter(out) as w: w.write_aas(shell.id, obj_store, fr, aid)
            with open(out, 'rb') as f: res = requests.post("http://localhost:8081/upload", files={'file': (os.path.basename(out), f, 'application/octet-stream')}, timeout=10)
            
            is_conflict = False
            if res.status_code == 409:
                is_conflict = True
            elif "Duplicate element id detected" in res.text or "CollidingIdentifierException" in res.text:
                is_conflict = True
 
            if is_conflict:
                while QApplication.overrideCursor() is not None:
                    QApplication.restoreOverrideCursor()
                reply = QMessageBox.question(
                    self, "AAS Already Exists",
                    f"An AAS with ID '{shell.id}' already exists. Would you like to overwrite it?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                    # Delete the existing AAS
                    self.delete_aas_by_id(shell.id)
                    time.sleep(0.5)  # Wait for BaSyx database to complete deletion & release file locks
                    # Retry upload
                    with open(out, 'rb') as f:
                        res = requests.post("http://localhost:8081/upload", files={'file': (os.path.basename(out), f, 'application/octet-stream')}, timeout=10)
                    if res.status_code in [200, 201, 204]:
                        requests.post("http://localhost:8082/shell-descriptors", json={"id": shell.id, "idShort": shell.id_short, "assetKind": "Instance", "globalAssetId": shell.asset_information.global_asset_id, "submodelDescriptors": [{"idShort": s.id_short, "id": s.id, "endpoints": [{"interface": "SUBMODEL-3.0", "protocolInformation": {"href": f"http://localhost:8081/submodels/{s.id}", "endpointProtocol": "HTTP"}}]} for s in [vs, vp, bm]], "endpoints": [{"interface": "AAS-3.0", "protocolInformation": {"href": f"http://localhost:8081/shells/{shell.id}", "endpointProtocol": "HTTP"}}]}, timeout=10)
                        while QApplication.overrideCursor() is not None:
                            QApplication.restoreOverrideCursor()
                        QMessageBox.information(self, "Success", f"AAS Kit deployed (overwritten) successfully!")
                        self.reset_wizard()
                        self.stack.setCurrentIndex(0)
                        self.update_nav()
                    else:
                        raise Exception(f"Upload failed after overwrite: {res.text}")
                else:
                    return
            elif res.status_code in [200, 201, 204]:
                requests.post("http://localhost:8082/shell-descriptors", json={"id": shell.id, "idShort": shell.id_short, "assetKind": "Instance", "globalAssetId": shell.asset_information.global_asset_id, "submodelDescriptors": [{"idShort": s.id_short, "id": s.id, "endpoints": [{"interface": "SUBMODEL-3.0", "protocolInformation": {"href": f"http://localhost:8081/submodels/{s.id}", "endpointProtocol": "HTTP"}}]} for s in [vs, vp, bm]], "endpoints": [{"interface": "AAS-3.0", "protocolInformation": {"href": f"http://localhost:8081/shells/{shell.id}", "endpointProtocol": "HTTP"}}]}, timeout=10)
                while QApplication.overrideCursor() is not None:
                    QApplication.restoreOverrideCursor()
                QMessageBox.information(self, "Success", f"AAS Kit deployed successfully!")
                self.reset_wizard()
                self.stack.setCurrentIndex(0)
                self.update_nav()
            else: raise Exception(f"Upload failed: {res.text}")
        except Exception as e:
            while QApplication.overrideCursor() is not None:
                QApplication.restoreOverrideCursor()
            traceback.print_exc(); QMessageBox.critical(self, "Error", str(e))
        finally:
            self.btn_next.setEnabled(True); self.btn_next.setText("Deploy to AAS")
            while QApplication.overrideCursor() is not None:
                QApplication.restoreOverrideCursor()

if __name__ == "__main__":
    app = QApplication(sys.argv); window = ConveyorWizard(); window.show(); sys.exit(app.exec())
