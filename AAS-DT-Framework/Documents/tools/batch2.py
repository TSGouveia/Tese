import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thesis_art_utils import *

# =============================================================================
# 6. ARDUINO FREERTOS SCHEMA
# =============================================================================
def make_arduino_freertos_schema():
    fig, ax = plt.subplots(figsize=(7.6, 7.2), dpi=300)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')

    c_red = '#b91c1c'
    c_green = '#15803d'

    # Tier 1: Hardware I/O
    draw_group(ax, 3, 79.0, 94, 19.5, "1. Microcontroller & Physical Hardware (Arduino Mega 2560)", '#fef2f2', c_red, fs=10.0)
    draw_card(ax, 5.5,  80.5, 26.0, 14.5, "Sensor Array (Port I)\nInputs I0_0 .. I2_5", 
              ["• Optical Breakbeams (880nm)", "• Inductive Proximity Sensors", "• PC817 Optocoupler Board"], bg='#ffffff', border=c_red, t_fs=8.5, b_fs=7.2)
    draw_card(ax, 37.0, 80.5, 26.0, 14.5, "Actuator Array (Port R)\nOutputs R0_2 .. R2_8", 
              ["• 24V DC Geared Motors", "• Pneumatic Stoppers & Gates", "• Opto-Isolated Relays"], bg='#ffffff', border=c_red, t_fs=8.5, b_fs=7.2)
    draw_card(ax, 68.5, 80.5, 26.0, 14.5, "W5100 Ethernet Shield\nIP: 192.168.10.1", 
              ["• Hardware TCP/IP Stack", "• SPI Bus to Mega 2560", "• Shielded RJ45 Port"], bg='#ffffff', border=c_red, t_fs=8.5, b_fs=7.2)

    # Tier 2: FreeRTOS Kernel
    draw_group(ax, 3, 26.5, 94, 46.0, "2. FreeRTOS Tasks & Message Queues", '#f0fdf4', c_green, fs=10.0)

    # Section 1: Tasks
    ax.text(6.0, 68.2, "Concurrent Real-Time Tasks", fontsize=9.2, fontweight='bold', color=c_green, zorder=3)
    draw_card(ax, 5.5,  49.5, 21.0, 17.5, "TaskSensores\n(Priority 3)", 
              ["• 10ms Scan Period", "• Read Port I Inputs", "• Push to Event Queue"], bg='#ffffff', border='#2563eb', t_fs=8.5, b_fs=7.2)
    draw_card(ax, 28.5, 49.5, 21.0, 17.5, "TaskEnvio\n(Priority 2)", 
              ["• Read Event Queue", "• Format JSON Packet", "• Send via TCP Socket"], bg='#ffffff', border='#2563eb', t_fs=8.5, b_fs=7.2)
    draw_card(ax, 51.5, 49.5, 21.0, 17.5, "TaskDigitalshadow\n(Priority 1)", 
              ["• TCP Server (:8888)", "• Watchdog Timer", "• Handle Reconnects"], bg='#ffffff', border='#2563eb', t_fs=8.5, b_fs=7.2)
    draw_card(ax, 74.5, 49.5, 20.5, 17.5, "TaskTripa\n(Priority 1)", 
              ["• HTTP Server (:80)", "• URL REST Parser", "• Execute Actuation"], bg='#ffffff', border='#2563eb', t_fs=8.5, b_fs=7.2)

    # Section 2: IPC & Shared State
    ax.text(6.0, 41.0, "Inter-Process Communication (IPC)", fontsize=9.0, fontweight='bold', color='#b45309', zorder=3)
    draw_card(ax, 7.5,  28.0, 26.0, 11.5, "Queue: envio (FIFO)\nBuffer: 30 elements", 
              ["Thread-safe event queue"], bg='#ffffff', border='#d97706', t_fs=8.2, b_fs=7.0)
    draw_card(ax, 37.0, 28.0, 26.0, 11.5, "mutex_envio\nSemaphoreMutex", 
              ["Protects TCP write access"], bg='#ffffff', border='#d97706', t_fs=8.2, b_fs=7.0)
    draw_card(ax, 66.5, 28.0, 28.0, 11.5, "Shared Bitfields\nporto_I & porto_R", 
              ["Atomic I/O state registers"], bg='#ffffff', border='#d97706', t_fs=8.2, b_fs=7.0)

    # Task & IPC Links
    draw_arrow(ax, (16.0, 49.5), (20.5, 39.5), color='#d97706', lw=1.3)
    draw_badge(ax, 16.0, 45.2, "Push", color='#d97706', fs=7.2)

    draw_arrow(ax, (25.5, 39.5), (34.0, 49.5), color='#d97706', lw=1.3)
    draw_badge(ax, 31.0, 45.2, "Pop", color='#d97706', fs=7.2)

    draw_arrow(ax, (39.0, 49.5), (48.0, 39.5), color='#d97706', lw=1.3, dashed=True)
    draw_badge(ax, 45.0, 45.2, "Lock", color='#d97706', fs=7.2)

    # Tier 3: Network Peers
    draw_group(ax, 3, 2.0, 94, 18.0, "3. Network Communication Peers", '#f5f3ff', '#9333ea', fs=10.0)
    draw_card(ax, 10.0, 3.5, 38.0, 13.0, "Unity 3D Simulation Client\nTCP Socket Stream (:8888)", 
              ["• Real-time sensor events: {'Port':'I1_1','Value':1}",
               "• Low-latency stream (< 10ms) for pose snapping"], bg='#ffffff', border='#9333ea', t_fs=8.5, b_fs=7.2)
    draw_card(ax, 52.0, 3.5, 38.0, 13.0, "BaSyx / Management\nHTTP REST Endpoint (:80)", 
              ["• Control calls: GET/POST /passadeiras?motor=R0_2&state=1",
               "• Standard actuator status & commands"], bg='#ffffff', border='#9333ea', t_fs=8.5, b_fs=7.2)

    # Inter-tier arrows
    draw_arrow(ax, (18.5, 80.5), (16.0, 67.0), color='#b91c1c', lw=1.4)
    draw_badge(ax, 17.5, 75.75, "digitalRead()", color='#b91c1c', fs=7.2)

    draw_arrow(ax, (84.5, 67.0), (50.0, 80.5), color='#b91c1c', lw=1.4)
    draw_badge(ax, 67.5, 75.75, "digitalWrite()", color='#b91c1c', fs=7.2)

    draw_arrow(ax, (39.0, 49.5), (29.0, 16.5), color='#9333ea', lw=1.5)
    draw_badge(ax, 32.0, 23.25, "TCP Stream JSON", color='#9333ea', fs=7.5)

    draw_arrow(ax, (71.0, 16.5), (84.5, 49.5), color='#9333ea', lw=1.4, dashed=True)
    draw_badge(ax, 79.0, 23.25, "HTTP REST Calls", color='#9333ea', fs=7.5)

    save_fig(fig, "arduino_freertos_schema")

