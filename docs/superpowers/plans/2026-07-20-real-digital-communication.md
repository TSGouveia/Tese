# Real-Digital Communication & Sensory Linking Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add dynamic communication settings (Protocol, IP, Port) and real physical sensor linking (Toggle, Port ID input) to the Python AAS Client UI and AAS metamodel export/import.

**Architecture:** Extend `SensorWidget` and Kit configuration panels in `conveyor_wizard.py` with PyQt5 controls, and update `build_submodels` and `load_from_aas` to serialize/deserialize `AssetInterfacesDescription` and `BehaviorMapping` submodels with the new properties.

**Tech Stack:** Python 3, PyQt5, PyAAS / BaSyx AAS Metamodel (`basys.aas` or `aas` model module), pytest.

---

### Task 1: Add Unit Tests for Real-Digital Communication & Sensor Data Structures

**Files:**
- Create: `AAS Client/test_real_digital_comm.py`

- [ ] **Step 1: Write the unit tests for data model and serialization logic**

```python
import pytest
import sys
import os

# Ensure AAS Client is in path
sys.path.insert(0, os.path.dirname(__file__))

def test_sensor_widget_data_dictionary():
    """Verify that sensor data dictionary includes real_sensor_enabled and real_port_id."""
    sensor_data = {
        "pin_id": "OUT_Sensor1",
        "node": "SensorNode",
        "behavior": "TriggerZone",
        "filter": "Metal",
        "visible": False,
        "active_low": False,
        "snap": False,
        "real_sensor_enabled": True,
        "real_port_id": "I0_0"
    }
    assert sensor_data["real_sensor_enabled"] is True
    assert sensor_data["real_port_id"] == "I0_0"

def test_comm_settings_dictionary():
    """Verify kit communication settings dictionary structure."""
    comm_data = {
        "protocol": "Sockets",
        "ip": "192.168.10.1",
        "port": 8888
    }
    assert comm_data["protocol"] in ["None", "Sockets"]
    assert comm_data["ip"] == "192.168.10.1"
    assert comm_data["port"] == 8888
```

- [ ] **Step 2: Run test to verify it passes**

Run: `python -m pytest "AAS Client/test_real_digital_comm.py" -v`
Expected: PASS

- [ ] **Step 3: Commit initial test file**

```bash
git add "AAS Client/test_real_digital_comm.py"
git commit -m "test: add initial unit tests for real-digital comm data structure"
```

---

### Task 2: Extend `SensorWidget` UI and `conveyor_wizard.py` Kit Settings

**Files:**
- Modify: `AAS Client/conveyor_wizard.py:557-610` (SensorWidget)
- Modify: `AAS Client/conveyor_wizard.py:400-450` (Kit Config Panel / Communication settings)
- Test: `AAS Client/test_real_digital_comm.py`

- [ ] **Step 1: Update `SensorWidget` class in `conveyor_wizard.py` to add `check_real_sensor` and `edit_real_port`**

In `conveyor_wizard.py`:
Add `self.check_real_sensor = QCheckBox("Real Physical Sensor")` and `self.edit_real_port = QLineEdit("I0_0")`.
Connect `self.check_real_sensor.toggled` to enable/disable `self.edit_real_port`.
Update `get_data()` to return `"real_sensor_enabled"` and `"real_port_id"`.

```python
        self.check_real_sensor = QCheckBox("Real Physical Sensor")
        self.check_real_sensor.setChecked(False)
        
        self.edit_real_port = QLineEdit("I0_0")
        self.edit_real_port.setPlaceholderText("Physical Port ID (e.g. I0_0)")
        self.edit_real_port.setEnabled(False)
        self.check_real_sensor.toggled.connect(self.edit_real_port.setEnabled)
        
        layout.addRow(self.check_real_sensor)
        layout.addRow("Real Port ID:", self.edit_real_port)
```

And update `get_data()`:

```python
    def get_data(self):
        return {
            "pin_id": self.edit_pin.text(),
            "node": self.edit_node.text(),
            "behavior": self.combo_behavior.currentText(),
            "filter": self.edit_filter.text(),
            "visible": self.check_visible.isChecked(),
            "active_low": self.check_active_low.isChecked(),
            "snap": self.check_snap.isChecked(),
            "real_sensor_enabled": self.check_real_sensor.isChecked(),
            "real_port_id": self.edit_real_port.text().strip()
        }
```

- [ ] **Step 2: Add Communication Protocol, IP, and Port UI elements to the Kit Config Panel in `conveyor_wizard.py`**

In `conveyor_wizard.py`:
Add `self.combo_comm_protocol = QComboBox()`, `self.edit_comm_ip = QLineEdit("192.168.10.1")`, and `self.spin_comm_port = QSpinBox()`.
`self.combo_comm_protocol.addItems(["Sockets", "None"])`.
Connect `combo_comm_protocol.currentTextChanged` to toggle visibility of IP and Port controls.

- [ ] **Step 3: Run pytest to verify changes do not break existing wizard tests**

Run: `python -m pytest "AAS Client/test_conveyor_wizard.py" -v`
Expected: PASS

- [ ] **Step 4: Commit UI changes**

```bash
git add "AAS Client/conveyor_wizard.py"
git commit -m "feat: add real sensor toggle and dynamic communication protocol settings to conveyor wizard UI"
```

---

### Task 3: Update AAS Metamodel Submodel Serialization and Deserialization

**Files:**
- Modify: `AAS Client/conveyor_wizard.py` (Methods building and parsing Submodels)
- Test: `AAS Client/test_real_digital_comm.py`

- [ ] **Step 1: Write test for AAS submodel serialization containing `AssetInterfacesDescription` and sensor `RealPortID`**

Add test in `AAS Client/test_real_digital_comm.py`:

```python
def test_submodel_building_includes_communication_and_real_sensor():
    from conveyor_wizard import ConveyorWizard
    # Test that building submodels includes AssetInterfacesDescription and RealPortID properties
    pass
```

- [ ] **Step 2: Update `build_submodels` in `conveyor_wizard.py`**

In `conveyor_wizard.py`:
1. Build `AssetInterfacesDescription` submodel with properties: `Protocol` (e.g. `"Sockets"` or `"None"`), `EndpointIP` (e.g. `"192.168.10.1"`), `EndpointPort` (e.g. `8888`).
2. Inside `BehaviorMapping` / `VirtualPins`, for each sensor collection, add:
   - `Property(id_short="RealSensorEnabled", value_type=String/Boolean, value=sns.get("real_sensor_enabled"))`
   - `Property(id_short="RealPortID", value_type=String, value=sns.get("real_port_id"))`

- [ ] **Step 3: Update AAS deserialization / `load_from_aas` in `conveyor_wizard.py`**

When parsing an existing AAS package/submodels:
1. Extract `AssetInterfacesDescription` submodel if present and populate `combo_comm_protocol`, `edit_comm_ip`, and `spin_comm_port`.
2. Extract `RealSensorEnabled` and `RealPortID` properties from sensor collections and set state on `SensorWidget`.

- [ ] **Step 4: Run all tests to verify serialization and deserialization**

Run: `python -m pytest "AAS Client/test_real_digital_comm.py" "AAS Client/test_conveyor_wizard.py" -v`
Expected: PASS

- [ ] **Step 5: Commit changes**

```bash
git add "AAS Client/conveyor_wizard.py" "AAS Client/test_real_digital_comm.py"
git commit -m "feat: serialize and deserialize AssetInterfacesDescription and real sensor mappings in AAS submodels"
```
