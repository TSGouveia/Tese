import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thesis_art_utils import *

# =============================================================================
# 1. GLOBAL ARCHITECTURE (3 LAYERS)
# =============================================================================
def make_architecture_global():
    fig, ax = plt.subplots(figsize=(7.6, 9.2), dpi=300)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')

    c_l1_bg, c_l1_border = '#eff6ff', '#2563eb'
    c_l2_bg, c_l2_border = '#f0fdf4', '#16a34a'
    c_l3_bg, c_l3_border = '#faf5ff', '#9333ea'

    # --- LAYER 1 ---
    draw_group(ax, 3, 76.5, 94, 21.5, "Layer 1 · Setup & Modeling Client (Python)", c_l1_bg, c_l1_border, fs=11.0)
    draw_card(ax, 6, 78.5, 26, 15.2, "Conveyor Wizard\nDesktop App", 
              ["PyQt6 Desktop App", "5-Step Guided Wizard", "Rule & Layout Editors"], '#ffffff', c_l1_border, t_fs=9.2, b_fs=7.8)
    draw_card(ax, 37, 78.5, 26, 15.2, "3D Model Parser\n(Geometry Engine)", 
              ["PyVista & Trimesh", "Read 3D Meshes & URDF", "Part Hierarchy Tree"], '#ffffff', c_l1_border, t_fs=9.2, b_fs=7.8)
    draw_card(ax, 68, 78.5, 26, 15.2, "BaSyx Python SDK\n(Package Builder)", 
              ["Create .aasx Archives", "Generate 5 Submodels", "Upload via REST API"], '#ffffff', c_l1_border, t_fs=9.2, b_fs=7.8)

    draw_arrow(ax, (32, 86.1), (37, 86.1), style='->', lw=1.6)
    draw_arrow(ax, (63, 86.1), (68, 86.1), style='->', lw=1.6)

    # --- LAYER 2 ---
    draw_group(ax, 3, 38.0, 94, 35.0, "Layer 2 · Semantic Services (Eclipse BaSyx v2 in Docker)", c_l2_bg, c_l2_border, fs=11.0)
    draw_card(ax, 6, 54.0, 41, 14.5, "AAS Repository\n(:8081)", 
              ["Store Shells & Submodels", "Upload Endpoint (/upload)", "Standard REST API Endpoints"], '#ffffff', c_l2_border, t_fs=9.2, b_fs=7.6)
    draw_card(ax, 53, 54.0, 41, 14.5, "AAS & SM Registries\n(:8082 / :8083)", 
              ["Look Up Asset Identifiers", "Resolve Microservice URLs", "Shell Directory & Discovery API"], '#ffffff', c_l2_border, t_fs=9.2, b_fs=7.6)

    draw_card(ax, 6, 40.5, 41, 11.5, "MongoDB Database (:27017)", 
              ["Persistent Storage for", "Registry Descriptors & Models"], '#ffffff', '#b45309', t_fs=8.8, b_fs=7.4)
    draw_card(ax, 53, 40.5, 41, 11.5, "BaSyx Web UI (:3000)", 
              ["Administrative Web Dashboard", "& Submodel Inspector"], '#ffffff', '#7e22ce', t_fs=8.8, b_fs=7.4)

    draw_arrow(ax, (47, 61.2), (53, 61.2), style='<->', lw=1.4)
    draw_arrow(ax, (26.5, 54.0), (26.5, 52.0), style='->', lw=1.3)
    draw_arrow(ax, (73.5, 54.0), (73.5, 52.0), style='->', lw=1.3)

    # --- LAYER 3 ---
    draw_group(ax, 3, 2.0, 94, 33.0, "Layer 3 · Simulation & Physical Synchronization", c_l3_bg, c_l3_border, fs=11.0)

    rect_u = patches.FancyBboxPatch((5.5, 3.5), 41.5, 27.5, boxstyle="round,pad=0.4,rounding_size=1.2",
                                    facecolor='#ffffff', edgecolor='#a855f7', linewidth=1.5, zorder=2)
    ax.add_patch(rect_u)
    ax.text(7.5, 28.5, "Unity 3D Simulation Runtime", fontsize=9.8, fontweight='bold', color='#7e22ce', zorder=3)

    draw_card(ax, 7.5, 20.0, 37.5, 7.0, "BaSyxManager.cs", ["Discover & Download Assets", "Query BaSyx REST API"], '#f5f3ff', '#a855f7', t_fs=8.8, b_fs=7.2)
    draw_card(ax, 7.5, 12.0, 37.5, 7.0, "AASRuleEngine.cs", ["Run ControlLogic Rules", "Virtual Commissioning Mode"], '#f5f3ff', '#a855f7', t_fs=8.8, b_fs=7.2)
    draw_card(ax, 7.5, 4.0,  37.5, 7.0, "DynamicProduct.cs", ["PhysX Rigidbodies & Motion", "Align Positions on Sensor Events"], '#f5f3ff', '#a855f7', t_fs=8.8, b_fs=7.2)

    draw_arrow(ax, (26.2, 20.0), (26.2, 19.0), style='->', lw=1.3)
    draw_arrow(ax, (26.2, 12.0), (26.2, 11.0), style='->', lw=1.3)

    rect_f = patches.FancyBboxPatch((53.0, 3.5), 41.5, 27.5, boxstyle="round,pad=0.4,rounding_size=1.2",
                                    facecolor='#ffffff', edgecolor='#ef4444', linewidth=1.5, zorder=2)
    ax.add_patch(rect_f)
    ax.text(55.0, 28.5, "Modular FMS Physical Testbed", fontsize=9.8, fontweight='bold', color='#dc2626', zorder=3)

    draw_card(ax, 55.0, 20.0, 37.5, 7.0, "Arduino Mega 2560", ["FreeRTOS Multi-Tasking", "Process I/O Signals & TCP"], '#fef2f2', '#ef4444', t_fs=8.8, b_fs=7.2)
    draw_card(ax, 55.0, 12.0, 37.5, 7.0, "Sensor Array (Port I)", ["Optical & Proximity Sensors", "Optocoupled Input Pins"], '#fef2f2', '#ef4444', t_fs=8.8, b_fs=7.2)
    draw_card(ax, 55.0, 4.0,  37.5, 7.0, "Actuator Array (Port R)", ["Conveyor Motors & Relays", "Pneumatic Diverters"], '#fef2f2', '#ef4444', t_fs=8.8, b_fs=7.2)

    draw_arrow(ax, (73.7, 20.0), (73.7, 19.0), style='->', lw=1.3)
    draw_arrow(ax, (73.7, 12.0), (73.7, 11.0), style='->', lw=1.3)

    # Bus Channels
    ax.plot([81, 81, 19, 19], [78.5, 75.0, 75.0, 68.5], color='#1d4ed8', lw=1.8, zorder=5)
    ax.annotate('', xy=(19, 68.5), xytext=(19, 70.0),
                arrowprops=dict(arrowstyle='->', color='#1d4ed8', lw=1.8, shrinkA=0, shrinkB=2), zorder=5)
    draw_badge(ax, 50, 75.0, "HTTP POST /upload (.aasx)", color='#1d4ed8', fs=8.5)

    draw_arrow(ax, (11, 54.0), (11, 31.0), color='#15803d', style='<->', lw=1.8)
    draw_badge(ax, 11, 36.0, "HTTP REST (Polling)", color='#15803d', fs=7.8)

    draw_arrow(ax, (47.0, 15.5), (53.0, 15.5), style='<->', lw=2.0, color='#b91c1c')
    draw_badge(ax, 50.0, 15.5, "Raw TCP Stream\n(:8888)", color='#b91c1c', fs=7.2)

    save_fig(fig, "architecture_global")

