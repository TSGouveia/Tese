# -*- coding: utf-8 -*-
import os, sys, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thesis_art_utils import save_fig

def _draw_initial_node(ax, cx, cy, r=1.6, color='#0f172a'):
    ax.add_patch(plt.Circle((cx, cy), r, facecolor=color, edgecolor=color, lw=1.0, zorder=6))

def _draw_final_node(ax, cx, cy, r_outer=2.0, color='#0f172a'):
    ax.add_patch(plt.Circle((cx, cy), r_outer, facecolor='#ffffff', edgecolor=color, lw=1.4, zorder=6))
    ax.add_patch(plt.Circle((cx, cy), r_outer * 0.55, facecolor=color, edgecolor=color, lw=0.8, zorder=7))

def _draw_action_node(ax, cx, cy, w, h, text, bg='#eff6ff', bd='#1d4ed8', fs=7.2, zorder=5):
    x = cx - w/2.0
    y = cy - h/2.0
    ax.add_patch(patches.FancyBboxPatch(
        (x, y), w, h, boxstyle='round,pad=0.0,rounding_size=2.2',
        facecolor=bg, edgecolor=bd, linewidth=1.3, zorder=zorder))
    ax.text(cx, cy, text, ha='center', va='center', fontsize=fs,
            fontweight='bold', color='#0f172a', zorder=zorder+1, multialignment='center')

def _draw_decision_diamond(ax, cx, cy, size=4.0, bg='#ffffff', bd='#0f172a', zorder=5):
    half = size / 2.0
    pts = [[cx, cy + half], [cx + half * 1.3, cy], [cx, cy - half], [cx - half * 1.3, cy]]
    poly = patches.Polygon(pts, closed=True, facecolor=bg, edgecolor=bd, linewidth=1.3, zorder=zorder)
    ax.add_patch(poly)

def _draw_control_flow(ax, p1, p2, label='', guard='', color='#334155', lw=1.3, fs=6.2):
    hl = 0.55 * 0.95
    hw = 0.35 * 0.95
    arr_style = f'-|>,head_length={hl:.2f},head_width={hw:.2f}'
    ax.annotate('', xy=p2, xytext=p1,
                arrowprops=dict(arrowstyle=arr_style, color=color, lw=lw, shrinkA=1, shrinkB=1),
                zorder=4)
    mx = (p1[0] + p2[0]) / 2.0
    my = (p1[1] + p2[1]) / 2.0
    if guard:
        ax.text(mx + 1.2, my, f'[{guard}]', ha='left', va='center',
                fontsize=fs, fontstyle='italic', fontweight='semibold', color='#0f172a', zorder=6)
    elif label:
        ax.text(mx, my + 1.2, label, ha='center', va='bottom',
                fontsize=fs, color='#334155', zorder=6)

