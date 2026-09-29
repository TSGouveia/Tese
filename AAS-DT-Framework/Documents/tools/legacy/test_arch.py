# -*- coding: utf-8 -*-
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

OUT_DIRS = ["Documentos/5-Figures", "Documentos/Figures", "5-Figures"]

def save_fig(fig, name):
    for d in OUT_DIRS:
        if os.path.exists(d):
            fig.savefig(os.path.join(d, f"{name}.pdf"), bbox_inches='tight', pad_inches=0.08)
            fig.savefig(os.path.join(d, f"{name}.png"), bbox_inches='tight', pad_inches=0.08, dpi=300)
    plt.close(fig)
    print(f"Generated: {name}.pdf / .png")

def draw_group(ax, x, y, w, h, label, bg, border, fs=11.5, lw=1.8, header_pos='top-left'):
    rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.5,rounding_size=1.2",
                                  facecolor=bg, edgecolor=border, linewidth=lw, zorder=1)
    ax.add_patch(rect)
    if label:
        if header_pos == 'top-left':
            ax.text(x + 2.2, y + h - 2.4, label, ha='left', va='center', fontsize=fs, fontweight='bold', color=border, zorder=2)
        elif header_pos == 'top-center':
            ax.text(x + w/2, y + h - 2.4, label, ha='center', va='center', fontsize=fs, fontweight='bold', color=border, zorder=2)

def draw_card(ax, x, y, w, h, title, lines=None, bg='#ffffff', border='#3b82f6', t_fs=10, b_fs=8.2, lw=1.4):
    rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.0",
                                  facecolor=bg, edgecolor=border, linewidth=lw, zorder=3)
    ax.add_patch(rect)
    
    t_lines = title.split('\n')
    if not lines:
        if len(t_lines) == 1:
            ax.text(x + w/2, y + h/2, title, ha='center', va='center', fontsize=t_fs, fontweight='bold', color='#0f172a', zorder=4)
        else:
            ax.text(x + w/2, y + h*0.62, t_lines[0], ha='center', va='center', fontsize=t_fs, fontweight='bold', color='#0f172a', zorder=4)
            ax.text(x + w/2, y + h*0.38, t_lines[1], ha='center', va='center', fontsize=t_fs, fontweight='bold', color='#0f172a', zorder=4)
        return

    if len(t_lines) == 1:
        ax.text(x + w/2, y + h - 2.2, t_lines[0], ha='center', va='center', fontsize=t_fs, fontweight='bold', color='#0f172a', zorder=4)
        top_offset = 3.6
    else:
        ax.text(x + w/2, y + h - 1.8, t_lines[0], ha='center', va='center', fontsize=t_fs, fontweight='bold', color='#0f172a', zorder=4)
        ax.text(x + w/2, y + h - 3.4, t_lines[1], ha='center', va='center', fontsize=t_fs, fontweight='bold', color='#0f172a', zorder=4)
        top_offset = 4.8

    n = len(lines)
    avail_h = h - top_offset - 0.6
    spacing = avail_h / max(n, 1)
    for i, line in enumerate(lines):
        ly = y + h - top_offset - (i + 0.5) * spacing
        ax.text(x + w/2, ly, line, ha='center', va='center', fontsize=b_fs, color='#334155', zorder=4)

def draw_badge(ax, x, y, text, color='#1e293b', bg='#ffffff', border=None, fs=8.5):
    if border is None:
        border = color
    ax.text(x, y, text, ha='center', va='center', fontsize=fs, fontweight='bold', color=color,
            bbox=dict(boxstyle='round,pad=0.25,rounding_size=0.3', facecolor=bg, edgecolor=border, lw=0.9),
            zorder=8)

def draw_arrow(ax, p1, p2, label="", label_pos=None, color='#1e293b', style='->', lw=1.5, dashed=False, b_fs=8.5):
    ls = '--' if dashed else '-'
    ax.annotate('', xy=p2, xytext=p1,
                arrowprops=dict(arrowstyle=style, color=color, lw=lw, linestyle=ls, shrinkA=2, shrinkB=2),
                zorder=5)
    if label:
        lx = (p1[0] + p2[0])/2 if label_pos is None else label_pos[0]
        ly = (p1[1] + p2[1])/2 if label_pos is None else label_pos[1]
        draw_badge(ax, lx, ly, label, color=color, bg='#ffffff', border=color, fs=b_fs)

