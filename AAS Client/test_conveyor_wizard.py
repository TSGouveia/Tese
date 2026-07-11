import unittest
import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Add current directory to path so imports work correctly
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from conveyor_wizard import ConveyorWizard, TriggerRow

class TestConveyorWizard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # We need a QApplication instance to create widgets
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_wizard_init(self):
        window = ConveyorWizard()
        try:
            # Verify stacked widget has 6 pages
            self.assertEqual(window.stack.count(), 6)
            
            # Verify logic_rules structure initialized
            self.assertIn("start", window.logic_rules)
            self.assertIn("sequences", window.logic_rules)
            self.assertEqual(window.logic_rules["start"], [])
            self.assertEqual(window.logic_rules["sequences"], [])
            
            # Verify Sequences List has Start Sequence
            self.assertEqual(window.list_sequences.count(), 1)
            self.assertEqual(window.list_sequences.item(0).text(), "Start Sequence")
        finally:
            if hasattr(window, 'plotter'):
                window.plotter.close()
            window.close()

    def test_sequence_operations(self):
        window = ConveyorWizard()
        try:
            # 1. Add Sequence
            window.logic_rules["sequences"].append({
                "name": "CustomSeq",
                "trigger": {"operator": "AND", "conditions": []},
                "steps": []
            })
            window.list_sequences.addItem("CustomSeq")
            self.assertEqual(window.list_sequences.count(), 2)
            self.assertEqual(window.list_sequences.item(1).text(), "CustomSeq")

            # 2. Select CustomSeq
            window.list_sequences.setCurrentRow(1)
            self.assertFalse(window.group_triggers.isHidden())
            
            # 3. Add Step to CustomSeq
            window.add_set_actuator_step()
            self.assertEqual(len(window.logic_rules["sequences"][0]["steps"]), 1)
            self.assertEqual(window.logic_rules["sequences"][0]["steps"][0]["type"], "set_actuator")
            self.assertEqual(window.list_steps.count(), 1)
            
            # 4. Add Wait Time step
            window.add_wait_time_step()
            self.assertEqual(len(window.logic_rules["sequences"][0]["steps"]), 2)
            self.assertEqual(window.logic_rules["sequences"][0]["steps"][1]["type"], "wait_time")
            self.assertEqual(window.logic_rules["sequences"][0]["steps"][1]["seconds"], 1.0)
            
            # 5. Move step up
            window.list_steps.setCurrentRow(1)
            window.move_step_up()
            # After move up, wait_time should be at index 0, set_actuator at index 1
            self.assertEqual(window.logic_rules["sequences"][0]["steps"][0]["type"], "wait_time")
            self.assertEqual(window.logic_rules["sequences"][0]["steps"][1]["type"], "set_actuator")
            
        finally:
            if hasattr(window, 'plotter'):
                window.plotter.close()
            window.close()

    def test_state_persistence(self):
        window = ConveyorWizard()
        try:
            # Set some rules state
            window.logic_rules = {
                "start": [
                    {"type": "wait_time", "seconds": 2.5}
                ],
                "sequences": [
                    {
                        "name": "TriggerBelt",
                        "trigger": {
                            "operator": "OR",
                            "conditions": [{"sensor": "SensorA", "value": True}]
                        },
                        "steps": [
                            {"type": "set_actuator", "actuator": "BeltMotor", "value": True}
                        ]
                    }
                ]
            }
            
            # Save state
            state = window.save_wizard_state()
            self.assertIn("control_logic", state)
            self.assertEqual(state["control_logic"]["start"][0]["seconds"], 2.5)
            self.assertEqual(state["control_logic"]["sequences"][0]["name"], "TriggerBelt")
            
            # Create a new wizard and restore state
            window2 = ConveyorWizard()
            try:
                window2.restore_wizard_state(state)
                self.assertEqual(len(window2.logic_rules["start"]), 1)
                self.assertEqual(window2.logic_rules["start"][0]["seconds"], 2.5)
                self.assertEqual(window2.logic_rules["sequences"][0]["name"], "TriggerBelt")
                self.assertEqual(window2.list_sequences.count(), 2)
                self.assertEqual(window2.list_sequences.item(1).text(), "TriggerBelt")
            finally:
                if hasattr(window2, 'plotter'):
                    window2.plotter.close()
                window2.close()
        finally:
            if hasattr(window, 'plotter'):
                window.plotter.close()
            window.close()

if __name__ == "__main__":
    unittest.main()