# =============================================================================
# 7. FMS PHYSICAL BENCH
# =============================================================================
def make_fms_physical_bench():
    fig, ax = plt.subplots(figsize=(7.6, 6.0), dpi=300)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')

    c_blue = '#1d4ed8'
    c_amber = '#b45309'

    draw_group(ax, 2, 2, 67, 96, "Modular Closed-Loop Track Layout", '#f8fafc', c_blue, fs=10.5)

    # Top Row: Station A -> Conveyor AB -> Station B
    draw_card(ax, 4.5,  74, 18.0, 18.0, "Station A\n(Infeed)\nSensor I0_0\nMotor R0_2", bg='#eff6ff', border=c_blue, t_fs=7.4, lw=1.2)
    draw_card(ax, 26.5, 77, 18.0, 12.0, "Conveyor AB\nMotor R0_3", bg='#f0fdf4', border='#16a34a', t_fs=7.4, lw=1.2)
    draw_card(ax, 48.5, 74, 18.0, 18.0, "Station B\n(Inspect)\nSensor I0_3\nStopper R0_4", bg='#eff6ff', border=c_blue, t_fs=7.4, lw=1.2)

    draw_arrow(ax, (22.5, 83), (26.5, 83), style='->', lw=1.8, color='#1e3a8a')
    draw_arrow(ax, (44.5, 83), (48.5, 83), style='->', lw=1.8, color='#1e3a8a')

    # Right Column: Station C -> Conveyor CD -> Station D
    draw_card(ax, 48.5, 43, 18.0, 24.0, "Station C\n(Drill)\nSensor I0_5\nSpindle R0_7\nZ-Axis R0_8", bg='#eff6ff', border=c_blue, t_fs=7.4, lw=1.2)
    draw_card(ax, 48.5, 25, 18.0, 12.0, "Conveyor CD\nMotor R1_2", bg='#f0fdf4', border='#16a34a', t_fs=7.4, lw=1.2)
    draw_card(ax, 48.5, 5,  18.0, 16.0, "Station D\n(Screw)\nSensor I1_2\nTool R1_3\nFeed R1_4", bg='#eff6ff', border=c_blue, t_fs=7.4, lw=1.2)

    draw_arrow(ax, (57.5, 74), (57.5, 67), style='->', lw=1.8, color='#1e3a8a')
    draw_arrow(ax, (57.5, 43), (57.5, 37), style='->', lw=1.8, color='#1e3a8a')
    draw_arrow(ax, (57.5, 25), (57.5, 21), style='->', lw=1.8, color='#1e3a8a')

    # Bottom Row: Station D -> Station E -> Station F
    draw_card(ax, 26.5, 5, 18.0, 16.0, "Station E\n(Buffer)\nSensor I1_5\nStopper R1_6", bg='#eff6ff', border=c_blue, t_fs=7.4, lw=1.2)
    draw_card(ax, 4.5,  5, 18.0, 16.0, "Station F\n(Outfeed)\nSensor I2_2", bg='#eff6ff', border=c_blue, t_fs=7.4, lw=1.2)

    draw_arrow(ax, (48.5, 13), (44.5, 13), style='->', lw=1.8, color='#1e3a8a')
    draw_arrow(ax, (26.5, 13), (22.5, 13), style='->', lw=1.8, color='#1e3a8a')

    # Left Column: Return Conveyors EF / FA
    draw_card(ax, 4.5, 25, 18.0, 12.0, "Conveyor EF\nMotor R1_8\nSensor I2_1", bg='#f0fdf4', border='#16a34a', t_fs=7.4, lw=1.2)
    draw_card(ax, 4.5, 43, 18.0, 24.0, "Conveyor FA\nMotor R2_3\nSensor I2_4", bg='#f0fdf4', border='#16a34a', t_fs=7.4, lw=1.2)

    draw_arrow(ax, (13.5, 21), (13.5, 25), style='->', lw=1.8, color='#1e3a8a')
    draw_arrow(ax, (13.5, 37), (13.5, 43), style='->', lw=1.8, color='#1e3a8a')
    draw_arrow(ax, (13.5, 67), (13.5, 74), style='->', lw=1.8, color='#1e3a8a')

    # Side Column: Control Cabinet & Power
    draw_group(ax, 71, 2, 27, 96, "Control Cabinet & Power", '#fffbeb', c_amber, fs=9.5)
    draw_card(ax, 73.0, 72, 23.0, 20.0, "Arduino Mega 2560\nController Board", 
              ["• FreeRTOS Firmware", "• 16MHz ATmega2560", "• Real-Time Control"], bg='#ffffff', border=c_amber, t_fs=8.5, b_fs=7.2)
    draw_card(ax, 73.0, 48, 23.0, 20.0, "W5100 Ethernet\nNetwork Shield", 
              ["• IP: 192.168.10.1", "• TCP Socket :8888", "• HTTP Server :80"], bg='#ffffff', border=c_amber, t_fs=8.5, b_fs=7.2)
    draw_card(ax, 73.0, 24, 23.0, 20.0, "Opto-Isolated\nTerminal Boards", 
              ["• Port I: 24V Inputs", "• Port R: 24V Relays", "• Electrical Isolation"], bg='#ffffff', border=c_amber, t_fs=8.5, b_fs=7.2)
    draw_card(ax, 73.0, 5,  23.0, 15.0, "Power Supply\n24V DC / 10A", 
              ["Industrial DIN Rail PSU"], bg='#ffffff', border=c_amber, t_fs=8.5, b_fs=7.2)

    draw_arrow(ax, (73.0, 50.0), (67.0, 50.0), color=c_amber, style='<->', lw=1.8)
    draw_badge(ax, 69.5, 54.5, "Field I/O", color=c_amber, fs=7.5)

    save_fig(fig, "fms_physical_bench")