def make_architecture_global():
    fig, ax = plt.subplots(figsize=(7.6, 9.0), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    c_l1_bg, c_l1_border = '#eff6ff', '#2563eb'
    c_l2_bg, c_l2_border = '#f0fdf4', '#16a34a'
    c_l3_bg, c_l3_border = '#faf5ff', '#9333ea'

    # =========================================================================
    # LAYER 1: SETUP & MODELING CLIENT (y: 77 to 98)
    # =========================================================================
    draw_group(ax, 3, 76.5, 94, 21.5, "Layer 1 · Setup & Semantic Modeling Client (Python AAS Client)", c_l1_bg, c_l1_border, fs=11.5)
    draw_card(ax, 6, 78.5, 26, 15.2, "Conveyor Wizard\nGUI Application", 
              ["PyQt6 Desktop Client", "5-Step Pipeline Wizard", "Rule & Layout Studios"], '#ffffff', c_l1_border, t_fs=10, b_fs=8.2)
    draw_card(ax, 37, 78.5, 26, 15.2, "3D & Kinematic\nParser Engine", 
              ["PyVista & Trimesh", "URDF / Xacro Geometry", "Scene Node Hierarchy"], '#ffffff', c_l1_border, t_fs=10, b_fs=8.2)
    draw_card(ax, 68, 78.5, 26, 15.2, "BaSyx Python\nSDK & Packager", 
              ["AASX Package Builder", "Submodels Generator", "REST Deployment Client"], '#ffffff', c_l1_border, t_fs=10, b_fs=8.2)

    draw_arrow(ax, (32, 86.1), (37, 86.1), style='->', lw=1.6)
    draw_arrow(ax, (63, 86.1), (68, 86.1), style='->', lw=1.6)

    # =========================================================================
    # LAYER 2: INDUSTRIAL SEMANTIC MIDDLEWARE (y: 40 to 72)
    # =========================================================================
    draw_group(ax, 3, 40, 94, 32.5, "Layer 2 · Industrial Semantic Middleware (Eclipse BaSyx v2 in Docker)", c_l2_bg, c_l2_border, fs=11.5)
    draw_card(ax, 6, 55.0, 26, 11.5, "AAS Environment\n(:8081)", 
              ["Shell & Submodel Repo", "Package Ingestion (/upload)", "Standard REST Provider"], '#ffffff', c_l2_border, t_fs=9.8, b_fs=8.0)
    draw_card(ax, 37, 55.0, 26, 11.5, "AAS & SM Registries\n(:8082 / :8083)", 
              ["Descriptor Directory", "Endpoint URL Registry", "Registration API"], '#ffffff', c_l2_border, t_fs=9.8, b_fs=8.0)
    draw_card(ax, 68, 55.0, 26, 11.5, "Mosquitto MQTT\nBroker (:1883)", 
              ["Real-Time Telemetry", "Pub/Sub Distribution", "High-Throughput Queue"], '#ffffff', c_l2_border, t_fs=9.8, b_fs=8.0)

    draw_card(ax, 18, 42.0, 28, 10.0, "MongoDB Database (:27017)", 
              ["Persistent Descriptors Storage", "AAS Registry Backend"], '#ffffff', '#b45309', t_fs=9.5, b_fs=7.8)
    draw_card(ax, 54, 42.0, 28, 10.0, "BaSyx Web UI (:3000)", 
              ["Supervisory Web Dashboard", "Live AAS Explorer & Metrics"], '#ffffff', '#7e22ce', t_fs=9.5, b_fs=7.8)

    draw_arrow(ax, (32, 60.7), (37, 60.7), style='<->', lw=1.4)
    draw_arrow(ax, (63, 60.7), (68, 60.7), style='<->', lw=1.4)
    draw_arrow(ax, (41, 55.0), (36, 52.0), style='->', lw=1.3)
    draw_arrow(ax, (54, 47.0), (46, 47.0), style='->', dashed=True, lw=1.3)

    # =========================================================================
    # LAYER 3: RUNTIME EXECUTION & HARDWARE (y: 2 to 36)
    # =========================================================================
    draw_group(ax, 3, 2, 94, 34.5, "Layer 3 · Runtime Execution & Physical Synchronization", c_l3_bg, c_l3_border, fs=11.5)

    # Unity Subgroup
    rect_u = patches.FancyBboxPatch((5.5, 3.8), 43, 28, boxstyle="round,pad=0.4,rounding_size=1.2",
                                    facecolor='#ffffff', edgecolor='#a855f7', linewidth=1.5, zorder=2)
    ax.add_patch(rect_u)
    ax.text(7.5, 29.8, "Unity 3D Simulation Engine", fontsize=10.5, fontweight='bold', color='#7e22ce', zorder=3)

    draw_card(ax, 8, 21.0, 38, 6.2, "BaSyxManager.cs", ["AAS Discovery, Ingestion & REST Polling"], '#f5f3ff', '#a855f7', t_fs=9.5, b_fs=8.0)
    draw_card(ax, 8, 13.0, 38, 6.2, "AASRuleEngine.cs", ["Autonomous Virtual Commissioning Logic"], '#f5f3ff', '#a855f7', t_fs=9.5, b_fs=8.0)
    draw_card(ax, 8, 5.0,  38, 6.2, "DynamicProduct.cs", ["PhysX Rigidbodies & Precision Snapping"], '#f5f3ff', '#a855f7', t_fs=9.5, b_fs=8.0)

    draw_arrow(ax, (27, 21.0), (27, 19.5), style='->', lw=1.3)
    draw_arrow(ax, (27, 13.0), (27, 11.5), style='->', lw=1.3)

    # FMS Subgroup
    rect_f = patches.FancyBboxPatch((51.5, 3.8), 43, 28, boxstyle="round,pad=0.4,rounding_size=1.2",
                                    facecolor='#ffffff', edgecolor='#ef4444', linewidth=1.5, zorder=2)
    ax.add_patch(rect_f)
    ax.text(53.5, 29.8, "Modular FMS Physical Testbed", fontsize=10.5, fontweight='bold', color='#dc2626', zorder=3)

    draw_card(ax, 54, 21.0, 38, 6.2, "Arduino Mega 2560", ["FreeRTOS Multi-Tasking Firmware"], '#fef2f2', '#ef4444', t_fs=9.5, b_fs=8.0)
    draw_card(ax, 54, 13.0, 38, 6.2, "Sensor Array (Port I)", ["Optical Breakbeams & Inductive Proximity"], '#fef2f2', '#ef4444', t_fs=9.5, b_fs=8.0)
    draw_card(ax, 54, 5.0,  38, 6.2, "Actuator Array (Port R)", ["Conveyor Belt Motors & Stopper Relays"], '#fef2f2', '#ef4444', t_fs=9.5, b_fs=8.0)

    draw_arrow(ax, (73, 21.0), (73, 19.5), style='->', lw=1.3)
    draw_arrow(ax, (73, 13.0), (73, 11.5), style='->', lw=1.3)

    # =========================================================================
    # INTER-LAYER BUS CHANNELS (Orthogonal routing, Zero collisions!)
    # =========================================================================
    # Channel 1: L1 -> L2 Deployment (horizontal bus at y=74.5)
    ax.plot([81, 81, 19, 19], [78.5, 74.5, 74.5, 66.5], color='#1d4ed8', lw=1.8, zorder=5)
    ax.annotate('', xy=(19, 66.5), xytext=(19, 68.0),
                arrowprops=dict(arrowstyle='->', color='#1d4ed8', lw=1.8, shrinkA=0, shrinkB=2), zorder=5)
    draw_badge(ax, 50, 74.5, "HTTP POST /upload (AASX Package)", color='#1d4ed8', fs=9.0)

    # Channel 2: L2 AAS Env <-> L3 Unity (Vertical straight line at x=15)
    draw_arrow(ax, (15, 55.0), (15, 31.8), label="HTTP REST & VirtualPins", label_pos=(15, 37.5),
               color='#15803d', style='<->', lw=1.8, b_fs=8.5)

    # Channel 2: L2 MQTT -> L3 Unity
    ax.plot([81, 81, 40, 40], [55.0, 37.5, 37.5, 31.8], color='#d97706', lw=1.6, ls='--', zorder=5)
    ax.annotate('', xy=(40, 31.8), xytext=(40, 33.0),
                arrowprops=dict(arrowstyle='->', color='#d97706', lw=1.6, linestyle='--', shrinkA=0, shrinkB=2), zorder=5)
    draw_badge(ax, 62, 37.5, "MQTT Telemetry (:1883)", color='#d97706', fs=8.5)

    # L3 Unity <-> Arduino Mega: Direct TCP Socket Link in the header strip at y=29.8
    draw_arrow(ax, (38, 29.8), (53.5, 29.8), style='<->', lw=2.0, color='#b91c1c')
    draw_badge(ax, 46, 29.8, "TCP :8888 (Fast Pins)", color='#b91c1c', fs=8.2)

    save_fig(fig, "architecture_global")

make_architecture_global()