# -----------------------------------------------------------------------------
# LAYER 1: SWIMLANES (Asset Authoring Tool vs. Package Serialization Service)
# -----------------------------------------------------------------------------
def make_activity_layer1():
    fig, ax = plt.subplots(figsize=(8.4, 6.2), dpi=300)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')

    ax.add_patch(patches.FancyBboxPatch(
        (3, 4), 94, 91, boxstyle='round,pad=0.0,rounding_size=1.5',
        facecolor='#ffffff', edgecolor='#334155', linewidth=1.5, zorder=1))
    ax.text(5.5, 92.2, '«activity» Layer 1 · Asset Modeling & Packaging',
            ha='left', va='center', fontsize=8.6, fontweight='bold', color='#0f172a', zorder=2)

    lane_w = 46.0
    x_eng = 4.0
    x_wiz = 50.0
    lane_h = 85.0
    y_lane = 5.0

    # Lane 1: Asset Authoring Tool
    ax.add_patch(patches.Rectangle((x_eng, y_lane), lane_w, lane_h,
                                   facecolor='#eff6ff', edgecolor='#2563eb', lw=1.2, zorder=2))
    ax.add_patch(patches.Rectangle((x_eng, y_lane + lane_h - 6.5), lane_w, 6.5,
                                   facecolor='#dbeafe', edgecolor='#2563eb', lw=1.2, zorder=3))
    ax.text(x_eng + lane_w/2.0, y_lane + lane_h - 3.2, 'Asset Authoring Tool',
            ha='center', va='center', fontsize=8.2, fontweight='bold', color='#1e40af', zorder=4)

    # Lane 2: Package Serialization Service
    ax.add_patch(patches.Rectangle((x_wiz, y_lane), lane_w, lane_h,
                                   facecolor='#f8fafc', edgecolor='#0284c7', lw=1.2, zorder=2))
    ax.add_patch(patches.Rectangle((x_wiz, y_lane + lane_h - 6.5), lane_w, 6.5,
                                   facecolor='#e0f2fe', edgecolor='#0284c7', lw=1.2, zorder=3))
    ax.text(x_wiz + lane_w/2.0, y_lane + lane_h - 3.2, 'Package Serialization Service',
            ha='center', va='center', fontsize=8.2, fontweight='bold', color='#0369a1', zorder=4)

    cx_e = 27.0
    cx_w = 73.0

    # Flow starts at Authoring Tool: import CAD
    _draw_initial_node(ax, cx_e, 78)
    _draw_control_flow(ax, (cx_e, 76.2), (cx_e, 71.5))

    _draw_action_node(ax, cx_e, 66.5, 34, 9.5, 'Import 3D CAD Model\n& Set Asset Info',
                      bg='#eff6ff', bd='#2563eb', fs=7.0)

    # Cross to Serialization Service: Parse Mesh & Kinematics
    _draw_control_flow(ax, (cx_e + 17.0, 66.5), (cx_w - 17.0, 66.5))
    _draw_action_node(ax, cx_w, 66.5, 34, 9.5, 'Parse Geometry &\nExtract Kinematic Joints',
                      bg='#f0f9ff', bd='#0284c7', fs=7.0)

    # Cross back to Authoring Tool: Assign Virtual Pins
    ax.plot([cx_w, cx_w, cx_e + 20.0], [61.7, 56.5, 56.5], color='#334155', lw=1.3, zorder=4)
    _draw_control_flow(ax, (cx_e + 20.0, 56.5), (cx_e + 17.0, 53.0))

    _draw_action_node(ax, cx_e, 50.0, 34, 9.5, 'Assign Virtual Pins\n& Define Logic Rules',
                      bg='#eff6ff', bd='#2563eb', fs=7.0)

    # Cross back to Serialization Service: Validate & Package
    ax.plot([cx_e + 17.0, 48.0, 48.0], [50.0, 50.0, 39.5], color='#334155', lw=1.3, zorder=4)
    _draw_control_flow(ax, (48.0, 39.5), (cx_w - 2.8, 39.5))

    # Decision diamond in Serialization Service lane
    _draw_decision_diamond(ax, cx_w, 39.5, size=5.2, bd='#0284c7')
    ax.text(cx_w, 44.2, 'Valid Package?', ha='center', va='bottom', fontsize=6.4, fontweight='bold', color='#0369a1')

    # [Invalid] branch: step up along right side and back to Authoring Tool
    ax.plot([cx_w + 3.2, 92.0, 92.0], [39.5, 39.5, 50.0], color='#b91c1c', lw=1.2, zorder=4)
    ax.plot([92.0, cx_e + 22.0], [50.0, 50.0], color='#b91c1c', lw=1.2, zorder=4)
    _draw_control_flow(ax, (cx_e + 22.0, 50.0), (cx_e + 17.0, 50.0), color='#b91c1c')
    ax.text(88.0, 41.0, '[No]', ha='center', va='bottom', fontsize=6.0, fontstyle='italic', color='#b91c1c')

    # [Valid] branch down in Serialization Service lane
    _draw_control_flow(ax, (cx_w, 36.9), (cx_w, 30.5), guard='Yes')

    _draw_action_node(ax, cx_w, 25.5, 34, 9.5, 'Build Submodels &\nExport Asset Package',
                      bg='#f0f9ff', bd='#0284c7', fs=7.0)

    # Final Node
    _draw_control_flow(ax, (cx_w, 20.7), (cx_w, 15.5))
    _draw_final_node(ax, cx_w, 13.5)
    ax.text(cx_w, 8.5, 'Package Ready for Upload', ha='center', va='center',
            fontsize=7.2, fontweight='bold', color='#0369a1')

    save_fig(fig, 'activity_layer1')


