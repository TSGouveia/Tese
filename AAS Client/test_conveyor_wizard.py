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

    def test_aas_generation_and_cloning(self):
        from unittest.mock import patch, MagicMock
        import base64
        window = ConveyorWizard()
        try:
            window.glb_path = "dummy.glb"
            window.edit_kit_name.setText("TestKit")
            window.edit_aas_id.setText("Test_01")
            window.logic_rules = {
                "start": [{"type": "wait_time", "seconds": 2.5}],
                "sequences": [{"name": "Seq1", "trigger": {"operator": "AND", "conditions": []}, "steps": []}]
            }

            # 1. Test deployment (which generates the AASX file and registers descriptors)
            with patch('requests.post') as mock_post, \
                 patch('requests.get') as mock_get, \
                 patch('builtins.open', create=True) as mock_open, \
                 patch('os.walk') as mock_walk, \
                 patch('os.makedirs') as mock_makedirs, \
                 patch('basyx.aas.adapter.aasx.AASXWriter') as mock_writer:
                
                mock_walk.return_value = [("C:\\Users\\LazyT\\Desktop\\Tese\\AAS Client", [], ["dummy.glb"])]
                mock_res = MagicMock()
                mock_res.status_code = 201
                mock_post.return_value = mock_res
                
                window.deploy_to_aas()
                
                self.assertTrue(mock_post.called)
                
            # 2. Test clone parsing (load_cloned_aas)
            shell_desc = {"id": "https://acplt.org/AAS_TestKit", "idShort": "Test_01"}
            
            shell_response = MagicMock()
            shell_response.status_code = 200
            shell_response.json.return_value = {
                "id": "https://acplt.org/AAS_TestKit",
                "idShort": "Test_01",
                "submodels": [
                    {"keys": [{"value": "https://acplt.org/Submodels/Visual_TestKit"}]},
                    {"keys": [{"value": "https://acplt.org/Submodels/Behavior_TestKit"}]},
                    {"keys": [{"value": "https://acplt.org/Submodels/ControlLogic_TestKit"}]}
                ]
            }
            
            vis_sm_response = MagicMock()
            vis_sm_response.status_code = 200
            vis_sm_response.json.return_value = {
                "id": "https://acplt.org/Submodels/Visual_TestKit",
                "idShort": "VisualStructure",
                "submodelElements": []
            }
            
            beh_sm_response = MagicMock()
            beh_sm_response.status_code = 200
            beh_sm_response.json.return_value = {
                "id": "https://acplt.org/Submodels/Behavior_TestKit",
                "idShort": "BehaviorMapping",
                "submodelElements": []
            }
            
            cl_sm_response = MagicMock()
            cl_sm_response.status_code = 200
            cl_sm_response.json.return_value = {
                "id": "https://acplt.org/Submodels/ControlLogic_TestKit",
                "idShort": "ControlLogic",
                "submodelElements": [
                    {
                        "idShort": "Rules",
                        "modelType": "Property",
                        "value": '{"start": [{"type": "wait_time", "seconds": 2.5}], "sequences": [{"name": "Seq1", "trigger": {"operator": "AND", "conditions": []}, "steps": []}]}'
                    }
                ]
            }
            
            def get_side_effect(url, **kwargs):
                if "shells/" in url:
                    return shell_response
                
                def is_encoded_in_url(val):
                    encoded = base64.urlsafe_b64encode(val.encode()).decode().rstrip("=")
                    return encoded in url
                    
                if is_encoded_in_url("https://acplt.org/Submodels/Visual_TestKit"):
                    return vis_sm_response
                elif is_encoded_in_url("https://acplt.org/Submodels/Behavior_TestKit"):
                    return beh_sm_response
                elif is_encoded_in_url("https://acplt.org/Submodels/ControlLogic_TestKit"):
                    return cl_sm_response
                return MagicMock(status_code=404)
                
            with patch('requests.get', side_effect=get_side_effect) as mock_get_clone:
                window.load_cloned_aas(shell_desc)
                
                # Check that logic_rules were successfully parsed from the ControlLogic submodel
                self.assertEqual(window.logic_rules["start"][0]["seconds"], 2.5)
                self.assertEqual(window.logic_rules["sequences"][0]["name"], "Seq1")
                # Check that UI list_sequences is updated
                self.assertEqual(window.list_sequences.count(), 2)
                self.assertEqual(window.list_sequences.item(1).text(), "Seq1")

        finally:
            if hasattr(window, 'plotter'):
                window.plotter.close()
            window.close()

if __name__ == "__main__":
    unittest.main()