# =============================================================================
# 8. FMS SENSOR & ACTUATOR DETAILS
# =============================================================================
def make_fms_sensor_actuator_details():
    fig, ax = plt.subplots(figsize=(7.6, 6.2), dpi=300)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')

    draw_group(ax, 2, 2, 96, 96, "Physical Sensors, Actuators & Interface Boards", '#f8fafc', '#334155', fs=10.5)

    # Column 1: Detection Sensors (Port I)
    draw_group(ax, 4, 4, 30, 89, "1. Sensors (Port I)", '#eff6ff', '#2563eb', fs=9.5)
    draw_card(ax, 6, 49, 26, 40, "Optical Breakbeam\nSensor", 
              ["• Infrared 880nm Beam",
               "• Polarized Reflective",
               "• Fast Response (< 2.5ms)",
               "• Active-Low NPN Signal",
               "• Detects pallet edges"], bg='#ffffff', border='#2563eb', t_fs=9.0, b_fs=7.5, align='left')
    draw_card(ax, 6, 6, 26, 39, "Inductive Proximity\nSensor", 
              ["• M12 Threaded Body",
               "• 4 mm Sensing Range",
               "• 24V DC PNP Output",
               "• Detects metal pucks",
               "• Confirms station stop"], bg='#ffffff', border='#2563eb', t_fs=9.0, b_fs=7.5, align='left')

    # Column 2: Motion Actuators (Port R)
    draw_group(ax, 35, 4, 30, 89, "2. Actuators (Port R)", '#fefce8', '#ca8a04', fs=9.5)
    draw_card(ax, 37, 49, 26, 40, "Conveyor 24V DC\nGeared Motor", 
              ["• Planetary Gear Drive",
               "• 120 RPM (0.15 m/s)",
               "• Torque: 1.8 N·m",
               "• Flyback Protection Diode",
               "• Drives conveyor belt"], bg='#ffffff', border='#ca8a04', t_fs=9.0, b_fs=7.5, align='left')
    draw_card(ax, 37, 6, 26, 39, "Pneumatic Diverters\n& Station Stoppers", 
              ["• Double-Acting Cylinders",
               "• 4 - 6 bar Air Pressure",
               "• 24V Solenoid Valves",
               "• Spring Return Action",
               "• Holds pallets at stations"], bg='#ffffff', border='#ca8a04', t_fs=9.0, b_fs=7.5, align='left')

    # Column 3: Isolation & Networking
    draw_group(ax, 66, 4, 30, 89, "3. Interface Stage", '#f0fdf4', '#16a34a', fs=9.5)
    draw_card(ax, 68, 63, 26, 26, "PC817 Optocouplers\nInput Stage", 
              ["• 24V Field -> 5V MCU", "• 5000 Vrms Isolation", "• Eliminates noise & spikes"], bg='#ffffff', border='#16a34a', t_fs=8.5, b_fs=7.4, align='left')
    draw_card(ax, 68, 34, 26, 26, "Opto-Isolated Relays\nOutput Driver Stage", 
              ["• 5V Logic -> 24V Power", "• Transistor Buffer Driver", "• LED Status Indicators"], bg='#ffffff', border='#16a34a', t_fs=8.5, b_fs=7.4, align='left')
    draw_card(ax, 68, 6,  26, 25, "W5100 Ethernet\nNetwork Controller", 
              ["• Hardware TCP/IP Stack", "• SPI Connection to MCU", "• Shielded RJ45 Port"], bg='#ffffff', border='#16a34a', t_fs=8.5, b_fs=7.4, align='left')

    save_fig(fig, "fms_sensor_actuator_details")