# -----------------------------------------------------------------------------
# LAYER 2: SWIMLANES (Model Repository vs. Asset Registry & Catalog)
# -----------------------------------------------------------------------------
def make_activity_layer2():
    fig, ax = plt.subplots(figsize=(8.4, 6.2), dpi=300)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')

    ax.add_patch(patches.FancyBboxPatch(
        (3, 4), 94, 91, boxstyle='round,pad=0.0,rounding_size=1.5',
        facecolor='#ffffff', edgecolor='#334155', linewidth=1.5, zorder=1))
    ax.text(5.5, 92.2, '«activity» Layer 2 · Asset Storage & Registry Services',
            ha='left', va='center', fontsize=8.6, fontweight='bold', color='#0f172a', zorder=2)

    lane_w = 46.0
    x_rep = 4.0
    x_reg = 50.0
    lane_h = 85.0
    y_lane = 5.0

    # Lane 1: Model Repository
    ax.add_patch(patches.Rectangle((x_rep, y_lane), lane_w, lane_h,
                                   facecolor='#f0fdf4', edgecolor='#16a34a', lw=1.2, zorder=2))
    ax.add_patch(patches.Rectangle((x_rep, y_lane + lane_h - 6.5), lane_w, 6.5,
                                   facecolor='#dcfce7', edgecolor='#16a34a', lw=1.2, zorder=3))
    ax.text(x_rep + lane_w/2.0, y_lane + lane_h - 3.2, 'Model Repository',
            ha='center', va='center', fontsize=8.2, fontweight='bold', color='#15803d', zorder=4)

    # Lane 2: Asset Registry & Catalog
    ax.add_patch(patches.Rectangle((x_reg, y_lane), lane_w, lane_h,
                                   facecolor='#fafffa', edgecolor='#059669', lw=1.2, zorder=2))
    ax.add_patch(patches.Rectangle((x_reg, y_lane + lane_h - 6.5), lane_w, 6.5,
                                   facecolor='#d1fae5', edgecolor='#059669', lw=1.2, zorder=3))
    ax.text(x_reg + lane_w/2.0, y_lane + lane_h - 3.2, 'Asset Registry & Catalog',
            ha='center', va='center', fontsize=8.2, fontweight='bold', color='#047857', zorder=4)

    cx_p = 27.0
    cx_g = 73.0

    # Ingestion flow starts at Model Repository
    _draw_initial_node(ax, cx_p, 78)
    _draw_control_flow(ax, (cx_p, 76.2), (cx_p, 71.5))

    _draw_action_node(ax, cx_p, 66.5, 34, 9.5, 'Receive & Extract\nAsset Package',
                      bg='#f0fdf4', bd='#16a34a', fs=7.0)
    _draw_control_flow(ax, (cx_p, 61.7), (cx_p, 55.5))

    _draw_action_node(ax, cx_p, 50.5, 34, 9.5, 'Save 3D Meshes &\nSubmodel Files',
                      bg='#f0fdf4', bd='#16a34a', fs=7.0)

    # Cross to Registry: Register Asset & Endpoints
    _draw_control_flow(ax, (cx_p + 17.0, 50.5), (cx_g - 17.0, 50.5))

    _draw_action_node(ax, cx_g, 50.5, 34, 9.5, 'Register Asset ID &\nNetwork Endpoints',
                      bg='#ecfdf5', bd='#059669', fs=7.0)
    _draw_control_flow(ax, (cx_g, 45.7), (cx_g, 39.5))

    _draw_action_node(ax, cx_g, 34.5, 34, 9.5, 'Lookup Active Assets &\nReturn Endpoints',
                      bg='#ecfdf5', bd='#059669', fs=7.0)

    # Cross back to Repository: Stream Model Files (Orthogonal route)
    ax.plot([cx_g - 17.0, 48.0, 48.0], [34.5, 34.5, 24.5], color='#334155', lw=1.3, zorder=4)
    _draw_control_flow(ax, (48.0, 24.5), (cx_p + 17.0, 24.5))

    _draw_action_node(ax, cx_p, 24.5, 34, 9.5, 'Send Model Files &\nMetadata to Simulation',
                      bg='#f0fdf4', bd='#16a34a', fs=7.0)

    # Final Node in Repository
    _draw_control_flow(ax, (cx_p, 19.7), (cx_p, 14.5))
    _draw_final_node(ax, cx_p, 12.5)
    ax.text(cx_p, 7.5, 'Asset Ready for Simulation', ha='center', va='center',
            fontsize=7.2, fontweight='bold', color='#15803d')

    save_fig(fig, 'activity_layer2')


