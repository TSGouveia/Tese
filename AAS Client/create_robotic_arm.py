import sys
import os
import io
import re
import math
import traceback
import collections
import collections.abc
import fractions

# =================================================================
# 1. COMPATIBILITY PATCHES (Immediate)
# =================================================================
def apply_compatibility_patches():
    """Applies patches for Python 3.10+ and older library versions."""
    for name in ['Mapping', 'MutableMapping', 'Set', 'MutableSet', 'Iterable', 'MutableSequence', 'Sequence']:
        if not hasattr(collections, name):
            obj = getattr(collections.abc, name)
            setattr(collections, name, obj)
            if 'collections' in sys.modules:
                setattr(sys.modules['collections'], name, obj)

    if not hasattr(fractions, 'gcd'): fractions.gcd = math.gcd

    try:
        import numpy as np
        np_patches = {'float': float, 'float_': np.float64, 'int': int, 'int_': np.int64, 'bool': bool}
        for old_attr, replacement in np_patches.items():
            if not hasattr(np, old_attr): setattr(np, old_attr, replacement)
    except ImportError: pass

    try:
        import networkx.utils as nx_utils
        import networkx as nx
        nx.utils = nx_utils
        import networkx.algorithms.bipartite
        import networkx.generators.intersection
    except: pass

apply_compatibility_patches()

# GLOBAL APP REFERENCE
_app = None
_splash = None

if __name__ == "__main__":
    # 1. SHOW SPLASH SCREEN AS FAST AS POSSIBLE
    from PyQt6.QtWidgets import QApplication, QSplashScreen
    from PyQt6.QtGui import QPixmap, QColor, QFont, QPainter
    from PyQt6.QtCore import Qt

    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    _app = QApplication(sys.argv)
    
    base_w, base_h = 400, 200
    ratio = _app.primaryScreen().devicePixelRatio()
    pixmap = QPixmap(int(base_w * ratio), int(base_h * ratio))
    pixmap.setDevicePixelRatio(ratio)
    pixmap.fill(QColor("#161616"))
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
    painter.setPen(QColor("#3498db"))
    painter.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
    painter.drawText(0, 0, base_w, base_h, Qt.AlignmentFlag.AlignCenter, "AAS Robot Studio")
    painter.setPen(QColor("#888"))
    painter.setFont(QFont("Segoe UI", 10))
    painter.drawText(0, 160, base_w, 30, Qt.AlignmentFlag.AlignCenter, "Loading libraries and resources...")
    painter.end()
    
    _splash = QSplashScreen(pixmap)
    _splash.show()
    _app.processEvents()

# 2. HEAVY IMPORTS (Loaded while splash is shown)
import numpy as np
import requests
import xml.etree.ElementTree as ET
from xml.dom import minidom
import mimetypes
import hashlib
import posixpath
import base64

# Import these at top level so Nuitka can detect them for compilation,
# but after splash.show() so the user sees the loading screen immediately.
import trimesh
import pyvista as pv
from pyvistaqt import BackgroundPlotter
from urdfpy import URDF
import xacro
import xacro.substitution_args

import basyx.aas.model as model
import basyx.aas.adapter.aasx as aasx

from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QPushButton, QLabel, QFileDialog, QSlider,
                             QFrame, QMessageBox, QInputDialog, QLineEdit, QDialog,
                             QListWidget, QListWidgetItem, QScrollArea, QGridLayout)
from PyQt6.QtCore import Qt, QTimer, QSize
# QPixmap, QColor, QFont, QPainter already imported above if __main__

# Compatibility patches already applied at top level.


# =================================================================
# 2. XACRO RESOLVER
# =================================================================
class XacroResolver:
    def __init__(self, root_path):
        self.root_path = os.path.abspath(root_path).replace('\\', '/')
        self.file_map = {} # full_path.lower() -> full_path
        self.basename_map = {} # basename.lower() -> [full_paths]
        print(f"[RESOLVER] Mapping: {self.root_path}")
        self._index_directory(self.root_path)
        print(f"[RESOLVER] {len(self.file_map)} entries mapped.")

    def _index_directory(self, path):
        for r, d, fs in os.walk(path):
            for f in fs:
                full_path = os.path.abspath(os.path.join(r, f)).replace('\\', '/')
                self.file_map[full_path.lower()] = full_path
                bn = f.lower()
                if bn not in self.basename_map: self.basename_map[bn] = []
                if full_path not in self.basename_map[bn]:
                    self.basename_map[bn].append(full_path)

    def add_search_path(self, new_path):
        print(f"[RESOLVER] Adding search path: {new_path}")
        old_count = len(self.file_map)
        self._index_directory(new_path)
        print(f"[RESOLVER] {len(self.file_map) - old_count} more files added.")

    def resolve(self, path):
        if not path: return None
        p_orig = path
        p_lower = path.lower().replace('\\', '/')
        
        # 1. Direct hit (absolute or relative to CWD)
        if p_lower in self.file_map: 
            return self.file_map[p_lower]
        
        # 2. Normalize (remove package:// and $(find ...))
        # If it's JUST a $(find pkg), we want to find the package directory
        if re.match(r'^\$\(find [^)]+\)$', path):
            pkg_name = re.search(r'\$\(find ([^)]+)\)', path).group(1).lower()
            # Try to find a directory with this name
            for r, ds, fs in os.walk(self.root_path):
                for d in ds:
                    if d.lower() == pkg_name:
                        return os.path.abspath(os.path.join(r, d)).replace('\\', '/')
            return None

        normalized = re.sub(r'\$\(find [^)]+\)', '', path.replace('package://', ''))
        normalized = '/'.join([s for s in normalized.replace('\\', '/').split('/') if s and s != '.'])
        norm_lower = normalized.lower()
        
        # 3. Best suffix match
        best_match = None
        max_score = -1
        
        bn = os.path.basename(normalized).lower()
        candidates = self.basename_map.get(bn, [])
        
        for cand in candidates:
            cand_lower = cand.lower()
            if cand_lower.endswith(norm_lower):
                score = len(norm_lower)
                if score > max_score:
                    max_score = score
                    best_match = cand
            else:
                # Try partial suffix match (e.g. if package name is different)
                parts = norm_lower.split('/')
                for i in range(len(parts)-1, 0, -1):
                    sub = '/'.join(parts[i:])
                    if cand_lower.endswith(sub):
                        score = len(sub)
                        if score > max_score:
                            max_score = score
                            best_match = cand
                        break
        
        if best_match:
            return best_match
            
        return None


# =================================================================
# 3. ENGINE (PATCHED XACRO)
# =================================================================
_original_abs_filename_spec = None
_original_parse = None
_active_resolver = None