# =============================================================================
# 2. AAS METAMODEL & CUSTOM SUBMODELS (FORMAL UML CLASS DIAGRAM)
# =============================================================================
# =============================================================================
# 2. AAS METAMODEL & CUSTOM SUBMODELS (FORMAL UML CLASS DIAGRAM)
# =============================================================================
def make_aas_metamodel_submodels():
    fig, ax = plt.subplots(figsize=(16.0, 11.0), dpi=300)
    ax.set_xlim(0, 120); ax.set_ylim(0, 100); ax.axis('off')

    c_border = '#0f172a'
    header_bg = '#f1f5f9'

    # 1. Root class — centred in 120-unit canvas (x: 28..92, w=64)
    draw_uml_class(ax, 28, 81.0, 64, 16.0, "DigitalTwin", stereotype=None,
                   attributes=[
                       "+ id: String [1]",
                       "+ assetKind: AssetKind [1]",
                       "+ description: String [0..1]"
                   ],
                   operations=None,
                   bg='#ffffff', border=c_border, t_fs=9.2, b_fs=7.5, header_bg='#e2e8f0', header_h=4.2)

    # Composition lines from Root to Submodels
    draw_uml_composition(ax, (60, 81.0), (60, 75.0), mult_parent="1", mult_child="", color=c_border, lw=1.4)

    # Bus line to Row 1 (y = 75.0)
    # Left branch → VisualStructure centre x = 14.5 (2 + 25/2)
    # Right branch → VirtualPins centre x = 74 (64 + 20/2)
    ax.plot([14.5, 74.0], [75.0, 75.0], color=c_border, lw=1.4)
    ax.plot([14.5, 14.5], [75.0, 70.0], color=c_border, lw=1.4)
    ax.text(15.7, 71.5, "1", fontsize=7.6, fontweight='bold', color=c_border)
    ax.plot([74.0, 74.0], [75.0, 70.0], color=c_border, lw=1.4)
    ax.text(75.2, 71.5, "1", fontsize=7.6, fontweight='bold', color=c_border)

    # Bus line down to Row 2 & Row 3
    # Left branch → BehaviorMapping centre x = 14
    # Right branch → AssetInterfacesDescription centre x = 91
    ax.plot([60, 60], [75.0, 42.0], color=c_border, lw=1.4)
    ax.plot([14.0, 91.0], [42.0, 42.0], color=c_border, lw=1.4)
    ax.plot([14.0, 14.0], [42.0, 37.0], color=c_border, lw=1.4)
    ax.text(15.2, 38.5, "1", fontsize=7.6, fontweight='bold', color=c_border)
    ax.plot([91.0, 91.0], [42.0, 37.0], color=c_border, lw=1.4)
    ax.text(92.2, 38.5, "1", fontsize=7.6, fontweight='bold', color=c_border)

    # Down to Row 3 (ControlLogic)
    ax.plot([60, 60], [42.0, 16.0], color=c_border, lw=1.4)
    ax.text(61.5, 17.5, "0..1", fontsize=7.6, fontweight='bold', color=c_border)

    # =========================================================================
    # ROW 1 (y: 53.0 to 70.0)
    # Left group: VisualStructure → SceneObject → Transform
    # Right group: VirtualPins → PinGroup → Pin
    # Spacing: gap=2 between each box
    # VS: x=2..27 (w=25), SO: x=29..45 (w=16), TR: x=47..58 (w=11)
    # VP: x=64..82 (w=18), PG: x=84..96 (w=12), PN: x=98..117 (w=19)
    # =========================================================================
    # VisualStructure (x: 2, w=25)
    draw_uml_class(ax, 2, 53.0, 25, 17.0, "VisualStructure", stereotype=None,
                   attributes=[
                       "+ idShort: String [1]",
                       "+ description: String [0..1]"
                   ],
                   operations=None,
                   bg='#ffffff', border=c_border, t_fs=8.5, b_fs=7.1, header_bg=header_bg, header_h=4.0)

    # SceneObject (x: 29, w=16)
    draw_uml_class(ax, 29, 53.0, 16, 17.0, "SceneObject", stereotype=None,
                   attributes=[
                       "+ mesh: File [1]",
                       "+ parent: String [0..1]",
                       "+ dynamic: Boolean [1]"
                   ],
                   operations=None,
                   bg='#ffffff', border=c_border, t_fs=8.2, b_fs=6.8, header_bg=header_bg, header_h=4.0)

    # Composition VisualStructure -> SceneObject
    draw_uml_composition(ax, (27, 61.5), (29, 61.5), mult_parent="1", mult_child="1..*", color=c_border, lw=1.3,
                         mult_parent_offset=(1.2, 1.4), mult_child_offset=(-2.8, 1.4))

    # Transform (x: 48, w=13)
    draw_uml_class(ax, 48, 53.0, 13, 17.0, "Transform", stereotype=None,
                   attributes=[
                       "+ pos: Vector3 [1]",
                       "+ rot: Vector3 [1]",
                       "+ scale: Vector3 [1]"
                   ],
                   operations=None,
                   bg='#ffffff', border=c_border, t_fs=8.2, b_fs=6.8, header_bg=header_bg, header_h=4.0)

    # Composition SceneObject -> Transform
    draw_uml_composition(ax, (45, 61.5), (48, 61.5), mult_parent="1", mult_child="1", color=c_border, lw=1.3,
                         mult_parent_offset=(1.0, 1.4), mult_child_offset=(-2.0, 1.4))

    # VirtualPins (x: 64, w=20)
    draw_uml_class(ax, 64, 53.0, 20, 17.0, "VirtualPins", stereotype=None,
                   attributes=[
                       "+ idShort: String [1]",
                       "+ description: String [0..1]"
                   ],
                   operations=None,
                   bg='#ffffff', border=c_border, t_fs=8.5, b_fs=7.1, header_bg=header_bg, header_h=4.0)

    # PinGroup (x: 88, w=14)
    draw_uml_class(ax, 88, 53.0, 14, 17.0, "PinGroup", stereotype=None,
                   attributes=[
                       "+ direction: PinDirection [1]",
                       "  {IN, OUT}"
                   ],
                   operations=None,
                   bg='#ffffff', border=c_border, t_fs=8.2, b_fs=7.0, header_bg=header_bg, header_h=4.0)

    # Composition VirtualPins -> PinGroup
    draw_uml_composition(ax, (84, 61.5), (88, 61.5), mult_parent="1", mult_child="2", color=c_border, lw=1.3,
                         mult_parent_offset=(1.0, 1.4), mult_child_offset=(-2.0, 1.4))

    # Pin (x: 104, w=15)
    draw_uml_class(ax, 104, 53.0, 15, 17.0, "Pin", stereotype=None,
                   attributes=[
                       "+ name: String [1]",
                       "+ value: Boolean [1]"
                   ],
                   operations=None,
                   bg='#ffffff', border=c_border, t_fs=8.2, b_fs=7.0, header_bg=header_bg, header_h=4.0)

    # Composition PinGroup -> Pin
    draw_uml_composition(ax, (102, 61.5), (104, 61.5), mult_parent="1", mult_child="1..*", color=c_border, lw=1.3,
                         mult_parent_offset=(1.0, 1.4), mult_child_offset=(-2.6, 1.4))

    # =========================================================================
    # ROW 2 (y: 21.0 to 37.0): BehaviorMapping + BehaviorBinding | AssetInterfacesDescription
    # BM: x=2..26 (w=24), BB: x=28..52 (w=24), AID: x=58..118 (w=60)
    # =========================================================================
    draw_uml_class(ax, 2, 21.0, 24, 16.0, "BehaviorMapping", stereotype=None,
                   attributes=[
                       "+ idShort: String [1]",
                       "+ description: String [0..1]"
                   ],
                   operations=None,
                   bg='#ffffff', border=c_border, t_fs=8.5, b_fs=7.1, header_bg=header_bg, header_h=4.0)

    draw_uml_class(ax, 28, 21.0, 24, 16.0, "BehaviorBinding", stereotype=None,
                   attributes=[
                       "+ pinID: String [1]",
                       "+ component: String [1]",
                       "+ type: String [1]",
                       "+ parameters: Map<String, Any> [1]"
                   ],
                   operations=None,
                   bg='#ffffff', border=c_border, t_fs=8.2, b_fs=7.0, header_bg=header_bg, header_h=4.0)

    # Composition BehaviorMapping -> BehaviorBinding
    draw_uml_composition(ax, (26, 29.0), (28, 29.0), mult_parent="1", mult_child="1..*", color=c_border, lw=1.3,
                         mult_parent_offset=(1.2, 1.4), mult_child_offset=(-2.6, 1.4))

    draw_uml_class(ax, 58, 21.0, 60, 16.0, "AssetInterfacesDescription", stereotype=None,
                   attributes=[
                       "+ idShort: String [1]",
                       "+ description: String [0..1]",
                       "+ protocol: String [1]",
                       "+ endpointIP: String [1]",
                       "+ endpointPort: Integer [1]"
                   ],
                   operations=None,
                   bg='#ffffff', border=c_border, t_fs=8.5, b_fs=7.1, header_bg=header_bg, header_h=4.0)

    # =========================================================================
    # ROW 3 (y: 3.0 to 16.0): ControlLogic — centred x=30..90 (w=60)
    # =========================================================================
    draw_uml_class(ax, 30, 3.0, 60, 13.0, "ControlLogic", stereotype=None,
                   attributes=[
                       "+ idShort: String [1]",
                       "+ description: String [0..1]",
                       "+ rules: String [1]"
                   ],
                   operations=None,
                   bg='#ffffff', border=c_border, t_fs=8.6, b_fs=7.2, header_bg=header_bg, header_h=4.0)

    save_fig(fig, "aas_metamodel_submodels")



