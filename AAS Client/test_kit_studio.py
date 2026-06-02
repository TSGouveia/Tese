import unittest
import json
import os
import shutil
from kit_studio_manager import KitStudioManager
import basyx.aas.model as model

class TestKitStudioManager(unittest.TestCase):
    def setUp(self):
        self.template_path = os.path.join("AAS_TEMPLATES", "kit_config_template.json")
        with open(self.template_path, "r") as f:
            self.test_json = json.load(f)

    def test_parse_json(self):
        manager = KitStudioManager()
        manager.load_config(self.test_json)
        
        self.assertEqual(manager.kit_name, "SortingStation")
        self.assertEqual(manager.aas_id, "SortingStation_01")
        self.assertEqual(len(manager.components), 3)

        belt = next(c for c in manager.components if c["name"] == "Belt")
        self.assertEqual(belt["parent"], "ConveyorBase")
        self.assertEqual(belt["actuators"][0]["pin_id"], "OUT_Conveyor_Run")

        sensor = next(c for c in manager.components if c["name"] == "PresenceSensor")
        self.assertEqual(sensor["sensors"][0]["behavior"], "TriggerZone")

    def test_generate_aas(self):
        manager = KitStudioManager()
        manager.load_config(self.test_json)
        
        shell, submodels = manager.generate_aas()
        
        self.assertIsInstance(shell, model.AssetAdministrationShell)
        self.assertEqual(shell.id_short, "SortingStation_01")
        
        submodel_ids = [sm.id_short for sm in submodels]
        self.assertIn("VisualStructure", submodel_ids)
        self.assertIn("VirtualPins", submodel_ids)
        self.assertIn("BehaviorMapping", submodel_ids)

        visual_structure = next(sm for sm in submodels if sm.id_short == "VisualStructure")
        belt_collection = next(el for el in visual_structure.submodel_element if el.id_short == "Belt")
        self.assertIsNotNone(belt_collection)
        self.assertEqual(belt_collection.id_short, "Belt")
        self.assertTrue(any(el.id_short == "Mesh" for el in belt_collection.value))
        self.assertTrue(any(el.id_short == "Transform" for el in belt_collection.value))
        self.assertTrue(any(el.id_short == "Parent" for el in belt_collection.value))

        virtual_pins = next(sm for sm in submodels if sm.id_short == "VirtualPins")
        self.assertTrue(any(el.id_short == "Inputs" for el in virtual_pins.submodel_element))
        self.assertTrue(any(el.id_short == "Outputs" for el in virtual_pins.submodel_element))

        behavior_mapping = next(sm for sm in submodels if sm.id_short == "BehaviorMapping")
        conveyor_behavior = next(el for el in behavior_mapping.submodel_element if el.id_short == "OUT_Conveyor_Run")
        self.assertIsNotNone(conveyor_behavior)

if __name__ == "__main__":
    unittest.main()