def _ensure_xacro_patched():
    global _original_abs_filename_spec, _original_parse
    if _original_abs_filename_spec is not None: return
    
    _original_abs_filename_spec = xacro.abs_filename_spec
    _original_parse = xacro.parse

    def patched_abs_filename_spec(filename_spec):
        if _active_resolver:
            resolved = _active_resolver.resolve(filename_spec)
            if resolved: return resolved
        return _original_abs_filename_spec(filename_spec)

    def patched_parse(inp, filename=None):
        if inp is None and filename and _active_resolver:
            resolved = _active_resolver.resolve(filename)
            if resolved:
                print(f"[XACRO-PATCH] Reading resolved file: {resolved}")
                with open(resolved, 'r', encoding='utf-8') as f: content = f.read()
                return minidom.parseString(content)
        return _original_parse(inp, filename)

    xacro.abs_filename_spec = patched_abs_filename_spec
    xacro.parse = patched_parse

    try:
        xacro.substitution_args._eval_find = lambda pkg: ""
        print("[XACRO-PATCH] Successfully patched xacro.substitution_args._eval_find")
    except Exception as e:
        print(f"[XACRO-PATCH] Warning: Failed to patch substitution_args: {e}")

def expand_xacro_final(filepath, mappings, resolver):
    _ensure_xacro_patched()
    print(f"[XACRO] Expanding {filepath} with mappings {mappings}")
    global _active_resolver
    _active_resolver = resolver
    try:
        doc = xacro.process_file(filepath, mappings=mappings)
        print(f"[XACRO] Expansion completed successfully.")
        return doc.toxml()
    except Exception as e:
        print(f"[XACRO] ERROR during expansion: {e}")
        raise e
    finally: _active_resolver = None


# =================================================================
# 4. AAS HELPERS
# =================================================================
class AssetManager:
    def __init__(self, assets_root):
        self.assets_root = os.path.abspath(assets_root)
        self.files_to_upload = {}
        self.exts = ['.stl', '.dae', '.obj', '.mtl', '.jpg', '.png', '.jpeg', '.yaml', '.json', '.txt', '.conf']
        print(f"[ASSETS] AssetManager started at: {self.assets_root}")

    def collect(self, filename, resolver):
        if not filename: return None
        print(f"[ASSETS] Collecting: {filename}")
        found = resolver.resolve(filename)
        if not found: 
            print(f"   [ASSETS] WARNING: Failed to resolve '{filename}' for collection.")
            return None
        found = os.path.abspath(found)
        if found in self.files_to_upload: 
            print(f"   [ASSETS] Already in cache: {self.files_to_upload[found]}")
            return self.files_to_upload[found]
        
        rel_path = os.path.relpath(found, self.assets_root).replace(os.sep, '/')
        self.files_to_upload[found] = rel_path
        print(f"   [ASSETS] New asset: {found} -> {rel_path}")
        
        if found.lower().endswith(('.dae', '.obj', '.mtl', '.yaml')):
            print(f"   [ASSETS] Analyzing dependencies of {os.path.basename(found)}...")
            try:
                with open(found, 'r', errors='ignore', encoding='utf-8') as f: content = f.read()
                refs = re.findall(r'<(?:init_from|texture|map_Kd|mtllib)[^>]*>\s*([^< \r\n]+)|(?:map_\w+|mtllib|import)\s+([^\s\r\n]+)', content)
                for r in refs:
                    ref = (r[0] or r[1]).strip()
                    if ref and any(ext in ref.lower() for ext in self.exts):
                        print(f"      [ASSETS] Reference found: {ref}")
                        self.collect(ref, resolver)
            except Exception as e:
                print(f"      [ASSETS] Error reading {found}: {e}")
        return rel_path

class RobustFileRepo(dict):
    def get_content_type(self, fn): 
        return mimetypes.guess_type(fn)[0] or "application/octet-stream"
    def add_file(self, n, c): self[n] = c
    def write_file(self, fn, t): 
        if fn in self: t.write(self[fn])
    def get_sha256(self, fn):
        if fn in self:
            return hashlib.sha256(self[fn]).hexdigest()
        return ""

def sanitize_filename(name):
    """Sanitizes a string for use as a filename, replacing spaces with hyphens."""
    # Replace spaces with hyphens
    res = re.sub(r'\s+', '-', name)
    # Remove characters that are problematic for filenames
    # Keep alphanumeric, hyphens, underscores, and dots
    res = re.sub(r'[^a-zA-Z0-9\-\_\.]', '', res)
    # Trim from start/end
    return res.strip('-_ ')

def sanitize_aas_id(name):
    """Ensures id_short follows AASConstraint AASd-002: [a-zA-Z][a-zA-Z0-9_]*"""
    # Replace anything not alphanumeric or underscore with underscore
    res = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    # Remove multiple underscores
    res = re.sub(r'_+', '_', res)
    if not res: return "ELEMENT_ID"
    # Must start with a letter
    if not res[0].isalpha(): res = "ID_" + res
    return res.strip('_')