# =============================================================================
# 3. DUAL-MODE SEQUENCE DIAGRAM
# =============================================================================
def make_dual_mode_sequence():
    fig, ax = plt.subplots(figsize=(7.6, 6.2), dpi=300)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')

    # Panel A: Virtual Commissioning
    draw_group(ax, 2, 2, 47, 96, "Mode A: Virtual Commissioning", '#eff6ff', '#2563eb', fs=10.5, header_pos='top-center')
    ax.text(25.5, 92.5, "Standalone Simulation & Rule Evaluation", ha='center', va='center', fontsize=8.5, color='#1e40af')

    x_ph, x_vs, x_re, x_va = 7.5, 19.5, 31.5, 43.5
    for x, lbl in [(x_ph, "Unity\nPhysX"), (x_vs, "Virtual\nSensor"), (x_re, "Rule\nEngine"), (x_va, "Virtual\nActuator")]:
        draw_card(ax, x - 5.2, 81, 10.4, 8.5, lbl, bg='#ffffff', border='#2563eb', t_fs=8.2, lw=1.2)
        ax.plot([x, x], [81, 8], color='#93c5fd', lw=1.2, ls='--', zorder=2)

    draw_arrow(ax, (x_ph, 72), (x_vs, 72), color='#1d4ed8', lw=1.4)
    ax.text((x_ph+x_vs)/2, 74.5, "1. Workpiece trips sensor", ha='center', va='center', fontsize=8.0, fontweight='bold', color='#1e3a8a')

    draw_arrow(ax, (x_vs, 58), (x_re, 58), color='#1d4ed8', lw=1.4)
    ax.text((x_vs+x_re)/2, 60.5, "2. Sensor Pin turns ON", ha='center', va='center', fontsize=8.0, fontweight='bold', color='#1e3a8a')

    ax.plot([x_re, x_re+4.0, x_re+4.0, x_re], [47, 47, 42, 42], color='#1d4ed8', lw=1.4, zorder=5)
    ax.annotate('', xy=(x_re, 42), xytext=(x_re+1.5, 42), arrowprops=dict(arrowstyle='->', color='#1d4ed8', lw=1.4), zorder=5)
    ax.text(x_re+4.8, 44.5, "3. Match Rule", ha='left', va='center', fontsize=7.8, fontweight='bold', color='#1e3a8a')

    draw_arrow(ax, (x_re, 30), (x_va, 30), color='#1d4ed8', lw=1.4)
    ax.text((x_re+x_va)/2, 32.5, "4. Trigger Actuator Pin", ha='center', va='center', fontsize=8.0, fontweight='bold', color='#1e3a8a')

    draw_arrow(ax, (x_va, 16), (x_ph, 16), color='#1d4ed8', lw=1.4)
    ax.text((x_ph+x_va)/2, 18.5, "5. Stop Belt & Extend Stopper", ha='center', va='center', fontsize=8.0, fontweight='bold', color='#1e3a8a')

    # Panel B: Digital Twin
    draw_group(ax, 51, 2, 47, 96, "Mode B: Digital Twin Tracking", '#fff1f2', '#e11d48', fs=10.5, header_pos='top-center')
    ax.text(74.5, 92.5, "Hardware Sync (Rules Paused)", ha='center', va='center', fontsize=8.5, color='#9f1239')

    x_hw, x_ard, x_tcp, x_wp = 56.5, 68.5, 80.5, 92.5
    for x, lbl in [(x_hw, "Physical\nFMS"), (x_ard, "Arduino\nMega"), (x_tcp, "Unity\nTCP Link"), (x_wp, "3D\nTwin")]:
        draw_card(ax, x - 5.2, 81, 10.4, 8.5, lbl, bg='#ffffff', border='#e11d48', t_fs=8.2, lw=1.2)
        ax.plot([x, x], [81, 8], color='#fecdd3', lw=1.2, ls='--', zorder=2)

    draw_arrow(ax, (x_hw, 72), (x_ard, 72), color='#be123c', lw=1.4)
    ax.text((x_hw+x_ard)/2, 74.5, "6. Pallet trips optical sensor", ha='center', va='center', fontsize=7.8, fontweight='bold', color='#881337')

    ax.plot([x_ard, x_ard+4.0, x_ard+4.0, x_ard], [60, 60, 55, 55], color='#be123c', lw=1.4, zorder=5)
    ax.annotate('', xy=(x_ard, 55), xytext=(x_ard+1.5, 55), arrowprops=dict(arrowstyle='->', color='#be123c', lw=1.4), zorder=5)
    ax.text(x_ard+4.8, 57.5, "7. Detect change\n(Port I1_1)", ha='left', va='center', fontsize=7.5, fontweight='bold', color='#881337')

    draw_arrow(ax, (x_ard, 42), (x_tcp, 42), color='#be123c', lw=1.4)
    ax.text((x_ard+x_tcp)/2, 44.5, "8. Send JSON event via TCP", ha='center', va='center', fontsize=7.8, fontweight='bold', color='#881337')

    draw_arrow(ax, (x_tcp, 28), (x_wp, 28), color='#be123c', lw=1.4)
    ax.text((x_tcp+x_wp)/2, 30.5, "9. Forward sensor event", ha='center', va='center', fontsize=7.8, fontweight='bold', color='#881337')

    ax.plot([x_wp, x_wp-4.0, x_wp-4.0, x_wp], [17, 17, 12, 12], color='#be123c', lw=1.4, zorder=5)
    ax.annotate('', xy=(x_wp, 12), xytext=(x_wp-1.5, 12), arrowprops=dict(arrowstyle='->', color='#be123c', lw=1.4), zorder=5)
    ax.text(x_wp-4.8, 14.5, "10. Snap workpiece\nto station position", ha='right', va='center', fontsize=7.5, fontweight='bold', color='#881337')

    save_fig(fig, "dual_mode_sequence")