# -----------------------------------------------------------------------------
# LAYER 3: CLEAN SWIMLANES WITH JOIN NODE & SIMPLER ENGLISH
# -----------------------------------------------------------------------------
def make_activity_layer3():
    fig, ax = plt.subplots(figsize=(9.6, 6.4), dpi=300)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')

    ax.add_patch(patches.FancyBboxPatch(
        (2.5, 3.5), 95.0, 92.5, boxstyle='round,pad=0.0,rounding_size=1.5',
        facecolor='#ffffff', edgecolor='#334155', linewidth=1.5, zorder=1))
    ax.text(5.0, 92.6, '«activity» Layer 3 · Runtime Simulation & Live Sync',
            ha='left', va='center', fontsize=8.8, fontweight='bold', color='#0f172a', zorder=2)

    lane_w = 42.0
    x_sim = 7.5
    x_phy = 50.5
    lane_h = 84.5
    y_lane = 5.5

    # Lane 1: Simulation Runtime Engine
    ax.add_patch(patches.Rectangle((x_sim, y_lane), lane_w, lane_h,
                                   facecolor='#faf5ff', edgecolor='#9333ea', lw=1.2, zorder=2))
    ax.add_patch(patches.Rectangle((x_sim, y_lane + lane_h - 6.5), lane_w, 6.5,
                                   facecolor='#f3e8ff', edgecolor='#9333ea', lw=1.2, zorder=3))
    ax.text(x_sim + lane_w/2.0, y_lane + lane_h - 3.2, 'Simulation Runtime Engine',
            ha='center', va='center', fontsize=8.2, fontweight='bold', color='#7e22ce', zorder=4)

    # Lane 2: Physical Automation Plant
    ax.add_patch(patches.Rectangle((x_phy, y_lane), lane_w, lane_h,
                                   facecolor='#fffafa', edgecolor='#dc2626', lw=1.2, zorder=2))
    ax.add_patch(patches.Rectangle((x_phy, y_lane + lane_h - 6.5), lane_w, 6.5,
                                   facecolor='#fee2e2', edgecolor='#dc2626', lw=1.2, zorder=3))
    ax.text(x_phy + lane_w/2.0, y_lane + lane_h - 3.2, 'Physical Automation Plant',
            ha='center', va='center', fontsize=8.2, fontweight='bold', color='#b91c1c', zorder=4)

    cx_s = x_sim + lane_w / 2.0  # 28.5
    node_w = 33.0

    _draw_initial_node(ax, cx_s, 77.5)
    _draw_control_flow(ax, (cx_s, 75.7), (cx_s, 70.5))

    _draw_action_node(ax, cx_s, 65.0, node_w, 9.5, 'Download Descriptors\nfrom Layer 2',
                        bg='#faf5ff', bd='#7e22ce', fs=7.0)
    _draw_control_flow(ax, (cx_s, 60.2), (cx_s, 54.5))

    _draw_action_node(ax, cx_s, 49.0, node_w, 9.5, 'Build Virtual Scene\n& Bind Pins',
                        bg='#faf5ff', bd='#7e22ce', fs=7.0)
    _draw_control_flow(ax, (cx_s, 44.2), (cx_s, 38.5))

    _draw_action_node(ax, cx_s, 33.0, node_w, 9.5, 'Run Physics Simulation\n& Check Collisions',
                        bg='#faf5ff', bd='#7e22ce', fs=7.0)
    
    # Flow from Physics down to UML Join Node before snap pose
    _draw_control_flow(ax, (cx_s, 28.2), (cx_s, 24.2))

    # Standard UML Join Bar (solid bar across x=[20.0, 37.0] at y=23.5)
    ax.plot([20.0, 37.0], [23.5, 23.5], color='#0f172a', lw=3.2, solid_capstyle='butt', zorder=6)

    # From Join Bar to Snap Pose
    _draw_control_flow(ax, (cx_s, 23.5), (cx_s, 19.5))

    _draw_action_node(ax, cx_s, 15.0, node_w, 9.0, 'Correct Drift & Snap\nPose to Sensor',
                        bg='#faf5ff', bd='#7e22ce', fs=7.0)

    # Simulation loopback: from snap pose back to physics
    ax.plot([cx_s - node_w/2.0, 5.6, 5.6], [15.0, 15.0, 33.0], color='#7e22ce', lw=1.3, zorder=4)
    _draw_control_flow(ax, (5.6, 33.0), (cx_s - node_w/2.0, 33.0), color='#7e22ce')
    ax.text(4.0, 24.0, '[Next Frame]', ha='center', va='center', rotation=90, fontsize=6.2, fontstyle='italic', fontweight='bold', color='#7e22ce')

    # --- Physical Plant Lane ---
    cx_p = x_phy + lane_w / 2.0  # 71.5

    _draw_initial_node(ax, cx_p, 77.5, color='#991b1b')
    _draw_control_flow(ax, (cx_p, 75.7), (cx_p, 70.5), color='#991b1b')

    _draw_action_node(ax, cx_p, 65.0, node_w, 9.5, 'Scan Digital Sensors\n(Cyclic Scan)',
                        bg='#fef2f2', bd='#b91c1c', fs=7.0)
    _draw_control_flow(ax, (cx_p, 60.2), (cx_p, 54.5), color='#991b1b')

    # Decision diamond: Sensor State Changed?
    _draw_decision_diamond(ax, cx_p, 51.0, size=5.2, bd='#b91c1c')
    ax.text(cx_p - 3.8, 51.0, 'Sensor State\nChanged?', ha='right', va='center', fontsize=6.2, fontweight='bold', color='#991b1b')

    # [No] loopback: routes at x=91.0
    ax.plot([cx_p + 3.4, 91.0, 91.0], [51.0, 51.0, 65.0], color='#991b1b', lw=1.2, zorder=4)
    _draw_control_flow(ax, (91.0, 65.0), (cx_p + node_w/2.0, 65.0), color='#991b1b')
    ax.text(89.8, 58.0, '[No]', ha='right', va='center', fontsize=6.0, fontstyle='italic', fontweight='bold', color='#991b1b')

    # [Yes] branch down
    _draw_control_flow(ax, (cx_p, 48.4), (cx_p, 42.0), guard='Yes', color='#991b1b')

    _draw_action_node(ax, cx_p, 36.5, node_w, 9.5, 'Send Telemetry Packet\nvia Socket',
                        bg='#fef2f2', bd='#b91c1c', fs=7.0)
    _draw_control_flow(ax, (cx_p, 31.7), (cx_p, 26.0), color='#991b1b')

    _draw_action_node(ax, cx_p, 20.5, node_w, 9.5, 'Control Actuators\n(Motors & Gates)',
                        bg='#fef2f2', bd='#b91c1c', fs=7.0)

    # Controller cyclic loop: from driving actuators back up to Scan Cycle in outer right margin (x=95.5)
    ax.plot([cx_p + node_w/2.0, 95.5, 95.5], [20.5, 20.5, 65.0], color='#991b1b', lw=1.2, zorder=4)
    _draw_control_flow(ax, (95.5, 65.0), (cx_p + node_w/2.0, 65.0), color='#991b1b')
    ax.text(94.2, 42.0, '[Next Scan]', ha='center', va='center', rotation=-90, fontsize=6.2, fontstyle='italic', fontweight='bold', color='#991b1b')

    # Solid Control Flow arrow from Send Telemetry Packet directly to Join Node
    # From Send Telemetry (cx_p - node_w/2.0 = 55.0, y=36.5) -> cross lane line cleanly -> Join Bar right end (37.0, 23.5)
    ax.plot([55.0, 44.5, 44.5], [36.5, 36.5, 23.5], color='#b91c1c', lw=1.3, zorder=5)
    _draw_control_flow(ax, (44.5, 23.5), (37.2, 23.5), color='#b91c1c')
    ax.text(62.0, 42.0, 'Telemetry Packet', ha='center', va='bottom', fontsize=6.2, fontstyle='italic', fontweight='bold', color='#b91c1c', zorder=6)

    save_fig(fig, 'activity_layer3')

if __name__ == '__main__':
    make_activity_layer1()
    make_activity_layer2()
    make_activity_layer3()