class DeployDialog(QDialog):
    def __init__(self, parent=None, default_id="Robot_AAS"):
        super().__init__(parent)
        self.setWindowTitle("Configure Digital Twin (BaSyx)")
        self.setMinimumWidth(450)
        layout = QVBoxLayout(self)

        # --- Configurações Base do AAS ---
        self.edit_id = QLineEdit(default_id)
        layout.addWidget(QLabel("AAS ID (Letters, numbers and _ only):"))
        layout.addWidget(self.edit_id)

        row = QHBoxLayout()
        self.ex = QLineEdit("0.0");
        self.ey = QLineEdit("0.0");
        self.ez = QLineEdit("0.0")
        row.addWidget(QLabel("X:"));
        row.addWidget(self.ex)
        row.addWidget(QLabel("Y:"));
        row.addWidget(self.ey)
        row.addWidget(QLabel("Z:"));
        row.addWidget(self.ez)
        layout.addLayout(row)

        # --- Configuração Genérica de Telemetria ---
        self.conn_group = QGroupBox("Live Connection (Telemetry / Sensoring)")
        c_layout = QGridLayout()

        # Protocolo
        self.combo_proto = QComboBox()
        self.combo_proto.addItems(["Offline / No Connection", "TCP/IP Socket", "HTTP / REST", "WebSocket", "MQTT"])
        c_layout.addWidget(QLabel("Protocolo:"), 0, 0)
        c_layout.addWidget(self.combo_proto, 0, 1)

        # Host / IP
        self.edit_host = QLineEdit("192.168.1.1")
        c_layout.addWidget(QLabel("Host / IP:"), 1, 0)
        c_layout.addWidget(self.edit_host, 1, 1)

        # Porta
        self.edit_port = QLineEdit()
        self.edit_port.setPlaceholderText("Ex: 30004, 80, 443...")
        c_layout.addWidget(QLabel("Porta:"), 2, 0)
        c_layout.addWidget(self.edit_port, 2, 1)

        # Endpoint (Para HTTP/WS/MQTT)
        self.edit_endpoint = QLineEdit()
        self.edit_endpoint.setPlaceholderText("Ex: /rw/motionsystem/... ou topic/robot")
        c_layout.addWidget(QLabel("Endpoint/Topic:"), 3, 0)
        c_layout.addWidget(self.edit_endpoint, 3, 1)

        # Unidades Articulares
        self.combo_units = QComboBox()
        self.combo_units.addItems(["rad", "deg", "mm"])
        c_layout.addWidget(QLabel("Unidade Juntas:"), 4, 0)
        c_layout.addWidget(self.combo_units, 4, 1)

        # Autenticação
        self.combo_auth = QComboBox()
        self.combo_auth.addItems(["None", "Basic Auth", "Digest Auth", "Bearer Token"])
        self.combo_auth.currentTextChanged.connect(self._toggle_auth)
        c_layout.addWidget(QLabel("Autenticação:"), 5, 0)
        c_layout.addWidget(self.combo_auth, 5, 1)

        self.edit_user = QLineEdit()
        self.edit_user.setEnabled(False)
        c_layout.addWidget(QLabel("Username:"), 6, 0)
        c_layout.addWidget(self.edit_user, 6, 1)

        self.edit_pass = QLineEdit()
        self.edit_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit_pass.setEnabled(False)
        c_layout.addWidget(QLabel("Pass / Token:"), 7, 0)
        c_layout.addWidget(self.edit_pass, 7, 1)

        self.conn_group.setLayout(c_layout)
        layout.addWidget(self.conn_group)

        btn = QPushButton("🚀 Send to BaSyx");
        btn.clicked.connect(self.validate_and_accept)
        btn.setStyleSheet("background: #27ae60; color: white; padding: 10px; font-weight: bold;")
        layout.addWidget(btn)

    def _toggle_auth(self, auth_type):
        """Ativa/desativa campos baseados no tipo de autenticação"""
        needs_auth = auth_type != "None"
        self.edit_user.setEnabled(needs_auth and auth_type != "Bearer Token")
        self.edit_pass.setEnabled(needs_auth)

    def validate_and_accept(self):
        rid = self.edit_id.text().strip()
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', rid):
            return QMessageBox.warning(self, "Error", "Invalid AAS ID!")
        for name, field in [("X", self.ex), ("Y", self.ey), ("Z", self.ez)]:
            try:
                float(field.text().replace(',', '.'))
            except ValueError:
                return QMessageBox.warning(self, "Error", f"{name} must be a number.")

        # Validar porta apenas se estiver preenchida
        if self.edit_port.text().strip():
            try:
                int(self.edit_port.text().strip())
            except ValueError:
                return QMessageBox.warning(self, "Error", "Porta tem de ser um número inteiro.")

        self.accept()

