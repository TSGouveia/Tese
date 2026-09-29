import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def create_architecture_global():
    fig, ax = plt.subplots(figsize=(8.0, 8.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Color Palette
    c_l1_bg = '#eff6ff'
    c_l1_border = '#2563eb'
    c_l2_bg = '#f0fdf4'
    c_l2_border = '#16a34a'
    c_l3_bg = '#faf5ff'
    c_l3_border = '#9333ea'

    c_box_bg = '#ffffff'
    c_text_main = '#0f172a'
    c_text_sub = '#334155'

    def box(x, y, w, h, title, subtitle, bg='#ffffff', border='#3b82f6', t_fs=11, s_fs=9.5):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.5,rounding_size=1.5",
                                      facecolor=bg, edgecolor=border, linewidth=1.8, zorder=3)
        ax.add_patch(rect)
        if subtitle:
            ax.text(x + w/2, y + h*0.62, title, ha='center', va='center', fontsize=t_fs, fontweight='bold', color=c_text_main, zorder=4)
            ax.text(x + w/2, y + h*0.32, subtitle, ha='center', va='center', fontsize=s_fs, color=c_text_sub, zorder=4)
        else:
            ax.text(x + w/2, y + h/2, title, ha='center', va='center', fontsize=t_fs, fontweight='bold', color=c_text_main, zorder=4)

    def group_box(x, y, w, h, label, bg, border):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.8,rounding_size=2.0",
                                      facecolor=bg, edgecolor=border, linewidth=2.2, zorder=1)
        ax.add_patch(rect)
        ax.text(x + 2.5, y + h - 2.8, label, ha='left', va='center', fontsize=12, fontweight='bold', color=border, zorder=2)

    def arrow(p1, p2, label="", label_pos=(0,0), color='#1e293b', style='->', lw=1.8, dashed=False):
        ls = '--' if dashed else '-'
        ax.annotate('', xy=p2, xytext=p1,
                    arrowprops=dict(arrowstyle=style, color=color, lw=lw, linestyle=ls, shrinkA=3, shrinkB=3),
                    zorder=5)
        if label:
            lx = (p1[0] + p2[0])/2 + label_pos[0]
            ly = (p1[1] + p2[1])/2 + label_pos[1]
            ax.text(lx, ly, label, ha='center', va='center', fontsize=9.5, fontweight='bold', color=color,
                    bbox=dict(boxstyle='round,pad=0.25', facecolor='#ffffff', edgecolor=color, lw=1.0), zorder=6)

    # =========================================================================
    # LAYER 1: SETUP & MODELING CLIENT
    # =========================================================================
    group_box(3, 76, 94, 21, "Layer 1 · Setup & Semantic Modeling Client (Python AAS Client)", c_l1_bg, c_l1_border)
    box(6,  78.5, 26, 13.5, "Conveyor Wizard GUI", "PyQt6 Desktop Application", '#ffffff', c_l1_border)
    box(37, 78.5, 26, 13.5, "3D & Kinematic Parser", "PyVista · Trimesh · Xacro/URDF", '#ffffff', c_l1_border)
    box(68, 78.5, 26, 13.5, "BaSyx Python SDK", "AASX Packager & Metamodel", '#ffffff', c_l1_border)

    arrow((32, 85.2), (37, 85.2))
    arrow((63, 85.2), (68, 85.2))

    # =========================================================================
    # LAYER 2: INDUSTRIAL SEMANTIC MIDDLEWARE (DOCKER)
    # =========================================================================
    group_box(3, 40, 94, 31, "Layer 2 · Industrial Semantic Middleware (Eclipse BaSyx v2 in Docker)", c_l2_bg, c_l2_border)
    box(6,  56.5, 26, 11.5, "AAS Environment (:8081)", "Shell & Submodel Repository", '#ffffff', c_l2_border)
    box(37, 56.5, 26, 11.5, "AAS / SM Registries (:8082)", "Shell & Submodel Descriptors", '#ffffff', c_l2_border)
    box(68, 56.5, 26, 11.5, "Mosquitto MQTT (:1883)", "Real-Time Telemetry Broker", '#ffffff', c_l2_border)

    box(16, 42.5, 30, 10.5, "MongoDB Store (:27017)", "Descriptors Persistence", '#ffffff', '#b45309')
    box(54, 42.5, 30, 10.5, "BaSyx Web UI (:3000)", "Supervisory Dashboard", '#ffffff', '#7e22ce')

    arrow((32, 62.2), (37, 62.2), style='<->')
    arrow((63, 62.2), (68, 62.2), style='<->')
    arrow((37, 56.5), (31, 53.0))
    arrow((20, 56.5), (54, 47.7))

    # =========================================================================
    # LAYER 3: RUNTIME EXECUTION & PHYSICAL SYNCHRONIZATION
    # =========================================================================
    group_box(3, 3, 94, 32, "Layer 3 · Runtime Execution & Physical Synchronization", c_l3_bg, c_l3_border)

    # Subgroup Unity
    rect_u = patches.FancyBboxPatch((5.5, 5.0), 43, 25, boxstyle="round,pad=0.5,rounding_size=1.5",
                                    facecolor='#ffffff', edgecolor='#a855f7', linewidth=1.6, zorder=2)
    ax.add_patch(rect_u)
    ax.text(8.0, 27.8, "Unity 3D Simulation & Twin Engine", fontsize=10.5, fontweight='bold', color='#7e22ce', zorder=3)

    box(8,  20.2, 38, 6.2, "BaSyxManager.cs", "Procedural Importer & REST Polling", '#f5f3ff', '#a855f7', 10, 8.5)
    box(8,  13.2, 38, 6.2, "AASRuleEngine.cs", "Virtual Commissioning Logic", '#f5f3ff', '#a855f7', 10, 8.5)
    box(8,  6.2,  38, 6.2, "DynamicProduct.cs", "PhysX Workpieces & Lerp Snapping", '#f5f3ff', '#a855f7', 10, 8.5)

    arrow((27, 20.2), (27, 19.4))
    arrow((27, 13.2), (27, 12.4))

    # Subgroup FMS
    rect_f = patches.FancyBboxPatch((51.5, 5.0), 43, 25, boxstyle="round,pad=0.5,rounding_size=1.5",
                                    facecolor='#ffffff', edgecolor='#ef4444', linewidth=1.6, zorder=2)
    ax.add_patch(rect_f)
    ax.text(54.0, 27.8, "Modular FMS Physical Testbed", fontsize=10.5, fontweight='bold', color='#dc2626', zorder=3)

    box(54, 20.2, 38, 6.2, "Arduino Mega 2560", "FreeRTOS Embedded Firmware", '#fef2f2', '#ef4444', 10, 8.5)
    box(54, 13.2, 38, 6.2, "Sensor Array (Port I)", "Optical Breakbeams & Inductive", '#fef2f2', '#ef4444', 10, 8.5)
    box(54, 6.2,  38, 6.2, "Actuator Array (Port R)", "Conveyor Motors & Diverters", '#fef2f2', '#ef4444', 10, 8.5)

    arrow((73, 20.2), (73, 19.4))
    arrow((73, 13.2), (73, 12.4))

    # =========================================================================
    # INTER-LAYER PROTOCOL ARROWS
    # =========================================================================
    arrow((81, 78.5), (25, 68.0), "HTTP POST /upload (AASX Package)", (-16, 5), '#1d4ed8')
    arrow((14, 56.5), (14, 26.4), "HTTP REST & VirtualPins", (0, 7), '#15803d', style='<->')
    arrow((81, 56.5), (42, 26.4), "MQTT Telemetry", (-10, 7), '#d97706', dashed=True)
    arrow((54, 23.3), (46, 23.3), "TCP Socket :8888 (Fast Pin Events)", (0, 2.5), '#b91c1c', style='<->', lw=2.2)
    arrow((19, 56.5), (65, 26.4), "REST Skill Calls :80", (16, 7), '#64748b', dashed=True)

    plt.tight_layout()
    for out_d in ["Documentos/5-Figures", "Documentos/Figures", "5-Figures"]:
        fig.savefig(os.path.join(out_d, "architecture_global.pdf"), bbox_inches='tight')
        fig.savefig(os.path.join(out_d, "architecture_global.png"), bbox_inches='tight')
    plt.close(fig)
    print("architecture_global rendered successfully!")

if __name__ == "__main__":
    create_architecture_global()