# =============================================================================
# 9. CONVEYOR WIZARD UI & WORKFLOW
# =============================================================================
def make_wizard_ui_screenshots():
    fig, ax = plt.subplots(figsize=(7.6, 5.8), dpi=300)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')

    c_blue = '#0284c7'
    c_purple = '#9333ea'

    # Top: 5-Step Pipeline
    draw_group(ax, 2, 44, 96, 54, "Conveyor Wizard 5-Step Workflow (conveyor_wizard.py)", '#ffffff', c_blue, fs=10.5)
    steps_data = [
        ("Step 1\n3D Model", ["• Load GLB / URDF", "• 3D Viewport", "• Part Hierarchy"]),
        ("Step 2\nTransform", ["• Pos, Rot, Scale", "• Protocol: TCP", "• IP & Port :8888"]),
        ("Step 3\nSensors", ["• Place Input Pins", "• Active-Low Option", "• Align Workpiece"]),
        ("Step 4\nActuators", ["• Assign Output Pins", "• Set Belt Speed", "• Stopper Motion"]),
        ("Step 5\nDeploy", ["• Build .aasx Package", "• Upload to BaSyx", "• Check for Errors"]),
    ]
    xs = [4.5, 23.5, 42.5, 61.5, 80.5]
    for i, (st, lines) in enumerate(steps_data):
        draw_card(ax, xs[i], 46.5, 16.5, 46, st, lines, bg='#f0f9ff', border=c_blue, t_fs=8.8, b_fs=7.4, align='left')
        if i < 4:
            draw_arrow(ax, (xs[i] + 16.5, 69.5), (xs[i+1], 69.5), style='->', lw=1.8, color=c_blue)

    # Bottom: Integrated Studios
    draw_group(ax, 2, 2, 96, 39, "Additional Editors", '#faf5ff', c_purple, fs=10.0)
    draw_card(ax, 4.5, 4.0, 44.0, 31.0, "Rule Editor Dialog\n(AASRulesEditorDialog)", 
              ["• Create IF/THEN rules for simulation",
               "• Example: IF Sensor == ON THEN Motor = RUN",
               "• Set action delays (e.g. 500ms)",
               "• Saved into ControlLogic submodel"], bg='#ffffff', border=c_purple, t_fs=8.8, b_fs=7.2, align='left')
    draw_card(ax, 51.5, 4.0, 44.0, 31.0, "3D Layout Preview\nStudio", 
              ["• Place multiple machines together",
               "• Align infeed and outfeed conveyors",
               "• Verify layout before deployment",
               "• Real-time inspection in PyVista 3D"], bg='#ffffff', border=c_purple, t_fs=8.8, b_fs=7.2, align='left')

    save_fig(fig, "wizard_ui_screenshots")