# =============================================================================
# 4. BASYX DOCKER TOPOLOGY (FORMAL UML DEPLOYMENT DIAGRAM)
# =============================================================================
def make_basyx_docker_topology():
    drawio_exe = r"C:\Program Files\draw.io\draw.io.exe"
    drawio_file = os.path.join(OUT_DIRS[0], "basyx_docker_topology.drawio")
    pdf_out = os.path.join(OUT_DIRS[0], "basyx_docker_topology.pdf")
    png_out = os.path.join(OUT_DIRS[0], "basyx_docker_topology.png")
    
    if os.path.exists(drawio_exe) and os.path.exists(drawio_file):
        import subprocess
        subprocess.run([drawio_exe, "--export", "--format", "pdf", "--output", pdf_out, drawio_file], check=True)
        subprocess.run([drawio_exe, "--export", "--format", "png", "--output", png_out, drawio_file], check=True)
        print("[OK] Exported draw.io topology: basyx_docker_topology.drawio -> .pdf / .png")
    else:
        print("[WARN] draw.io.exe or basyx_docker_topology.drawio not found")

# =============================================================================
# 5. UNITY SCENE HIERARCHY
# =============================================================================
def make_unity_scene_hierarchy():
    fig, ax = plt.subplots(figsize=(7.6, 7.2), dpi=300)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')

    c_purple = '#9333ea'

    # Tier 1: Singletons
    draw_group(ax, 3, 77.0, 94, 21.0, "1. Core Scene Managers (Singletons)", '#f5f3ff', c_purple, fs=9.8)
    draw_card(ax, 5.5,  78.5, 20.5, 15.5, "BaSyxManager\n.cs", 
              ["• Discover AAS Assets", "• Poll REST API (:8081)", "• Build 3D Objects"], bg='#ffffff', border=c_purple, t_fs=8.5, b_fs=7.2)
    draw_card(ax, 29.5, 78.5, 20.5, 15.5, "OperationMode\nManager.cs", 
              ["• Dual-Mode Switch", "• Virtual Comm vs DT", "• Rule Engine State"], bg='#ffffff', border=c_purple, t_fs=8.5, b_fs=7.2)
    draw_card(ax, 53.5, 78.5, 20.5, 15.5, "AASArduinoLink\n.cs", 
              ["• TCP Socket (:8888)", "• Read Live Stream", "• Dispatch Pin Events"], bg='#ffffff', border=c_purple, t_fs=8.5, b_fs=7.2)
    draw_card(ax, 77.5, 78.5, 17.5, 15.5, "ModeUI\nController.cs", 
              ["• On-Screen UI / HUD", "• Toggle Mode Button", "• Sensor Pin Status"], bg='#ffffff', border=c_purple, t_fs=8.5, b_fs=7.2)

    # Tier 2: Procedural AAS Instances
    draw_group(ax, 3, 25.0, 94, 44.0, "2. Procedural AAS Objects (Generated at Runtime)", '#ffffff', '#0284c7', fs=10.0)

    # Conveyor System Kit (2x2 grid)
    draw_group(ax, 5.5, 26.5, 53, 33.0, "Conveyor System Kit (AASKitImporter.cs)", '#f0f9ff', '#0284c7', fs=8.8, lw=1.3)
    draw_card(ax, 7.5,  43.5, 23.5, 12.5, "3D Mesh Hierarchy\n(Base, Rails & Belt)", ["Mesh Colliders", "Transform Tree"], bg='#ffffff', border='#0284c7', t_fs=8.0, b_fs=7.0)
    draw_card(ax, 33.5, 43.5, 23.0, 12.5, "AASSensorController\n(Port I Inputs)", ["Optical Breakbeams", "Collider Triggers"], bg='#ffffff', border='#0284c7', t_fs=8.0, b_fs=7.0)
    draw_card(ax, 7.5,  28.0, 23.5, 12.5, "AASRuleEngine\n(Virtual Comm)", ["Local Rules", "IF/THEN Logic"], bg='#ffffff', border='#0284c7', t_fs=8.0, b_fs=7.0)
    draw_card(ax, 33.5, 28.0, 23.0, 12.5, "AASActuatorController\n(Port R Outputs)", ["Belt Surface Velocity", "Stopper Pneumatics"], bg='#ffffff', border='#0284c7', t_fs=8.0, b_fs=7.0)

    draw_arrow(ax, (31.0, 49.7), (33.5, 49.7), style='->', lw=1.2)
    draw_arrow(ax, (45.0, 43.5), (45.0, 40.5), style='->', lw=1.2)
    draw_arrow(ax, (33.5, 34.2), (31.0, 34.2), style='<-', lw=1.2)

    # Robotic Arm Twin
    draw_group(ax, 61.0, 26.5, 34.0, 33.0, "Robotic Arm Twin (AASUrdfImporter.cs)", '#fff7ed', '#ea580c', fs=8.8, lw=1.3)
    draw_card(ax, 63.0, 43.5, 30.0, 12.5, "URDF Articulation Chain\nKinematic Joints", ["6-DOF Articulation Bodies", "Link Meshes & Colliders"], bg='#ffffff', border='#ea580c', t_fs=8.0, b_fs=7.0)
    draw_card(ax, 63.0, 28.0, 30.0, 12.5, "AASRobotSync.cs\nJoint Telemetry", ["Live Joint Angles", "Smooth Interpolation"], bg='#ffffff', border='#ea580c', t_fs=8.0, b_fs=7.0)
    draw_arrow(ax, (78.0, 43.5), (78.0, 40.5), style='<->', lw=1.2)

    # Tier 3: Dynamic Workpieces
    draw_group(ax, 3, 2.0, 94, 17.0, "3. Workpieces & Physics Layer (PhysX)", '#f0fdf4', '#16a34a', fs=9.8)
    draw_card(ax, 6, 3.5, 88, 12.0, "DynamicProduct.cs (Pallets & Workpieces)",
              ["• Rigidbody Physics & Surface Friction (conveyance along active belt speed)",
               "• Smooth Position Snapping on Sensor Events (I1_1) to eliminate physics drift"],
              bg='#ffffff', border='#16a34a', t_fs=8.8, b_fs=7.4, align='center')

    # Inter-tier arrows
    draw_arrow(ax, (15.5, 77.0), (15.5, 59.5), color='#9333ea', lw=1.5)
    draw_badge(ax, 21.0, 73.0, "Builds Scene Objects", color='#9333ea', fs=7.3)

    draw_arrow(ax, (63.5, 77.0), (45.0, 59.5), color='#b91c1c', lw=1.5)
    draw_badge(ax, 58.0, 73.0, "Forward Pin Event (I1_1)", color='#b91c1c', fs=7.3)

    draw_arrow(ax, (32.0, 25.0), (32.0, 19.0), color='#16a34a', lw=1.5)
    draw_badge(ax, 48.0, 22.0, "PhysX Conveyance Interaction", color='#16a34a', fs=7.5)

    save_fig(fig, "unity_scene_hierarchy")

if __name__ == "__main__":
    make_architecture_global()
    make_aas_metamodel_submodels()
    make_dual_mode_sequence()
    make_basyx_docker_topology()
    make_unity_scene_hierarchy()
    print("Batch 1 updated successfully.")