class DependencyDialog(QDialog):
    def __init__(self, missing_files, resolver, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Missing Files")
        self.setMinimumWidth(500)
        self.resolver, self.missing = resolver, missing_files
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>Files not found:</b>"))
        self.list_widget = QListWidget()
        for f in self.missing: self.list_widget.addItem(f"❌ {f}")
        layout.addWidget(self.list_widget)
        btn_add = QPushButton("📂 Add Folder"); btn_add.clicked.connect(self.add_folder)
        self.btn_retry = QPushButton("Try Again"); self.btn_retry.setEnabled(False); self.btn_retry.clicked.connect(self.accept)
        btn_layout = QHBoxLayout(); btn_layout.addWidget(btn_add); btn_layout.addWidget(self.btn_retry)
        layout.addLayout(btn_layout)

    def add_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Folder")
        if path:
            self.resolver.add_search_path(path)
            all_ok = True
            for i in range(self.list_widget.count()):
                it = self.list_widget.item(i)
                orig = it.text().replace("❌ ", "").replace("✅ ", "")
                if self.resolver.resolve(orig): it.setText(f"✅ {orig}"); it.setForeground(Qt.GlobalColor.green)
                else: all_ok = False
            if all_ok: self.btn_retry.setEnabled(True)

class XacroArgsDialog(QDialog):
    def __init__(self, args_info, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Xacro Variables")
        self.setMinimumWidth(600)
        self.results = {}
        
        main_layout = QVBoxLayout(self)
        self.grid = QGridLayout()
        self.grid.setSpacing(10)
        
        self.inputs = {}
        # Organize in grid: 2 columns of inputs
        cols = 2
        for i, (name, default) in enumerate(args_info.items()):
            row = i // cols
            col_offset = (i % cols) * 2
            
            lbl = QLabel(f"<b>{name}</b>")
            
            edit = QLineEdit()
            if default: edit.setPlaceholderText(str(default))
            edit.setMinimumWidth(120)
            
            self.inputs[name] = edit
            self.grid.addWidget(lbl, row, col_offset)
            self.grid.addWidget(edit, row, col_offset + 1)

        main_layout.addLayout(self.grid)
        
        btn = QPushButton("Confirm Mappings"); btn.clicked.connect(self.accept_all)
        btn.setStyleSheet("background: #2980b9; color: white; padding: 10px; font-weight: bold; margin-top: 10px;")
        main_layout.addWidget(btn)

    def accept_all(self):
        for n, e in self.inputs.items():
            v = e.text().strip()
            if v: self.results[n] = v
        self.accept()

class DependencyManager:
    @staticmethod
    def scan_xacro_args(filepath, resolver):
        """
        Scans for Xacro arguments and returns ONLY those that are actually used
        in the robot description $(arg name).
        """
        all_defs = {}
        all_text = ""
        visited = set()
        
        def collect_recursive(fp):
            nonlocal all_text
            if fp in visited: return
            visited.add(fp)
            print(f"[DEP-MANAGER] Analyzing: {fp}")
            try:
                with open(fp, 'r', encoding='utf-8') as f:
                    content = f.read()
                    all_text += "\n" + content
                    
                    # 1. Capture definitions: <xacro:arg name="..." default="..." />
                    for m in re.finditer(r'<xacro:arg\s+name=["\']([^"\']+)["\'](?:\s+default=["\']([^"\']+)["\'])?', content):
                        name, default = m.group(1), m.group(2)
                        
                        # Resolve path macros in default values for better readability
                        if default and '$(find ' in default:
                            def replacer(match):
                                pkg = match.group(1)
                                res = resolver.resolve(f"$(find {pkg})") or f"[{pkg}]"
                                return res
                            default = re.sub(r'\$\(find ([^)]+)\)', replacer, default)
                        
                        all_defs[name] = default

                    # 2. Recurse into includes
                    for inc in re.findall(r'<xacro:include\s+filename=["\']([^"\']+)["\']', content):
                        res = resolver.resolve(inc)
                        if res: collect_recursive(res)
            except Exception as e:
                print(f"   [DEP-MANAGER] Error reading {fp}: {e}")

        collect_recursive(filepath)
        
        # 3. Filter: Only keep args that are actually referenced in the combined code
        # Pattern: $(arg name) or some variations with spaces
        used_names = set(re.findall(r'\$\(arg\s+([^)]+)\)', all_text))
        
        filtered_args = {k: v for k, v in all_defs.items() if k in used_names}
        print(f"[DEP-MANAGER] Found {len(all_defs)} definitions, {len(filtered_args)} are actually used.")
        return filtered_args

    @staticmethod
    def scan_meshes(xml_text):
        meshes = list(set(re.findall(r'<mesh\s+filename=["\']([^"\']+)["\']', xml_text)))
        print(f"[DEP-MANAGER] Meshes detected in XML: {len(meshes)}")
        return meshes

    @staticmethod
    def check_recursive_xacro(filepath, resolver, visited=None):
        if visited is None: visited = set()
        if filepath in visited: return []
        visited.add(filepath)
        missing = []
        print(f"[DEP-MANAGER] Recursive Xacro check: {filepath}")
        try:
            with open(filepath, 'r', encoding='utf-8') as f: content = f.read()
            for inc in re.findall(r'<xacro:include\s+filename=["\']([^"\']+)["\']', content):
                res = resolver.resolve(inc)
                if not res: 
                    print(f"   [DEP-MANAGER] MISSING: {inc}")
                    missing.append(inc)
                else: missing.extend(DependencyManager.check_recursive_xacro(res, resolver, visited))
        except Exception as e:
            print(f"   [DEP-MANAGER] Error verifying {filepath}: {e}")
        return list(set(missing))


# =================================================================
# 5. MAIN APP
# =================================================================
class RobotStudioPro(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AAS Robot Studio - Pro")
        self.robot = None
        self.resolver = None
        self.mesh_actors = {}
        self.show_degrees = False
        self.current_urdf_xml = None
        self.current_urdf_path = None
        self.global_matrix = np.eye(4)
        
        # Smooth Motion State
        self.current_joint_state = {}
        self.target_joint_state = {}
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self._smooth_update)
        self.anim_timer.start(10) # 100Hz for maximum fluidity
        
        self._setup_ui()
        self.showMaximized()
        print("[APP] RobotStudioPro initialized.")

    def _smooth_update(self):
        if not self.robot or not self.target_joint_state: return
        
        changed = False
        # Factor 0.4: Responsive drag, smooth Lerp damping
        lerp_factor = 0.4 
        
        for name in list(self.target_joint_state.keys()):
            target = self.target_joint_state[name]
            current = self.current_joint_state.get(name, 0.0)
            diff = target - current
            
            if abs(diff) > 0.0001:
                self.current_joint_state[name] = current + (diff * lerp_factor)
                changed = True
            else:
                self.current_joint_state[name] = target
        
        if changed:
            self.update_robot_visuals()
            self.plotter.update() # Ultra-fast incremental update

    def update_robot_visuals(self, active=None):
        if not self.robot: return
        # FK calculated using the interpolated state
        fk = self.robot.visual_geometry_fk(cfg=self.current_joint_state)
        for obj, trans in fk.items():
            if obj in self.mesh_actors:
                # Apply mesh scale if present in URDF geometry
                scale_matrix = np.eye(4)
                # obj is usually a Visual object, find its geometry
                geom = obj.geometry if hasattr(obj, 'geometry') else None
                if geom and hasattr(geom, 'scale') and geom.scale is not None:
                    s = geom.scale
                    scale_matrix = np.diag([s[0], s[1], s[2], 1.0])
                
                final_trans = self.global_matrix @ trans @ scale_matrix
                for a in self.mesh_actors[obj]:
                    a.user_matrix = final_trans
                    if active and active.lower() in str(obj).lower():
                        a.GetProperty().SetEdgeVisibility(True); a.GetProperty().SetEdgeColor(0,1,1)
                    else: a.GetProperty().SetEdgeVisibility(False)

    def _setup_ui(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #0f0f0f; }
            QFrame#Sidebar { 
                background-color: #161616; 
                border-right: 1px solid #222; 
            }
            QPushButton { 
                background-color: #252525; 
                color: #e0e0e0; 
                border: 1px solid #333;
                border-radius: 6px; 
                padding: 8px; 
                font-family: 'Segoe UI', sans-serif;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover { background-color: #303030; border-color: #444; }
            QPushButton#ActionBtn { background-color: #2980b9; color: white; border: none; font-weight: bold; }
            QPushButton#ActionBtn:hover { background-color: #3498db; }
            QPushButton#ImportBtn { background-color: #d35400; color: white; border: none; font-weight: bold; }
            QPushButton#ImportBtn:hover { background-color: #e67e22; }
            
            QLabel { color: #888; font-family: 'Segoe UI'; font-size: 11px; }
            QLineEdit { 
                background-color: #1a1a1a; 
                color: #3498db; 
                border: 1px solid #333; 
                padding: 2px; 
                border-radius: 3px; 
                font-weight: bold;
                font-size: 11px;
            }
            QSlider::groove:horizontal {
                border: 1px solid #222;
                height: 3px;
                background: #222;
                border-radius: 1px;
            }
            QSlider::handle:horizontal {
                background: #3498db;
                border: 1px solid #3498db;
                width: 10px;
                height: 10px;
                margin: -4px 0;
                border-radius: 5px;
            }
            QScrollArea { border: none; background: transparent; }
        """)

        central = QWidget(); self.setCentralWidget(central)
        layout = QHBoxLayout(central); layout.setContentsMargins(0,0,0,0); layout.setSpacing(0)
        
        side = QFrame(); side.setObjectName("Sidebar"); side.setFixedWidth(400)
        self.side_layout = QVBoxLayout(side); self.side_layout.setContentsMargins(15,15,15,15); self.side_layout.setSpacing(12)
        
        # --- TOP: FILE ACTIONS ---
        header = QLabel("ROBOT SOURCE"); header.setStyleSheet("color: #555; font-weight: bold; letter-spacing: 1.5px;")
        self.side_layout.addWidget(header)
        
        btn_load = QPushButton("📂  Open Local Folder"); btn_load.clicked.connect(self.load_robot); self.side_layout.addWidget(btn_load)
        
        self.btn_import = QPushButton("📥  Import from BaSyx"); self.btn_import.setObjectName("ImportBtn")
        self.btn_import.clicked.connect(self.import_from_basyx); self.side_layout.addWidget(self.btn_import)

        line = QFrame(); line.setFrameShape(QFrame.Shape.HLine); line.setStyleSheet("color: #222;"); self.side_layout.addWidget(line)

        # --- MIDDLE: JOINT CONTROL (SCROLLABLE) ---
        row_tools = QHBoxLayout()
        header_joints = QLabel("ARTICULATIONS"); header_joints.setStyleSheet("color: #555; font-weight: bold; letter-spacing: 1.5px;")
        row_tools.addWidget(header_joints); row_tools.addStretch()
        
        self.unit_toggle = QPushButton("Rad"); self.unit_toggle.setFixedWidth(40); self.unit_toggle.setCheckable(True)
        self.unit_toggle.clicked.connect(self.toggle_units); row_tools.addWidget(self.unit_toggle)
        self.side_layout.addLayout(row_tools)

        self.slider_area = QVBoxLayout()
        self.slider_area.setSpacing(4) # Ultra tight spacing
        slider_container = QWidget(); slider_container.setLayout(self.slider_area)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setWidget(slider_container)
        self.side_layout.addWidget(scroll)

        # --- BOTTOM: AAS & STATUS ---
        line2 = QFrame(); line2.setFrameShape(QFrame.Shape.HLine); line2.setStyleSheet("color: #222;"); self.side_layout.addWidget(line2)
        
        btn_reset = QPushButton("🏠 Reset Pose"); btn_reset.clicked.connect(self.reset_pose); self.side_layout.addWidget(btn_reset)
        
        self.btn_aas = QPushButton("🚀  GENERATE DIGITAL TWIN (AAS)"); self.btn_aas.setObjectName("ActionBtn")
        self.btn_aas.setFixedHeight(40)
        self.btn_aas.clicked.connect(self.deploy_aas); self.btn_aas.setEnabled(False); self.side_layout.addWidget(self.btn_aas)

        self.lbl_info = QLabel("Status: Ready"); self.lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.side_layout.addWidget(self.lbl_info)
        
        # 3D Plotter
        self.plotter = BackgroundPlotter(show=False)
        self.plotter.set_background("#080808", top="#121212") 
        self.plotter.add_axes(color='white') # White axes labels
        self.plotter.enable_shadows(); self.plotter.enable_eye_dome_lighting()
        
        # Lock Z axis and initial camera setup
        self.plotter.enable_terrain_style(mouse_wheel_zooms=True)
        self.plotter.camera.focal_point = (0, 0, 0)
        self.plotter.camera.position = (3, 3, 2)
        self.plotter.camera.up = (0, 0, 1)
        
        layout.addWidget(side); layout.addWidget(self.plotter.interactor)

    def reset_pose(self):
        print("[APP] Resetting pose...")
        if not self.robot: return
        for sld in self.joint_sliders.values(): sld.setValue(0)
        self.update_robot()

    def load_robot(self):
        path = QFileDialog.getExistingDirectory(self, "Folder")
        if not path: return
        self.current_robot_root = path  
        self.global_matrix = np.eye(4) # Reset global pos on local load
        print(f"\n[LOAD] Initializing load from: {path}")
        self.resolver = XacroResolver(path)
        candidates = sorted(list(set([f for f in self.resolver.file_map.values() if f.lower().endswith('.urdf') or f.lower().endswith('.urdf.xacro')])))
        
        if not candidates: 
            return QMessageBox.warning(self, "Error", "No URDF/Xacro found in directory!")
        
        target = candidates[0]
        if len(candidates) > 1:
            item, ok = QInputDialog.getItem(self, "Choose", "Primary File?", [os.path.basename(c) for c in candidates], 0, False)
            if ok: target = [c for c in candidates if os.path.basename(c) == item][0]
            else: return
        
        try:
            mappings = {"ur_type": "ur3e", "name": "ur"} # Defaults
            
            if target.lower().endswith('.xacro'):
                # 1. CLEAN & RESOLVE: Check dependencies BEFORE asking for args
                print("[LOAD] Verifying dependencies...")
                while True:
                    missing = DependencyManager.check_recursive_xacro(target, self.resolver)
                    if missing:
                        print(f"   [LOAD] Found {len(missing)} missing includes.")
                        if DependencyDialog(missing, self.resolver, self).exec() == QDialog.DialogCode.Accepted:
                            continue # Check again after adding folder
                        else: return # User cancelled
                    break
                
                # 2. VALIDATE: Check if it's a valid assembly or just a macro library
                with open(target, 'r', encoding='utf-8') as f:
                    content = f.read()
                    is_pure_macro = "<xacro:macro" in content and "<link" not in content and "<joint" not in content
                    # Simple heuristic: if it has macros but no links/joints and doesn't call a macro, it's likely a library
                    if is_pure_macro and not re.search(r'<xacro:[^m][^a][^c][^r][^o]', content):
                        print("[LOAD] WARNING: Selected file appears to be a Macro library, not a Robot assembly.")
                        res = QMessageBox.question(self, "Macro File Detected", 
                            "This file seems to contain only Macro definitions, not a full Robot.\n\n"
                            "Are you sure you want to proceed? (It might result in an empty visualization)",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                        if res == QMessageBox.StandardButton.No: return

                # 3. SCAN: Now that we have all files, scan for ONLY used arguments
                print("[LOAD] Scanning for used Xacro arguments...")
                args = DependencyManager.scan_xacro_args(target, self.resolver)
                if args:
                    dlg = XacroArgsDialog(args, self)
                    if dlg.exec() == QDialog.DialogCode.Accepted:
                        mappings.update(dlg.results)
                    else: return
                
                print("[LOAD] Expanding Xacro...")
                xml_text = expand_xacro_final(target, mappings, self.resolver)
            else:
                with open(target, 'r', encoding='utf-8') as f: xml_text = f.read()

            self.current_urdf_xml, self.current_urdf_path = xml_text, target
            root = ET.fromstring(xml_text.strip())
            
            # URDF Post-processing
            if 'name' not in root.attrib: root.set('name', os.path.basename(target).split('.')[0])
            for trans in root.findall(".//transmission"): root.remove(trans)
            
            print("[LOAD] Resolving mesh paths in URDF...")
            for m_tag in root.findall(".//mesh"):
                fn = m_tag.get("filename")
                real = self.resolver.resolve(fn)
                if real: m_tag.set("filename", real)
            
            temp = os.path.join(path, "_compiled.urdf")
            with open(temp, "w", encoding='utf-8') as f: f.write(ET.tostring(root, encoding='unicode'))
            
            # Store the resolved tree for AAS deployment
            self.current_urdf_tree = root
            
            try:
                print("[LOAD] Parsing final URDF...")
                self.robot = URDF.load(temp)
                self._build_view(); self._create_sliders()
                self.lbl_info.setText(f"✓ {self.robot.name}"); self.btn_aas.setEnabled(True)
            except ValueError as ve:
                if "Link" in str(ve):
                    QMessageBox.warning(self, "Empty Robot", 
                        "The resulting URDF contains no Links.\n\n"
                        "Please verify if you selected the correct entry file (e.g., 'ur.urdf.xacro' instead of 'ur_macro.xacro').")
                else: raise ve
        except Exception as e: 
            print(f"[LOAD] ERROR: {e}")
            traceback.print_exc()
            QMessageBox.critical(self, "Load Failed", f"Critical error while loading robot:\n{str(e)}")

    def _b64(self, s):
        return base64.urlsafe_b64encode(s.encode()).decode().rstrip('=')

    def import_from_basyx(self):
        print("\n" + "="*50 + "\n[IMPORT] STARTING BASYX IMPORT\n" + "="*50)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            reg_res = requests.get("http://localhost:8082/shell-descriptors", timeout=5).json()
            shells = reg_res if isinstance(reg_res, list) else reg_res.get("result", [])
            QApplication.restoreOverrideCursor()
            if not shells: return QMessageBox.information(self, "BaSyx", "Registry empty.")
            
            options = [f"{s['idShort']} ({s['id']})" for s in shells if 'id' in s]
            choice, ok = QInputDialog.getItem(self, "BaSyx Explorer", "Robot:", options, 0, False)
            if not ok: return
            
            sel_id = choice.split('(')[-1].rstrip(')')
            sel_short = choice.split(' (')[0].strip()
            
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            cache_dir = os.path.abspath(os.path.join("aas_cache", sel_short))
            os.makedirs(cache_dir, exist_ok=True)
            
            repo_url = "http://localhost:8081"
            res_shell = requests.get(f"{repo_url}/shells/{self._b64(sel_id)}").json()
            sm_refs = res_shell.get("submodels", [])
            
            geo_id, pos_id = None, None
            for r in sm_refs:
                sid = r["keys"][0]["value"]
                s_data = requests.get(f"{repo_url}/submodels/{self._b64(sid)}").json()
                idS = s_data.get("idShort")
                if idS == "GeometryData": geo_id = sid
                if idS == "PositionData": pos_id = sid
            
            if not geo_id: raise Exception("GeometryData missing!")

            def dl_elems(url, tdir):
                items = requests.get(f"{url}/submodel-elements").json()
                if not isinstance(items, list): items = items.get("result", [])
                for el in items:
                    idS = el.get("idShort", "")
                    if el.get("modelType") == "File":
                        rel = idS.replace("PATH_", "").replace("_SL_", "/").replace("_DOT_", ".")
                        if rel == "Main_URDF": rel = "robot.urdf"
                        elif not any(x in rel for x in ['.urdf', '.stl', '.dae', '.obj', '.png', '.jpg']): rel += ".urdf"
                        dest = os.path.join(tdir, rel)
                        os.makedirs(os.path.dirname(dest), exist_ok=True)
                        down = requests.get(f"{url}/submodel-elements/{idS}/attachment")
                        with open(dest, "wb") as f: f.write(down.content)
                    elif el.get("modelType") == "SubmodelElementCollection":
                        dl_elems(f"{url}/submodel-elements/{idS}", tdir)

            dl_elems(f"{repo_url}/submodels/{self._b64(geo_id)}", cache_dir)
            urdf_path = None
            for r, d, fs in os.walk(cache_dir):
                for f in fs:
                    if f.lower().endswith(".urdf") and not f.startswith("_"):
                        urdf_path = os.path.abspath(os.path.join(r, f))
                        break
            
            if not urdf_path: raise Exception(f"URDF not found in {cache_dir}")
            self.current_robot_root = cache_dir
            self.current_urdf_path = urdf_path
            with open(urdf_path, 'r', encoding='utf-8') as f: self.current_urdf_xml = f.read()
            self.resolver = XacroResolver(cache_dir)
            self.robot = URDF.load(urdf_path)
            self._build_view(); self._create_sliders()
            
            pos = [0,0,0]
            if pos_id:
                p_items = requests.get(f"{repo_url}/submodels/{self._b64(pos_id)}/submodel-elements").json()
                if not isinstance(p_items, list): p_items = p_items.get("result", [])
                for pi in p_items:
                    k = pi["idShort"].upper()
                    try:
                        v = float(pi["value"])
                        if "X" in k: pos[0] = v
                        elif "Y" in k: pos[1] = v
                        elif "Z" in k: pos[2] = v
                    except: pass
            
            self.global_matrix = trimesh.transformations.translation_matrix(pos)
            self.update_robot() # Apply matrix via update_robot
            
            # Update camera for new base
            base_pos = self.global_matrix[:3, 3]
            self.plotter.camera.focal_point = base_pos
            self.plotter.camera.position = base_pos + np.array([3.0, 3.0, 2.0])
            self.plotter.camera_set = True # Prevent reset on first zoom
            
            self.lbl_info.setText(f"✓ {sel_short} (Synced)")
            QApplication.restoreOverrideCursor()
            print("[IMPORT] Import completed successfully.")
            QMessageBox.information(self, "Success", "Imported!")
        except Exception as e:
            QApplication.restoreOverrideCursor()
            traceback.print_exc(); QMessageBox.critical(self, "Error", str(e))

    def deploy_aas(self):
        if not self.robot or not hasattr(self, 'current_urdf_tree'): 
            return QMessageBox.warning(self, "Error", "Please load a robot first.")
            
        dlg = DeployDialog(self, default_id=self.robot.name)
        if dlg.exec() != QDialog.DialogCode.Accepted: return
        
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        self.btn_aas.setEnabled(False); self.btn_aas.setText("⏳...")
        try:
            rid_raw = dlg.edit_id.text().strip()
            rid_fn = rid_raw
            rid_aas = rid_raw
            px, py, pz = dlg.ex.text(), dlg.ey.text(), dlg.ez.text()
            
            # Use the selected robot folder as the root for all relative paths
            assets_root = self.current_robot_root
            manager = AssetManager(assets_root)
            
            # Use the resolved tree (which has absolute paths on this machine)
            import copy
            tree_copy = copy.deepcopy(self.current_urdf_tree)
            
            print(f"[DEPLOY] Starting asset collection from resolved URDF tree...")
            for elem in tree_copy.iter():
                for attr, val in elem.attrib.items():
                    # Check if the attribute looks like a path with one of our extensions
                    if any(ext in val.lower() for ext in manager.exts):
                        rel = manager.collect(val, self.resolver)
                        if rel:
                            print(f"   [DEPLOY] Path updated: {attr}='{os.path.basename(val)}' -> '{rel}'")
                            elem.set(attr, rel)

            urdf_filename = os.path.basename(self.current_urdf_path)
            if urdf_filename.lower().endswith('.xacro'):
                urdf_filename = re.sub(r'\.xacro$', '', urdf_filename, flags=re.IGNORECASE)
            if not urdf_filename.lower().endswith('.urdf'):
                urdf_filename += '.urdf'
            urdf_rel_path = urdf_filename
            
            urdf_bytes = io.BytesIO()
            ET.ElementTree(tree_copy).write(urdf_bytes, encoding='utf-8', xml_declaration=True)
            
            shell = model.AssetAdministrationShell(
                asset_information=model.AssetInformation(asset_kind=model.AssetKind.INSTANCE, global_asset_id=f"http://acplt.org/Assets/{rid_fn}"),
                id_=f"https://acplt.org/AAS_{rid_fn}", id_short=rid_aas
            )
            sm_geo = model.Submodel(id_=f"https://acplt.org/Submodels/Geo_{rid_fn}", id_short="GeometryData")
            sm_pos = model.Submodel(id_=f"https://acplt.org/Submodels/Pos_{rid_fn}", id_short="PositionData")
            
            for ax, v in [('X', px), ('Y', py), ('Z', pz)]:
                sm_pos.submodel_element.add(model.Property(id_short=f"Pos_{ax}", value_type=model.datatypes.Double, value=float(v.replace(',', '.'))))
            
            file_repo = RobustFileRepo()
            
            # Save URDF at root: /aasx/robot/robot_name.urdf
            aas_urdf_path = posixpath.normpath(posixpath.join("/aasx/robot", urdf_rel_path))
            file_repo.add_file(aas_urdf_path, urdf_bytes.getvalue())
            urdf_id = sanitize_aas_id("PATH_" + urdf_rel_path.replace("/", "_SL_").replace(".", "_DOT_").replace("-", "_DASH_"))
            sm_geo.submodel_element.add(model.File(id_short=urdf_id[:100], value=aas_urdf_path, content_type="application/xml"))

            print(f"[DEPLOY] Uploading {len(manager.files_to_upload)} collected assets...")
            for l_path, r_path in manager.files_to_upload.items():
                aas_path = posixpath.normpath(posixpath.join("/aasx/robot", r_path))
                if aas_path == aas_urdf_path: continue
                
                try:
                    with open(l_path, 'rb') as f: file_repo.add_file(aas_path, f.read())
                    pid = sanitize_aas_id("PATH_" + r_path.replace("/", "_SL_").replace(".", "_DOT_").replace("-", "_DASH_"))
                    sm_geo.submodel_element.add(model.File(id_short=pid[:100], value=aas_path, content_type=mimetypes.guess_type(l_path)[0] or "application/octet-stream"))
                    print(f"   [DEPLOY] Included: {r_path}")
                except Exception as e:
                    print(f"   [DEPLOY] ERROR reading {l_path}: {e}")

            obj_store = model.DictObjectStore()
            obj_store.add(shell); obj_store.add(sm_geo); obj_store.add(sm_pos)
            shell.submodel.add(model.ModelReference.from_referable(sm_geo))
            shell.submodel.add(model.ModelReference.from_referable(sm_pos))
            
            os.makedirs("aasx_packages", exist_ok=True)
            out_fn = os.path.join("aasx_packages", f"{rid_fn}_Twin.aasx")
            with aasx.AASXWriter(out_fn) as writer: writer.write_aas(shell.id, obj_store, file_repo, rid_aas)
            
            res = requests.post("http://localhost:8081/upload", files={'file': (os.path.basename(out_fn), open(out_fn, 'rb'), 'application/octet-stream')})
            if res.status_code in [200, 201, 204]:
                requests.post("http://localhost:8082/shell-descriptors", json={
                    "id": shell.id, "idShort": shell.id_short, "assetKind": "Instance",
                    "globalAssetId": shell.asset_information.global_asset_id,
                    "submodelDescriptors": [{"idShort": sm.id_short, "id": sm.id, "endpoints": [{"interface": "SUBMODEL-3.0", "protocolInformation": {"href": f"http://localhost:8081/submodels/{sm.id}", "endpointProtocol": "HTTP"}}]} for sm in [sm_geo, sm_pos]],
                    "endpoints": [{"interface": "AAS-3.0", "protocolInformation": {"href": f"http://localhost:8081/shells/{shell.id}", "endpointProtocol": "HTTP"}}]
                })
                QApplication.restoreOverrideCursor()
                print("[DEPLOY] AAS created and registered successfully.")
                QMessageBox.information(self, "Success", f"AAS Created!\n\nIncluded {len(manager.files_to_upload)} meshes/textures.")
            else:
                raise Exception(f"Upload failed ({res.status_code})")
        except Exception as e: 
            QApplication.restoreOverrideCursor()
            traceback.print_exc(); QMessageBox.critical(self, "Error", str(e))
        finally:
            while QApplication.overrideCursor() is not None: QApplication.restoreOverrideCursor()
            self.btn_aas.setEnabled(True); self.btn_aas.setText("🤖 Create AAS Digital Twin")

    def _build_view(self):
        print("[VIEW] Building 3D visualization...")
        self.plotter.clear(); self.mesh_actors = {}; self.plotter.add_axes(color='white')
        
        # Prevent crash if robot has no visuals or failed to load meshes
        try:
            fk = self.robot.visual_geometry_fk()
        except Exception as e:
            print(f"[VIEW] Error calculating FK: {e}")
            return

        all_pts = []
        for obj, transform in fk.items():
            # obj is typically a Visual object
            name = getattr(obj, 'name', 'unnamed')
            geom = obj.geometry if hasattr(obj, 'geometry') else obj
            if geom is None:
                print(f"   [VIEW] Skipping {name}: geometry is None")
                continue
            
            g_type = type(geom).__name__
            meshes = None
            
            # urdfpy might have failed to load meshes (NoneType error in its getter)
            try:
                meshes = geom.meshes
            except Exception as e:
                print(f"   [VIEW] Warning: urdfpy failed to provide meshes for {g_type} ({name}): {e}")

            # Fallback for urdfpy primitive issues
            if (meshes is None or len(meshes) == 0):
                if g_type == 'Cylinder':
                    print(f"   [VIEW] Falling back to manual Cylinder creation for {name}...")
                    try: meshes = [trimesh.creation.cylinder(radius=geom.radius, height=geom.length)]
                    except Exception as e: print(f"      [VIEW] Cylinder fallback failed: {e}")
                elif g_type == 'Box':
                    print(f"   [VIEW] Falling back to manual Box creation for {name}...")
                    try: meshes = [trimesh.creation.box(extents=geom.size)]
                    except Exception as e: print(f"      [VIEW] Box fallback failed: {e}")
                elif g_type == 'Sphere':
                    print(f"   [VIEW] Falling back to manual Sphere creation for {name}...")
                    try: meshes = [trimesh.creation.sphere(radius=geom.radius)]
                    except Exception as e: print(f"      [VIEW] Sphere fallback failed: {e}")
                elif g_type == 'Mesh':
                    print(f"   [VIEW] Falling back to manual Mesh load for {name}: {getattr(geom, 'filename', 'unknown')}...")
                    try:
                        loaded = trimesh.load(geom.filename)
                        if isinstance(loaded, trimesh.Scene):
                            m = loaded.dump(concatenate=True)
                        else:
                            m = loaded
                        
                        if hasattr(geom, 'scale') and geom.scale is not None:
                            m.apply_scale(geom.scale)
                        meshes = [m]
                    except Exception as e: print(f"      [VIEW] Mesh fallback failed: {e}")

            if meshes is None or len(meshes) == 0:
                print(f"   [VIEW] Warning: Could not obtain meshes for {g_type} ({name}).")
                continue

            print(f"   [VIEW] Processing {g_type} ({name}) with {len(meshes)} meshes")
            
            col = [0.7,0.7,0.7]
            if hasattr(obj, 'material') and obj.material and obj.material.color is not None:
                col = np.array(obj.material.color[:3]).astype(float)
                if col.max() > 1.01: col /= 255.0
            
            for i, mesh in enumerate(meshes):
                if mesh is None: continue
                
                # PyVista needs faces to be a flat array: [3, v1, v2, v3, 3, v4, v5, v6, ...]
                # trimesh.faces is (N, 3). Ensure int32 for VTK compatibility.
                faces = np.column_stack([np.full(len(mesh.faces), 3), mesh.faces]).astype(np.int32).flatten()
                
                # Apply mesh scale if present in URDF geometry
                scale_matrix = np.eye(4)
                if hasattr(geom, 'scale') and geom.scale is not None:
                    s = geom.scale
                    scale_matrix = np.diag([s[0], s[1], s[2], 1.0])
                
                all_pts.append(trimesh.transformations.transform_points(mesh.vertices, transform @ scale_matrix))
                pv_mesh = pv.PolyData(mesh.vertices, faces)
                
                actor = None
                if hasattr(mesh, 'visual') and mesh.visual:
                    try:
                        mat = getattr(mesh.visual, 'material', None)
                        if mat:
                            img = getattr(mat, 'image', getattr(mat, 'baseColorTexture', getattr(mat, 'base_color_texture', None)))
                            if img:
                                pv_mesh.texture_map_coords = mesh.visual.uv
                                actor = self.plotter.add_mesh(pv_mesh, texture=pv.numpy_to_texture(np.array(img)), smooth_shading=True)
                            if not actor:
                                pbr = getattr(mat, 'baseColorFactor', getattr(mat, 'base_color_factor', None))
                                if pbr is not None:
                                    c2 = np.array(pbr[:3]).astype(float)
                                    if c2.max() > 1.01: c2 /= 255.0
                                    actor = self.plotter.add_mesh(pv_mesh, color=c2, smooth_shading=True, specular=0.5)
                        if not actor and hasattr(mesh.visual, 'vertex_colors'):
                            c3 = mesh.visual.vertex_colors[:, :3].astype(float)
                            if c3.max() > 1.01: c3 /= 255.0
                            pv_mesh.point_data['colors'] = c3
                            actor = self.plotter.add_mesh(pv_mesh, scalars='colors', rgb=True, preference='point', smooth_shading=True)
                    except Exception as e: pass
                
                if not actor: actor = self.plotter.add_mesh(pv_mesh, color=col, smooth_shading=True, specular=0.5, ambient=0.2)
                actor.user_matrix = self.global_matrix @ transform @ scale_matrix
                if obj not in self.mesh_actors: self.mesh_actors[obj] = []
                self.mesh_actors[obj].append(actor)
        
        if all_pts:
            # Pivot at real robot base (world)
            base_pos = self.global_matrix[:3, 3]
            self.plotter.camera.focal_point = base_pos
            # Offset camera to avoid parallel view vector and up vector
            self.plotter.camera.position = base_pos + np.array([3.0, 3.1, 2.0]) 
            self.plotter.camera.up = (0, 0, 1)
            self.plotter.camera.reset_clipping_range()
            self.plotter.camera_set = True # Lock auto-resets
            self.plotter.render()

    def _clear_layout(self, layout):
        if not layout: return
        while layout.count():
            it = layout.takeAt(0)
            widget = it.widget()
            if widget:
                widget.setParent(None); widget.deleteLater()
            else:
                sub_layout = it.layout()
                if sub_layout: self._clear_layout(sub_layout)

    def _create_sliders(self):
        self._clear_layout(self.slider_area)
        self.joint_sliders, self.joint_inputs = {}, {}
        for j in self.robot.actuated_joints:
            low = j.limit.lower if j.limit and j.limit.lower is not None else -math.pi
            high = j.limit.upper if j.limit and j.limit.upper is not None else math.pi
            
            # Compact Row: Label | Slider | Input
            row = QHBoxLayout()
            row.setSpacing(10)
            
            lbl = QLabel(f"<b>{j.name}</b>")
            lbl.setFixedWidth(110)
            
            sld = QSlider(Qt.Orientation.Horizontal)
            sld.setRange(int(low * 10000), int(high * 10000)); sld.setValue(0)

            val_input = QLineEdit("0.000000"); val_input.setFixedWidth(85); val_input.setAlignment(Qt.AlignmentFlag.AlignRight)

            self.joint_sliders[j.name], self.joint_inputs[j.name] = sld, val_input
            sld.valueChanged.connect(lambda v, name=j.name: self.sync_slider_to_input(name))
            val_input.editingFinished.connect(lambda name=j.name: self.sync_input_to_slider(name))

            row.addWidget(lbl); row.addWidget(sld); row.addWidget(val_input)
            self.slider_area.addLayout(row)

    def sync_slider_to_input(self, name):
        val = self.joint_sliders[name].value() / 10000.0
        self.joint_inputs[name].setText(f"{math.degrees(val):.3f}" if self.show_degrees else f"{val:.6f}")
        self.target_joint_state[name] = val

    def sync_input_to_slider(self, name):
        try:
            txt = self.joint_inputs[name].text().replace(',', '.')
            val = float(txt)
            rad = math.radians(val) if self.show_degrees else val
            sld = self.joint_sliders[name]; iv = int(rad * 10000)
            sld.setValue(max(sld.minimum(), min(sld.maximum(), iv)))
        except: self.sync_slider_to_input(name)

    def toggle_units(self):
        self.show_degrees = not self.show_degrees
        self.unit_toggle.setText("Deg" if self.show_degrees else "Rad")
        for n in self.joint_sliders: self.sync_slider_to_input(n)

    def update_robot(self, active=None):
        self.update_robot_visuals(active)

if __name__ == "__main__":
    # 3. LOAD MAIN WINDOW (After all imports and definitions are complete)
    apply_compatibility_patches()
    
    window = RobotStudioPro()
    window.show()
    
    # 4. CLOSE SPLASH
    if _splash: _splash.finish(window)
    
    sys.exit(_app.exec())
