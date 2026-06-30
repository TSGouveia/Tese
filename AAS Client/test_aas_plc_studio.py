import unittest
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from aas_plc_studio import AASPLCStudio, RegistryWorker, PinsWorker

# Stub out background workers so they don't start and hang during tests
RegistryWorker.start = lambda self: None
PinsWorker.start = lambda self: None

class TestAASPLCStudio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication(sys.argv)

    def test_always_on_top_toggle(self):
        window = AASPLCStudio()
        try:
            # Verify checkbox exists and is unchecked
            self.assertTrue(hasattr(window, 'chk_always_on_top'))
            self.assertFalse(window.chk_always_on_top.isChecked())
            
            # Toggle always on top ON
            window.chk_always_on_top.setChecked(True)
            self.assertTrue(bool(window.windowFlags() & Qt.WindowType.WindowStaysOnTopHint))
            
            # Toggle always on top OFF
            window.chk_always_on_top.setChecked(False)
            self.assertFalse(bool(window.windowFlags() & Qt.WindowType.WindowStaysOnTopHint))
        finally:
            window.close()

if __name__ == "__main__":
    unittest.main()