# =============================================================================
# 10. DUAL-LEVEL SYSTEM ARCHITECTURE (AAS_FMS vs AAS_CONVEYOR)
# =============================================================================
def make_system_architecture_real():
    fig, ax = plt.subplots(figsize=(12.0, 15.2), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    c_purple_bg = '#faf5ff'
    c_purple_bd = '#7e22ce'
    c_blue_bg = '#eff6ff'
    c_blue_bd = '#1d4ed8'
    c_amber_bg = '#fffbeb'
    c_amber_bd = '#b45309'

    # Title
    ax.text(50, 98.5, "Dual-Level AAS Digital Twin Architecture", 
            ha='center', va='center', fontsize=14, fontweight='bold', color='#0f172a')
    ax.text(50, 97.0, "Line-Level Orchestration (AAS_FMS) vs. Device-Level Assets (AAS_Conveyor_A) with Real Hardware Telemetry", 
            ha='center', va='center', fontsize=9.0, fontstyle='italic', color='#475569')

    # =========================================================================
    # LEVEL 1: LINE-LEVEL ORCHESTRATOR (AAS_FMS)
    # =========================================================================
    draw_group(ax, 3.0, 68.0, 94.0, 27.5, 
               "Level 1 · System-Level Shell: AAS_FMS (Line Orchestrator & Interlocks)", 
               c_purple_bg, c_purple_bd, fs=9.4, header_pos='top-left')
    ax.text(94.0, 93.6, "id: https://acplt.org/AAS_FMS", ha='right', va='center', fontsize=7.5, color='#6b21a8')

    # Submodel: ControlLogic container
    ax.add_patch(patches.FancyBboxPatch((5.0, 69.5), 90.0, 22.0, boxstyle="round,pad=0.0,rounding_size=0.8",
                                        facecolor='#ffffff', edgecolor='#a855f7', linewidth=1.2))
    ax.add_patch(patches.Rectangle((5.0, 88.0), 90.0, 3.5, facecolor='#f3e8ff', edgecolor='none'))
    ax.plot([5.0, 95.0], [88.0, 88.0], color='#a855f7', lw=1.0)
    ax.text(7.0, 89.7, "Submodel: ControlLogic (id: https://acplt.org/Submodels/ControlLogic_FMS)", fontsize=8.8, fontweight='bold', color='#6b21a8', va='center')
    ax.text(93.0, 89.7, "[Evaluated by AASRuleEngine.cs in Unity]", ha='right', fontsize=7.5, fontstyle='italic', color='#7e22ce', va='center')

    ax.text(7.0, 86.2, "Property: Rules (JSON-Structured Manufacturing Automation Sequences)", fontsize=8.2, fontweight='bold', color='#1e1b4b')

    # Sequence Cards
    # Card 1: Sequence A->B
    draw_card(ax, 6.5, 70.6, 43.0, 15.0, "Sequence: 'A->B' (Transfer Conveyor A -> B)",
              ["• Trigger (Operator: AND):",
               "  - Conveyor_A: Sensor_Product == true",
               "  - Conveyor_B: Sensor_Product == false",
               "  - Interlocks: [Rule] B->C, F->A == false",
               "• Ordered Steps:",
               "  1. call_http_service (POST /passadeiras?skill=AB)",
               "  2. if (Sensor_Left == true) -> set Conveyor_A_Left = true",
               "  3. wait_until (Sensor_Left == false, timeout: 2.0s)",
               "  4. set Conveyor_A_Out = true & Move_Conveyor_OUT = true (B)",
               "  5. wait_until (Sensor_Product in B == true) -> stop motors"],
              bg='#faf5ff', border='#c084fc', t_fs=7.6, b_fs=5.6, align='left', max_chars=65)

    # Card 2: Sequence C->D
    draw_card(ax, 50.5, 70.6, 43.0, 15.0, "Sequence: 'C->D' (Workstation Indexing & Punching)",
              ["• Trigger (Operator: AND):",
               "  - Conveyor_C: Conveyor_C_Product == true",
               "  - Conveyor_D: Sensor_Product == false",
               "  - Interlocks: [Rule] D->E, B->C == false",
               "• Ordered Steps:",
               "  1. call_http_service (POST /passadeiras?skill=CD)",
               "  2. Align table (Rotate CW/CCW until Sensor0 == false)",
               "  3. Transfer product to Conveyor_D",
               "  4. call_http_service (POST /estacao?skill=1)",
               "  5. Actuate Punch_FMS (Forward->Down->Rotate->Up->Back)"],
              bg='#faf5ff', border='#c084fc', t_fs=7.6, b_fs=5.6, align='left', max_chars=65)


    # Connector between ControlLogic and VirtualPins
    draw_arrow(ax, (38.0, 68.0), (38.0, 62.8), style='<->', lw=2.0, color=c_purple_bd)
    draw_badge(ax, 38.0, 65.4, "Evaluates Sensor States & Triggers Actuation Steps", color='#6b21a8', bg='#ede9fe', border='#c084fc', fs=7.0)

    # =========================================================================
    # LEVEL 2: DEVICE-LEVEL SHELL (AAS_Conveyor_A)
    # =========================================================================
    draw_group(ax, 3.0, 31.5, 94.0, 31.0,
               "Level 2 · Asset-Level Shell: AAS_Conveyor_A (Machine Twin Instance)",
               c_blue_bg, c_blue_bd, fs=9.4, header_pos='top-left')
    ax.text(94.0, 60.6, "id: https://acplt.org/AAS_Conveyor_A", ha='right', va='center', fontsize=7.5, color='#1d4ed8')

    # Submodel 1: VisualStructure
    draw_card(ax, 5.0, 33.0, 21.0, 24.8, "1. VisualStructure\n(Geometry & Transforms)",
              ["• Mesh File:",
               "  Conveyor_A_cloned.glb",
               "• DynamicObject: false",
               "• Coordinates:",
               "  - Pos: (-4.5, 0.0, 0.3)",
               "  - Rot: (0.0, 180.0, 0.0)",
               "  - Scale: (1.0, 1.0, 1.0)",
               "• Ingestion:",
               "  Procedural mesh baking"],
              bg='#ffffff', border='#3b82f6', t_fs=7.5, b_fs=6.2, align='left')

    # Submodel 2: VirtualPins
    draw_card(ax, 27.5, 33.0, 21.0, 24.8, "2. VirtualPins\n(Electrical I/O Telemetry)",
              ["Inputs (Live Sensors):",
               "• Sensor_Left: true",
               "• Sensor_Right: true",
               "• Sensor_Product: true",
               "",
               "Outputs (Actuators):",
               "• Conveyor_A_Left: true",
               "• Conveyor_A_Right: false",
               "• Conveyor_A_IN: false",
               "• Conveyor_A_Out: false",
               "",
               "• Live Boolean cache"],
              bg='#ffffff', border='#3b82f6', t_fs=7.5, b_fs=6.2, align='left')

    # Submodel 3: AssetInterfacesDescription
    draw_card(ax, 50.0, 33.0, 20.5, 24.8, "3. AssetInterfaces\n(Hardware Network Ports)",
              ["Network Configuration:",
               "• Protocol: Sockets",
               "  (Raw TCP byte stream)",
               "• EndpointIP: 192.168.10.1",
               "• EndpointPort: 8888",
               "",
               "Transport Semantics:",
               "• High-speed telemetry",
               "• Arduino Mega + W5100",
               "• Dispatches port updates",
               "  (e.g., I2_2, R1_8)"],
              bg='#ffffff', border='#3b82f6', t_fs=7.5, b_fs=6.2, align='left')

    # Submodel 4: BehaviorMapping
    draw_card(ax, 72.0, 33.0, 23.5, 24.8, "4. BehaviorMapping\n(Physics & Kinematics)",
              ["Actuator Kinematics:",
               "• Pin: Conveyor_A_Left",
               "  - Comp: 'Conveyor'",
               "  - Type: TranslateContinuous",
               "  - AxisY: 1.0 | Spd: 0.83",
               "  - RealPortID: R1_8 (Relay)",
               "",
               "Sensor Trigger Physics:",
               "• Pin: Sensor_Left",
               "  - Comp: 'Sensor_Left'",
               "  - Type: TriggerZone",
               "  - ActiveLow: true (NC)",
               "  - RealPortID: I2_2 (Input)",
               "  - MoveTarget: 'Conveyor'",
               "  - MovePosY: 0.11, PosZ: 4.7"],
              bg='#ffffff', border='#3b82f6', t_fs=7.5, b_fs=6.0, align='left')

    # Connectors between Level 2 and Level 3
    draw_arrow(ax, (15.5, 25.0), (15.5, 31.5), style='->', lw=1.6, color=c_blue_bd)
    draw_badge(ax, 15.5, 28.2, "Loads Mesh & Transforms", color='#1d4ed8', bg='#dbeafe', border='#93c5fd', fs=6.5)

    draw_arrow(ax, (83.5, 25.0), (83.5, 31.5), style='->', lw=1.6, color=c_blue_bd)
    draw_badge(ax, 83.5, 28.2, "Applies Kinematics & Ports", color='#1d4ed8', bg='#dbeafe', border='#93c5fd', fs=6.5)

    draw_arrow(ax, (60.5, 25.0), (60.5, 31.5), style='<->', lw=2.0, color='#dc2626')
    draw_badge(ax, 60.5, 28.2, "TCP Sockets (:8888)", color='#b91c1c', bg='#fee2e2', border='#fca5a5', fs=6.8)

    # =========================================================================
    # LEVEL 3: RUNTIME SYNCHRONIZATION (Unity 3D Simulation & Physical Plant)
    # =========================================================================
    draw_group(ax, 3.0, 3.0, 94.0, 22.0,
               "Level 3 · Runtime Execution: Unity 3D Digital Twin Engine & Physical Automation Plant",
               c_amber_bg, c_amber_bd, fs=9.4, header_pos='top-left')

    # Unity 3D Box
    draw_card(ax, 5.0, 4.8, 43.5, 16.5, "Unity 3D Simulation Engine (Virtual Commissioning / DT)",
              ["• BaSyxManager.cs: Queries GET /shells, discovers AAS & downloads .glb meshes",
               "• AASRuleEngine.cs: Evaluates ControlLogic JSON sequences in a 10 Hz coroutine",
               "• AASActuatorController.cs: Translates outputs to TranslateContinuous surface motion",
               "• AASSensorController.cs: Simulates TriggerZone collision filters & SnapTarget positioning",
               "• AASArduinoLink.cs: TCP Socket client mapping hardware events (I2_2, R1_8) in real-time"],
              bg='#ffffff', border='#f59e0b', t_fs=7.8, b_fs=6.2, align='left')

    # Physical Plant Box
    draw_card(ax, 51.5, 4.8, 43.5, 16.5, "Physical FMS Plant & Edge Controller (Hardware Reality)",
              ["• Microcontroller: Arduino Mega 2560 + W5100 Ethernet Shield (192.168.10.1)",
               "• TCP Socket Server (:8888): Dispatches live optical sensor breaks & relay clicks",
               "• HTTP REST Gateway (:80): Exposes modular manufacturing skills (/passadeiras?skill=AB)",
               "• Physical Conveyor Belts & Relays: Opto-isolated 24V DC field drives (R0_7, R0_8, R1_8)",
               "• Industrial Workstation (Punch_FMS): Pneumatic cylinders, indexing table & limit switches"],
              bg='#ffffff', border='#dc2626', t_fs=7.8, b_fs=6.2, align='left')

    save_fig(fig, "system_architecture_real")

if __name__ == "__main__":
    make_arduino_freertos_schema()
    make_fms_physical_bench()
    make_fms_sensor_actuator_details()
    make_wizard_ui_screenshots()
    make_system_architecture_real()
    print("Batch 2 completed successfully.")


