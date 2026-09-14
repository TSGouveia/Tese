import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from thesis_art_utils import *

def _comp_palette(theme='blue'):
    if theme == 'blue': # Layer 1
        return dict(
            sub_bg='#f8faff', sub_bd='#2563eb',
            box_bg='#eff6ff', box_bd='#1d4ed8',
            bar_bg='#dbeafe',
            iface_c='#1d4ed8', dep_c='#475569',
            txt_t='#0f172a', txt_b='#1e293b',
            badge_bg='#dbeafe', badge_txt='#1e40af'
        )
    elif theme == 'green': # Layer 2
        return dict(
            sub_bg='#fcfdfa', sub_bd='#16a34a',
            box_bg='#f0fdf4', box_bd='#15803d',
            bar_bg='#dcfce7',
            iface_c='#15803d', dep_c='#475569',
            txt_t='#0f172a', txt_b='#1e293b',
            badge_bg='#dcfce7', badge_txt='#166534'
        )
    else: # purple / mixed - Layer 3
        return dict(
            sub_bg_sim='#fbfaff', sub_bd_sim='#9333ea',
            sub_bg_phy='#fffafa', sub_bd_phy='#dc2626',
            box_bg_sim='#faf5ff', box_bd_sim='#7e22ce',
            box_bg_phy='#fef2f2', box_bd_phy='#b91c1c',
            bar_bg_sim='#f3e8ff', bar_bg_phy='#fee2e2',
            iface_c='#7e22ce', dep_c='#475569',
            txt_t='#0f172a', txt_b='#1e293b',
        )

def _draw_component_box(ax, x, y, w, h, title, subtext=None, bg='#eff6ff', bd='#1d4ed8', bar_bg='#dbeafe', title_fs=8.0, subtext_fs=6.5):
    """Clean UML Component: rounded box, distinct header bar with component icon."""
    # Main component container
    ax.add_patch(patches.FancyBboxPatch(
        (x, y), w, h, boxstyle='round,pad=0.0,rounding_size=1.2',
        facecolor=bg, edgecolor=bd, linewidth=1.4, zorder=3))
    
    # Header bar background band
    header_h = 7.5 if '\n' in title else 6.0
    ax.add_patch(patches.FancyBboxPatch(
        (x, y + h - header_h), w, header_h, boxstyle='round,pad=0.0,rounding_size=1.2',
        facecolor=bar_bg, edgecolor=bd, linewidth=1.0, zorder=3.5))
    ax.add_patch(patches.Rectangle((x, y + h - header_h), w, 2.0,
        facecolor=bar_bg, edgecolor='none', zorder=3.6))

    # Dividing line under header
    ax.plot([x, x + w], [y + h - header_h, y + h - header_h],
            color=bd, lw=1.1, alpha=0.85, zorder=4)

    # Component icon in top-right corner
    icon_w, icon_h = 3.6, 2.6
    ix = x + w - icon_w - 1.4
    iy = y + h - icon_h - 1.2
    ax.add_patch(patches.Rectangle((ix, iy), icon_w, icon_h,
        facecolor='#ffffff', edgecolor=bd, linewidth=0.9, zorder=5))
    for dy in (0.4, 1.45):
        ax.add_patch(patches.Rectangle((ix - 1.1, iy + dy), 1.2, 0.65,
            facecolor='#ffffff', edgecolor=bd, linewidth=0.75, zorder=6))

    # Title (single or multi-line)
    if '\n' in title:
        t_lines = title.split('\n')
        ax.text(x + 2.2, y + h - 2.8, t_lines[0],
                ha='left', va='center', fontsize=title_fs, fontweight='bold',
                color='#0f172a', zorder=5)
        ax.text(x + 2.2, y + h - 5.4, t_lines[1],
                ha='left', va='center', fontsize=title_fs, fontweight='bold',
                color='#0f172a', zorder=5)
    else:
        ax.text(x + 2.2, y + h - header_h/2.0, title,
                ha='left', va='center', fontsize=title_fs, fontweight='bold',
                color='#0f172a', zorder=5)

    # Optional descriptive role/subtext centered in component body
    if subtext:
        ax.text(x + w/2.0, y + (h - header_h)/2.0, subtext,
                ha='center', va='center', fontsize=subtext_fs, fontstyle='italic',
                color='#334155', zorder=5, multialignment='center')


def _lollipop_iface(ax, start_pt, end_pt, label='', label_pos='top', color='#1d4ed8', r=1.6, fs=6.5):
    """Provided Interface: solid line ending in hollow circle."""
    x0, y0 = start_pt
    x1, y1 = end_pt
    ax.plot([x0, x1], [y0, y1], color=color, lw=1.3, zorder=4)
    ax.add_patch(plt.Circle((x1, y1), r, facecolor='#ffffff', edgecolor=color,
                            linewidth=1.4, zorder=6))
    if label:
        lx, ly = x1, y1
        ha, va = 'center', 'bottom'
        if label_pos == 'top':
            ly += r + 1.4
            va = 'bottom'
        elif label_pos == 'bottom':
            ly -= (r + 1.4)
            va = 'top'
        elif label_pos == 'left':
            lx -= (r + 1.6)
            ha = 'right'
            va = 'center'
        elif label_pos == 'right':
            lx += (r + 1.6)
            ha = 'left'
            va = 'center'
        ax.text(lx, ly, label, ha=ha, va=va, fontsize=fs, fontweight='bold',
                color='#1e293b', zorder=7, multialignment=ha)

def _socket_iface(ax, start_pt, end_pt, label='', label_pos='top', color='#1d4ed8', r=1.6, arc_side='left', fs=6.5):
    """Required Interface: line ending in open arc."""
    x0, y0 = start_pt
    x1, y1 = end_pt
    ax.plot([x0, x1], [y0, y1], color=color, lw=1.3, zorder=4)
    
    if arc_side == 'left':
        theta1, theta2 = 90, 270
    elif arc_side == 'right':
        theta1, theta2 = -90, 90
    elif arc_side == 'up':
        theta1, theta2 = 0, 180
    else:
        theta1, theta2 = 180, 360

    arc = patches.Arc((x1, y1), r*2.2, r*2.2, angle=0, theta1=theta1, theta2=theta2,
                      color=color, linewidth=1.4, zorder=6)
    ax.add_patch(arc)

    if label:
        lx, ly = x1, y1
        ha, va = 'center', 'bottom'
        if label_pos == 'top':
            ly += r + 1.4
            va = 'bottom'
        elif label_pos == 'bottom':
            ly -= (r + 1.4)
            va = 'top'
        elif label_pos == 'left':
            lx -= (r + 1.6)
            ha = 'right'
            va = 'center'
        elif label_pos == 'right':
            lx += (r + 1.6)
            ha = 'left'
            va = 'center'
        ax.text(lx, ly, label, ha=ha, va=va, fontsize=fs, fontweight='bold',
                color='#1e293b', zorder=7, multialignment=ha)

def _assembly_conn(ax, x0, y, x1, label='', color='#475569', fs=6.2, label_y_offset=2.6, provider_side='left'):
    """Lollipop meets Socket assembly connection between two components."""
    xm = (x0 + x1) / 2.0
    r_circ = 1.4
    r_arc = 3.6
    if provider_side == 'left':
        # Left provides (circle), right requires (socket arc wraps left circle, opening to right?
        # A socket that fits onto a circle from the left opens to the LEFT (embracing circle from right)
        # Circle at xm - 0.4, socket at xm with opening towards circle.
        ax.plot([x0, xm], [y, y], color=color, lw=1.3, zorder=4)
        ax.add_patch(plt.Circle((xm, y), r_circ, facecolor='#ffffff', edgecolor=color, lw=1.3, zorder=5))
        arc = patches.Arc((xm, y), r_arc, r_arc, angle=0, theta1=90, theta2=270,
                          color=color, linewidth=1.4, zorder=6)
        ax.add_patch(arc)
        ax.plot([xm + r_arc/2.0, x1], [y, y], color=color, lw=1.3, zorder=4)
    else:
        # Right provides (circle), left requires (socket)
        # Physical plant on right provides interface: circle connects to x1.
        # Simulation on left requires interface: socket connects to x0, arc opens to right embracing circle.
        ax.plot([x1, xm], [y, y], color=color, lw=1.3, zorder=4)
        ax.add_patch(plt.Circle((xm, y), r_circ, facecolor='#ffffff', edgecolor=color, lw=1.3, zorder=5))
        arc = patches.Arc((xm, y), r_arc, r_arc, angle=0, theta1=-90, theta2=90,
                          color=color, linewidth=1.4, zorder=6)
        ax.add_patch(arc)
        ax.plot([xm - r_arc/2.0, x0], [y, y], color=color, lw=1.3, zorder=4)

    if label:
        ax.text(xm, y + label_y_offset, label, ha='center', va='bottom', fontsize=fs,
                fontweight='semibold', color='#1e293b', zorder=7, multialignment='center',
                bbox=dict(boxstyle='round,pad=0.25', facecolor='#ffffff', edgecolor='#e2e8f0', linewidth=0.5, alpha=0.96))

def _dep_link(ax, start, end, label='', color='#64748b', style='->', fs=6.0, label_side='right'):
    """Dashed UML dependency with label."""
    ax.annotate('', xy=end, xytext=start,
                arrowprops=dict(arrowstyle=style, color=color,
                                linestyle='dashed', lw=1.2, shrinkA=2, shrinkB=2), zorder=4)
    if label:
        mx, my = (start[0] + end[0]) / 2.0, (start[1] + end[1]) / 2.0
        ha = 'left' if label_side == 'right' else 'right'
        offset_x = 1.2 if label_side == 'right' else -1.2
        ax.text(mx + offset_x, my, label, ha=ha, va='center', fontsize=fs,
                fontstyle='italic', color='#334155', zorder=5)

def make_architecture_conceptual():
    """UML 2.5 Subsystem & Component Diagram for Conceptual Architecture."""
    fig, ax = plt.subplots(figsize=(8.0, 9.4), dpi=300)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')

    c_l1_bg, c_l1_border, c_l1_bar = '#f8faff', '#2563eb', '#dbeafe'
    c_l2_bg, c_l2_border, c_l2_bar = '#fcfdfa', '#16a34a', '#dcfce7'
    c_l3_bg, c_l3_border = '#faf5ff', '#7e22ce'

    # =========================================================================
    # =========================================================================
    # SUBSYSTEM 1: ASSET MODELING & INGESTION
    # =========================================================================
    ax.add_patch(patches.FancyBboxPatch(
        (3.5, 73.0), 93.0, 24.0, boxstyle='round,pad=0.0,rounding_size=1.5',
        facecolor=c_l1_bg, edgecolor=c_l1_border, linewidth=1.1, linestyle='--', alpha=0.7, zorder=1))
    ax.text(6.0, 94.2, 'Layer 1 · Asset Modeling & Configuration',
            ha='left', va='center', fontsize=8.6, fontweight='bold', color=c_l1_border, zorder=2)

    _draw_component_box(ax, 7.0, 75.0, 36.5, 16.0, "Asset Authoring Tool",
                        subtext="CAD decomposition, mesh parsing &\nkinematic link definition",
                        bg='#eff6ff', bd=c_l1_border, bar_bg=c_l1_bar, title_fs=7.4, subtext_fs=6.5)

    _draw_component_box(ax, 56.5, 75.0, 36.5, 16.0, "Package Serialization Service",
                        subtext="Virtual pin mapping, submodels\ncompilation & package bundling",
                        bg='#eff6ff', bd=c_l1_border, bar_bg=c_l1_bar, title_fs=7.4, subtext_fs=6.5)

    # Connector between L1 authoring and compiler (gap from 43.5 to 56.5, center at 50.0)
    _assembly_conn(ax, 43.5, 83.0, 56.5, label="Kinematic Tree\n& Metadata", fs=6.2, label_y_offset=2.6)

    # =========================================================================
    # SUBSYSTEM 2: SEMANTIC SERVICES & DATA
    # =========================================================================
    ax.add_patch(patches.FancyBboxPatch(
        (3.5, 38.0), 93.0, 25.0, boxstyle='round,pad=0.0,rounding_size=1.5',
        facecolor=c_l2_bg, edgecolor=c_l2_border, linewidth=1.1, linestyle='--', alpha=0.7, zorder=1))
    ax.text(6.0, 60.5, 'Layer 2 · Semantic Services & Data',
            ha='left', va='center', fontsize=8.6, fontweight='bold', color=c_l2_border, zorder=2)

    _draw_component_box(ax, 7.0, 40.5, 36.5, 16.5, "Model Repository",
                        subtext="Standardized package store,\nsubmodel providers & mesh endpoints",
                        bg='#f0fdf4', bd=c_l2_border, bar_bg=c_l2_bar, title_fs=7.6, subtext_fs=6.5)

    _draw_component_box(ax, 56.5, 40.5, 36.5, 16.5, "Asset Registry & Catalog",
                        subtext="Active twin directory, network\nendpoint resolution & dynamic routing",
                        bg='#f0fdf4', bd=c_l2_border, bar_bg=c_l2_bar, title_fs=7.6, subtext_fs=6.5)

    # Internal L2 Assembly connector (gap from 43.5 to 56.5, center at 50.0)
    _assembly_conn(ax, 43.5, 48.75, 56.5, label="Register &\nIndex", fs=6.2, label_y_offset=2.6)

    # =========================================================================
    # SUBSYSTEM 3: RUNTIME EXECUTION & SYNCHRONIZATION
    # =========================================================================
    ax.add_patch(patches.FancyBboxPatch(
        (3.5, 3.0), 93.0, 26.0, boxstyle='round,pad=0.0,rounding_size=1.5',
        facecolor=c_l3_bg, edgecolor=c_l3_border, linewidth=1.1, linestyle='--', alpha=0.7, zorder=1))
    ax.text(6.0, 26.5, 'Layer 3 · Runtime Execution & Synchronization',
            ha='left', va='center', fontsize=8.6, fontweight='bold', color=c_l3_border, zorder=2)

    # Simulation Runtime Component
    _draw_component_box(ax, 7.0, 5.5, 36.5, 18.0, "Simulation Runtime Engine",
                        subtext="Procedural scene assembly,\nrigid-body dynamics, contact physics\n& discrete sensor pose snapping",
                        bg='#faf5ff', bd='#7e22ce', bar_bg='#f3e8ff', title_fs=7.6, subtext_fs=6.5)

    # Physical Plant Component
    _draw_component_box(ax, 56.5, 5.5, 36.5, 18.0, "Physical Automation Plant",
                        subtext="Conveyors, optical sensors, drives\n& real-time field controller\nexecuting cyclic I/O scanning",
                        bg='#fef2f2', bd='#b91c1c', bar_bg='#fee2e2', title_fs=7.6, subtext_fs=6.5)

    # Formal UML Assembly Connector: Physical Plant provides telemetry interface, Simulation Engine requires it
    # Between Simulation (x=43.5) and Physical (x=56.5) at y=14.5 (matching component centers)
    _assembly_conn(ax, 43.5, 14.5, 56.5, label="Live Telemetry\nUDP Stream",
                   color='#b91c1c', fs=6.2, label_y_offset=2.6, provider_side='right')

    # =========================================================================
    # INTER-SUBSYSTEM FORMAL UML INTERFACES
    # =========================================================================
    # 1. Package Publication: Model Repository (Layer 2) provides the package storage interface (lollipop up).
    # Package Serialization Service (Layer 1) requires/invokes it (socket arc embracing the lollipop from above).
    y_bus1 = 65.5
    # L2 Model Repository provides the interface: stem goes up from (26.5, 57.0) to lollipop at (26.5, y_bus1)
    ax.plot([26.5, 26.5], [57.0, y_bus1], color=c_l2_border, lw=1.3, zorder=4)
    ax.add_patch(plt.Circle((26.5, y_bus1), 1.4, facecolor='#ffffff', edgecolor=c_l2_border, lw=1.3, zorder=5))
    # L1 Serialization Service requires the interface: stem comes down from (73.5, 75.0) to (26.5, y_bus1 + 1.8), arc opens downward towards lollipop
    ax.plot([73.5, 73.5, 26.5], [75.0, y_bus1 + 1.8, y_bus1 + 1.8], color=c_l1_border, lw=1.3, zorder=4)
    arc_p = patches.Arc((26.5, y_bus1), 3.6, 3.6, angle=0, theta1=0, theta2=180,
                        color=c_l1_border, linewidth=1.4, zorder=6)
    ax.add_patch(arc_p)
    ax.text(50.0, y_bus1 + 3.0, "Package Publication Service", ha='center', va='bottom',
            fontsize=6.8, fontweight='bold', color='#1e293b', zorder=7,
            bbox=dict(boxstyle='round,pad=0.25', facecolor='#ffffff', edgecolor='#e2e8f0', linewidth=0.5, alpha=0.96))

    # 2. Asset Discovery & Model Retrieval: Model Repository (L2) provides the interface (lollipop down).
    # Simulation Runtime Engine (L3) requires it (socket arc opening upward from below).
    y_mid2 = 31.0
    # L2 provided interface (lollipop) down from Model Repository (26.5, 40.5)
    ax.plot([26.5, 26.5], [40.5, y_mid2], color=c_l2_border, lw=1.3, zorder=4)
    ax.add_patch(plt.Circle((26.5, y_mid2), 1.4, facecolor='#ffffff', edgecolor=c_l2_border, lw=1.3, zorder=5))
    # L3 required interface (socket) up from Simulation Engine (26.5, 23.5)
    ax.plot([26.5, 26.5], [23.5, y_mid2 - 1.8], color='#7e22ce', lw=1.3, zorder=4)
    arc_r = patches.Arc((26.5, y_mid2), 3.6, 3.6, angle=0, theta1=180, theta2=360,
                        color='#7e22ce', linewidth=1.4, zorder=6)
    ax.add_patch(arc_r)
    ax.text(30.0, y_mid2, "Model Download & Registry Discovery", ha='left', va='center',
            fontsize=6.6, fontweight='bold', color='#1e293b', zorder=7,
            bbox=dict(boxstyle='round,pad=0.25', facecolor='#ffffff', edgecolor='#e2e8f0', linewidth=0.5, alpha=0.96))

    save_fig(fig, "architecture_conceptual")

# =============================================================================
# CONCEPTUAL ASSET METAMODEL (CHAPTER 3, FIGURE 3.2) - FORMAL UML CLASS DIAGRAM
# =============================================================================
def make_asset_metamodel_conceptual():
    fig, ax = plt.subplots(figsize=(8.8, 9.8), dpi=300)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')

    c_border = '#0f172a'
    header_bg = '#f1f5f9'

    # 1. Root Entity: AssetDescriptor (top center: x=24, y=82.0, w=52, h=15.0)
    draw_uml_class(ax, 24, 82.0, 52, 15.0, "AssetDescriptor", stereotype="Root Entity",
                   attributes=[
                       "+ assetId: String [1]",
                       "+ globalAssetId: String [1]",
                       "+ assetType: String [1]",
                       "+ description: String [0..1]"
                   ],
                   operations=None,
                   bg='#ffffff', border=c_border, t_fs=9.2, b_fs=7.6, header_bg='#e2e8f0', header_h=5.2)

    # Central composition stem down from Root (x=50, y=82) to horizontal distribution bus at y=76.0
    draw_uml_composition(ax, (50, 82.0), (50, 76.0), mult_parent="1", mult_child="", color=c_border, lw=1.4)

    # Bus line at y=76.0 connecting the 4 main sub-entities
    ax.plot([14.25, 86.75], [76.0, 76.0], color=c_border, lw=1.4)

    # 1. Drop to VisualStructure (x=3, w=22.5, center=14.25, y: 40.0 to 68.0, h=28.0)
    ax.plot([14.25, 14.25], [76.0, 68.0], color=c_border, lw=1.4)
    ax.text(15.5, 70.0, "1", fontsize=7.8, fontweight='bold', color=c_border)
    draw_uml_class(ax, 3.0, 40.0, 22.5, 28.0, "VisualStructure", stereotype="Facet",
                   attributes=[
                       "+ meshPath: String [1]",
                       "+ localPosition: Vector3 [1]",
                       "+ localRotation: Vector3 [1]",
                       "+ localScale: Vector3 [1]",
                       "+ isDynamic: Boolean [1]"
                   ],
                   operations=None,
                   bg='#ffffff', border=c_border, t_fs=8.4, b_fs=7.2, header_bg=header_bg, header_h=5.2)

    # 2. Drop to KinematicJoint (x=27.5, w=22.5, center=38.75, y: 40.0 to 68.0, h=28.0)
    ax.plot([38.75, 38.75], [76.0, 68.0], color=c_border, lw=1.4)
    ax.text(40.0, 70.0, "0..*", fontsize=7.8, fontweight='bold', color=c_border)
    draw_uml_class(ax, 27.5, 40.0, 22.5, 28.0, "KinematicJoint", stereotype="Facet",
                   attributes=[
                       "+ jointId: String [1]",
                       "+ targetNode: String [1]",
                       "+ motionType: String [1]",
                       "+ maxVelocity: Float [0..1]"
                   ],
                   operations=None,
                   bg='#ffffff', border=c_border, t_fs=8.4, b_fs=7.2, header_bg=header_bg, header_h=5.2)

    # 3. Drop to VirtualPin (x=52.0, w=22.5, center=63.25, y: 40.0 to 68.0, h=28.0)
    ax.plot([63.25, 63.25], [76.0, 68.0], color=c_border, lw=1.4)
    ax.text(64.5, 70.0, "1..*", fontsize=7.8, fontweight='bold', color=c_border)
    draw_uml_class(ax, 52.0, 40.0, 22.5, 28.0, "VirtualPin", stereotype="Entity",
                   attributes=[
                       "+ pinId: String [1]",
                       "+ direction: String [1]",
                       "+ signalType: String [1]",
                       "+ physicalChannel: String [0..1]",
                       "+ defaultValue: String [0..1]"
                   ],
                   operations=None,
                   bg='#ffffff', border=c_border, t_fs=8.4, b_fs=7.2, header_bg=header_bg, header_h=5.2)

    # 4. Drop to NetworkEndpoint (x=76.5, w=20.5, center=86.75, y: 40.0 to 68.0, h=28.0)
    ax.plot([86.75, 86.75], [76.0, 68.0], color=c_border, lw=1.4)
    ax.text(88.0, 70.0, "1..*", fontsize=7.8, fontweight='bold', color=c_border)
    draw_uml_class(ax, 76.5, 40.0, 20.5, 28.0, "NetworkEndpoint", stereotype="Entity",
                   attributes=[
                       "+ endpointId: String [1]",
                       "+ protocol: String [1]",
                       "+ hostAddress: String [1]",
                       "+ port: Integer [1]",
                       "+ role: String [1]"
                   ],
                   operations=None,
                   bg='#ffffff', border=c_border, t_fs=8.4, b_fs=7.2, header_bg=header_bg, header_h=5.2)

    # Composition from VirtualPin down to ControlLogic / Trigger Rule
    # VirtualPin bottom center is at (63.25, 40.0). Rule box top is at 23.0.
    draw_uml_composition(ax, (63.25, 40.0), (63.25, 23.0), mult_parent="1", mult_child="", color=c_border, lw=1.4)
    ax.text(65.0, 24.5, "0..*", fontsize=7.8, fontweight='bold', color=c_border)
    draw_uml_class(ax, 47.0, 5.0, 32.5, 18.0, "ControlLogicRule", stereotype="Facet",
                   attributes=[
                       "+ ruleId: String [1]",
                       "+ triggerCondition: String [1]",
                       "+ targetAction: String [1]"
                   ],
                   operations=None,
                   bg='#ffffff', border=c_border, t_fs=8.6, b_fs=7.4, header_bg=header_bg, header_h=5.2)

    save_fig(fig, "asset_metamodel_conceptual")


def make_individual_metamodel_classes():
    """Generates focused individual UML diagrams for each entity of the metamodel."""
    c_border = '#0f172a'
    header_bg = '#f1f5f9'

    # 1. AssetDescriptor
    fig, ax = plt.subplots(figsize=(4.8, 2.2), dpi=300)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')
    draw_uml_class(ax, 5, 8, 90, 84, "AssetDescriptor", stereotype="Root Entity",
                   attributes=[
                       "+ assetId: String [1]",
                       "+ globalAssetId: String [1]",
                       "+ assetType: String [1]",
                       "+ description: String [0..1]"
                   ],
                   bg='#ffffff', border=c_border, t_fs=9.2, b_fs=8.2, header_bg='#e2e8f0', header_h=24)
    save_fig(fig, "metamodel_asset_descriptor")

    # 2. VisualStructure
    fig, ax = plt.subplots(figsize=(4.8, 2.5), dpi=300)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')
    draw_uml_class(ax, 5, 8, 90, 84, "VisualStructure", stereotype="Facet",
                   attributes=[
                       "+ meshPath: String [1]",
                       "+ localPosition: Vector3 [1]",
                       "+ localRotation: Vector3 [1]",
                       "+ localScale: Vector3 [1]",
                       "+ isDynamic: Boolean [1]"
                   ],
                   bg='#ffffff', border=c_border, t_fs=9.2, b_fs=8.2, header_bg=header_bg, header_h=24)
    save_fig(fig, "metamodel_visual_structure")

    # 3. KinematicJoint
    fig, ax = plt.subplots(figsize=(4.8, 2.4), dpi=300)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')
    draw_uml_class(ax, 5, 8, 90, 84, "KinematicJoint", stereotype="Facet",
                   attributes=[
                       "+ jointId: String [1]",
                       "+ targetNode: String [1]",
                       "+ motionType: String [1]",
                       "+ maxVelocity: Float [0..1]"
                   ],
                   bg='#ffffff', border=c_border, t_fs=9.2, b_fs=8.2, header_bg=header_bg, header_h=24)
    save_fig(fig, "metamodel_kinematic_joint")

    # 4. VirtualPin
    fig, ax = plt.subplots(figsize=(4.8, 2.5), dpi=300)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')
    draw_uml_class(ax, 5, 8, 90, 84, "VirtualPin", stereotype="Entity",
                   attributes=[
                       "+ pinId: String [1]",
                       "+ direction: String [1]",
                       "+ signalType: String [1]",
                       "+ physicalChannel: String [0..1]",
                       "+ defaultValue: String [0..1]"
                   ],
                   bg='#ffffff', border=c_border, t_fs=9.2, b_fs=8.2, header_bg=header_bg, header_h=24)
    save_fig(fig, "metamodel_virtual_pin")

    # 5. ControlLogicRule
    fig, ax = plt.subplots(figsize=(4.8, 2.0), dpi=300)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')
    draw_uml_class(ax, 5, 8, 90, 84, "ControlLogicRule", stereotype="Facet",
                   attributes=[
                       "+ ruleId: String [1]",
                       "+ triggerCondition: String [1]",
                       "+ targetAction: String [1]"
                   ],
                   bg='#ffffff', border=c_border, t_fs=9.2, b_fs=8.2, header_bg=header_bg, header_h=24)
    save_fig(fig, "metamodel_control_logic")

    # 6. NetworkEndpoint
    fig, ax = plt.subplots(figsize=(4.8, 2.5), dpi=300)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')
    draw_uml_class(ax, 5, 8, 90, 84, "NetworkEndpoint", stereotype="Entity",
                   attributes=[
                       "+ endpointId: String [1]",
                       "+ protocol: String [1]",
                       "+ hostAddress: String [1]",
                       "+ port: Integer [1]",
                       "+ role: String [1]"
                   ],
                   bg='#ffffff', border=c_border, t_fs=9.2, b_fs=8.2, header_bg=header_bg, header_h=24)
    save_fig(fig, "metamodel_network_endpoint")

# =============================================================================
# INDIVIDUAL LAYER CONCEPTUAL DIAGRAMS (CHAPTER 3)
# =============================================================================
def make_architecture_layer1():
    fig, ax = plt.subplots(figsize=(8.2, 4.6), dpi=300)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')

    c_bg, c_border = '#eff6ff', '#2563eb'
    draw_group(ax, 2, 3.0, 96, 94.0, "Layer 1 · Asset Modeling & Configuration Tier (Detailed Zoom-In)", c_bg, c_border, fs=10.5)

    # 3 Pipeline Stages: x=4.5 (w=27), x=36.5 (w=27), x=68.5 (w=27)
    # 1. Geometry Stage
    draw_card(ax, 4.5, 8.0, 27.0, 80.0, "3D Geometry &\nKinematic Ingestion",
              ["• CAD File Ingestion",
               "• Mesh Boundary Extraction",
               "• Hierarchy Tree Parsing",
               "• Joint Axis & Motion Limits",
               "• Surface Raycast Targeting"], '#ffffff', c_border, t_fs=8.8, b_fs=7.4, align='left')

    # 2. Semantic Pin Binding Stage
    draw_card(ax, 36.5, 8.0, 27.0, 80.0, "Semantic Parameterization\n& Virtual Pins",
              ["• Virtual Input Pins (Sensors)",
               "• Virtual Output Pins (Drives)",
               "• Surface Anchor Snapping",
               "• Electrical Signal Semantics",
               "• Rule & Interlock Definitions"], '#ffffff', c_border, t_fs=8.8, b_fs=7.4, align='left')

    # 3. Packaging & Publication Stage
    draw_card(ax, 68.5, 8.0, 27.0, 80.0, "Standardized Packaging\n& Publication",
              ["• Five Standard Submodels",
               "• Geometric Asset Bundling",
               "• Global Identifier Binding",
               "• Archive Serialization",
               "• Model Publication Endpoint"], '#ffffff', c_border, t_fs=8.8, b_fs=7.4, align='left')

    # Connecting horizontal arrows with clear gaps
    draw_arrow(ax, (31.5, 48.0), (36.5, 48.0), style='->', lw=1.8, color=c_border, head_size=1.0)
    draw_badge(ax, 34.0, 54.0, "Kinematics", color=c_border, fs=6.5)

    draw_arrow(ax, (63.5, 48.0), (68.5, 48.0), style='->', lw=1.8, color=c_border, head_size=1.0)
    draw_badge(ax, 66.0, 54.0, "Parameters", color=c_border, fs=6.5)

    save_fig(fig, "architecture_layer1")

def make_architecture_layer2():
    fig, ax = plt.subplots(figsize=(8.2, 5.4), dpi=300)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')

    c_bg, c_border = '#f0fdf4', '#16a34a'
    draw_group(ax, 2, 3.0, 96, 94.0, "Layer 2 · Semantic Services & Data Tier (Detailed Zoom-In)", c_bg, c_border, fs=10.5)

    # Top Row: x=5 (w=39), x=56 (w=39) across gap 44 to 56
    draw_card(ax, 5.0, 51.0, 39.0, 37.0, "Model Repository\n(Asset & Submodel Store)", 
              ["• Semantic Shell Archive Ingestion",
               "• Submodel Data Schema Providers",
               "• 3D Geometry File Streaming API",
               "• RESTful CRUD Query Interface"], 
              '#ffffff', c_border, t_fs=8.8, b_fs=7.5, align='left')
    
    draw_card(ax, 56.0, 51.0, 39.0, 37.0, "Asset Registry\n(Discovery Directory)", 
              ["• Active Asset Identifier Catalog",
               "• Network Endpoint Resolution",
               "• Dynamic Twin Lookup & Routing",
               "• Live Topology State Discovery"], 
              '#ffffff', c_border, t_fs=8.8, b_fs=7.5, align='left')

    # Bottom Row: x=5 (w=39), x=56 (w=39)
    draw_card(ax, 5.0, 8.0, 39.0, 29.0, "Configuration Database\n(Persistence Engine)", 
              ["• Persistent Storage for Descriptors",
               "• Topology Graphs & Network Routes",
               "• Asset Versioning & Change Log"], 
              '#ffffff', '#b45309', t_fs=8.6, b_fs=7.3, align='left')
    
    draw_card(ax, 56.0, 8.0, 39.0, 29.0, "Supervisory Dashboard\n(Management & Inspection UI)", 
              ["• Interactive Submodel Tree Inspection",
               "• Operational Property Visualization",
               "• Registry Endpoint Health Monitor"], 
              '#ffffff', '#7e22ce', t_fs=8.6, b_fs=7.3, linestyle='--', align='left')

    # Horizontal arrow between repo and registry (gap 44 to 56)
    draw_arrow(ax, (44.0, 69.5), (56.0, 69.5), style='<->', lw=1.8, color=c_border, head_size=1.0)
    draw_badge(ax, 50.0, 69.5, "Index &\nRegister", color=c_border, fs=6.5)

    # Vertical arrows down to DB and UI across gap 51 to 37
    draw_arrow(ax, (24.5, 51.0), (24.5, 37.0), style='->', lw=1.8, color='#b45309', head_size=1.0)
    draw_badge(ax, 24.5, 44.0, "Persist", color='#b45309', fs=6.8)

    draw_arrow(ax, (75.5, 51.0), (75.5, 37.0), style='->', lw=1.8, color='#7e22ce', dashed=True, head_size=1.0)
    draw_badge(ax, 75.5, 44.0, "Inspect", color='#7e22ce', fs=6.8)

    save_fig(fig, "architecture_layer2")

def make_architecture_layer3():
    fig, ax = plt.subplots(figsize=(8.2, 5.8), dpi=300)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')

    c_bg, c_border = '#faf5ff', '#9333ea'
    draw_group(ax, 2, 2.0, 96, 96.0, "Layer 3 · Runtime Execution & Physical Synchronization (Detailed Zoom-In)", c_bg, c_border, fs=10.5)

    # Left: Simulation Runtime container (x=4.0, w=40.5, ends at 44.5)
    rect_u = patches.FancyBboxPatch((4.0, 4.5), 40.5, 83.5, boxstyle="round,pad=0.4,rounding_size=1.2",
                                    facecolor='#ffffff', edgecolor='#a855f7', linewidth=1.5, zorder=2)
    ax.add_patch(rect_u)
    ax.text(6.0, 84.5, "Simulation Runtime Engine", fontsize=9.2, fontweight='bold', color='#7e22ce', zorder=3)

    draw_card(ax, 6.0, 58.0, 36.5, 20.0, "Semantic Scene Ingestion", 
              ["• Discover Active Twin Models", "• Procedural Mesh Instantiation", "• Pin-to-Component Mapping"], '#f5f3ff', '#a855f7', t_fs=8.5, b_fs=7.2, align='left')
    
    draw_card(ax, 6.0, 32.5, 36.5, 20.0, "Physics & Kinematics Engine", 
              ["• Rigid Body Dynamics & Contact", "• Continuous Conveyor Belt Motion", "• Workpiece Kinematic Constraints"], '#f5f3ff', '#a855f7', t_fs=8.5, b_fs=7.2, align='left')

    draw_card(ax, 6.0, 7.0, 36.5, 20.0, "Drift Correction & Sync", 
              ["• Real-Time Event Demultiplexer", "• State & Pose Interpolation", "• Target Surface Snapping"], '#f5f3ff', '#a855f7', t_fs=8.5, b_fs=7.2, align='left')

    # Vertical arrows in simulation engine
    draw_arrow(ax, (24.2, 58.0), (24.2, 52.5), style='->', lw=1.6, color='#a855f7', head_size=0.9)
    draw_arrow(ax, (24.2, 32.5), (24.2, 27.0), style='->', lw=1.6, color='#a855f7', head_size=0.9)

    # Right: Physical Equipment container (x=55.5, w=40.5, gap between 44.5 and 55.5 = 11 units)
    rect_f = patches.FancyBboxPatch((55.5, 4.5), 40.5, 83.5, boxstyle="round,pad=0.4,rounding_size=1.2",
                                    facecolor='#ffffff', edgecolor='#ef4444', linewidth=1.5, zorder=2)
    ax.add_patch(rect_f)
    ax.text(57.0, 84.5, "Physical Equipment & Embedded Controller", fontsize=8.8, fontweight='bold', color='#dc2626', zorder=3)

    draw_card(ax, 57.5, 58.0, 36.0, 20.0, "Real-Time Controller", 
              ["• Deterministic Task Scheduling", "• High-Frequency I/O Scanning", "• Low-Latency Network Stack"], '#fef2f2', '#ef4444', t_fs=8.5, b_fs=7.2, align='left')
    
    draw_card(ax, 57.5, 32.5, 36.0, 20.0, "Physical Sensor Subsystem", 
              ["• Optical Breakbeam Detection", "• Inductive Position Sensing", "• Optocoupled Signal Isolation"], '#fef2f2', '#ef4444', t_fs=8.5, b_fs=7.2, align='left')
    
    draw_card(ax, 57.5, 7.0, 36.0, 20.0, "Actuation & Field Drives", 
              ["• Conveyor Geared Drive Motors", "• Pneumatic Stoppers & Gates", "• Opto-Isolated Power Drivers"], '#fef2f2', '#ef4444', t_fs=8.5, b_fs=7.2, align='left')

    # Vertical arrows in physical controller
    draw_arrow(ax, (75.5, 58.0), (75.5, 52.5), style='->', lw=1.6, color='#dc2626', head_size=0.9)
    draw_arrow(ax, (75.5, 32.5), (75.5, 27.0), style='->', lw=1.6, color='#dc2626', head_size=0.9)

    # Longer Stream between Left and Right across gap 44.5 to 55.5
    draw_arrow(ax, (44.5, 42.5), (55.5, 42.5), style='<->', lw=1.8, color='#b91c1c', head_size=1.0)
    draw_badge(ax, 50.0, 42.5, "Direct Fast\nTelemetry", color='#b91c1c', fs=6.5)

    save_fig(fig, "architecture_layer3")


def make_usecase_generic():
    """Generic (technology-agnostic) Use Case diagram for Chapter 3."""
    fig, ax = plt.subplots(figsize=(8.0, 6.2), dpi=300)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')

    # ── colour palette ───────────────────────────────────────────────────────
    C_SYS   = '#f8faff'
    C_BORD  = '#334155'
    C_UC    = '#e0e7ff'
    C_UCBRD = '#4338ca'
    C_LINE  = '#64748b'
    C_ACT   = '#1e293b'

    # ── helpers ───────────────────────────────────────────────────────────────
    def stick_figure(cx, cy, label, label_side='left'):
        """Draw a UML stick-figure actor."""
        head_r = 2.2
        # head
        ax.add_patch(plt.Circle((cx, cy + 10), head_r, color=C_ACT, zorder=3))
        # body
        ax.plot([cx, cx], [cy + 7.8, cy + 2.5], color=C_ACT, lw=1.5, zorder=3)
        # arms
        ax.plot([cx - 3.5, cx + 3.5], [cy + 5.5, cy + 5.5], color=C_ACT, lw=1.5, zorder=3)
        # legs
        ax.plot([cx, cx - 3.0], [cy + 2.5, cy - 1.5], color=C_ACT, lw=1.5, zorder=3)
        ax.plot([cx, cx + 3.0], [cy + 2.5, cy - 1.5], color=C_ACT, lw=1.5, zorder=3)
        # label
        ha = 'right' if label_side == 'left' else 'left'
        offset = -3.5 if label_side == 'left' else 3.5
        ax.text(cx + offset, cy + 3.5, label, ha=ha, va='center',
                fontsize=7.5, fontweight='bold', color=C_ACT, zorder=4,
                multialignment='center')

    def use_case(cx, cy, label, w=22, h=7):
        """Draw a UML use-case ellipse."""
        ell = patches.Ellipse((cx, cy), w, h,
                              facecolor=C_UC, edgecolor=C_UCBRD, linewidth=1.4, zorder=2)
        ax.add_patch(ell)
        ax.text(cx, cy, label, ha='center', va='center',
                fontsize=7.0, color='#1e1b4b', zorder=3, multialignment='center')

    def connect(ax1, ay1, ax2, ay2):
        """Draw a plain association line."""
        ax.plot([ax1, ax2], [ay1, ay2], color=C_LINE, lw=1.1, zorder=1)

    def include_arrow(x1, y1, x2, y2, label='«include»'):
        """Dashed include dependency."""
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color=C_LINE,
                                   linestyle='dashed', lw=1.0), zorder=1)
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx, my + 1.5, label, ha='center', va='bottom',
                fontsize=5.8, fontstyle='italic', color=C_LINE, zorder=3)

    # ── system boundary ───────────────────────────────────────────────────────
    sys_x, sys_y, sys_w, sys_h = 18, 5, 64, 90
    ax.add_patch(patches.FancyBboxPatch(
        (sys_x, sys_y), sys_w, sys_h,
        boxstyle='round,pad=0.5', linewidth=1.8,
        edgecolor=C_BORD, facecolor=C_SYS, zorder=0))
    ax.text(sys_x + sys_w / 2, sys_y + sys_h - 3.5,
            'Digital Twin Framework',
            ha='center', va='center', fontsize=9.0,
            fontweight='bold', color=C_BORD, zorder=1)

    # ── use cases (cx, cy) ────────────────────────────────────────────────────
    uc_positions = {
        'uc1': (50, 83, 'Author Asset\nPackage'),
        'uc2': (50, 68, 'Publish Asset\nto Registry'),
        'uc3': (50, 53, 'Discover Available\nAssets'),
        'uc4': (50, 38, 'Assemble\nVirtual Scene'),
        'uc5': (50, 23, 'Synchronize\nwith Physical Equipment'),
        'uc6': (50, 10, 'Monitor\nAsset State'),
    }
    for key, (cx, cy, lbl) in uc_positions.items():
        use_case(cx, cy, lbl)

    # ── actors ────────────────────────────────────────────────────────────────
    # Automation Engineer — left
    eng_x, eng_y = 7, 72
    stick_figure(eng_x, eng_y, 'Automation\nEngineer', label_side='right')

    # Simulation Runtime — right, top
    sim_x, sim_y = 93, 45
    stick_figure(sim_x, sim_y, 'Simulation\nRuntime', label_side='left')

    # Physical Controller — right, bottom
    phy_x, phy_y = 93, 18
    stick_figure(phy_x, phy_y, 'Physical\nController', label_side='left')

    # ── associations ──────────────────────────────────────────────────────────
    # Engineer → uc1, uc2
    connect(eng_x + 2, eng_y + 9, uc_positions['uc1'][0] - 11, uc_positions['uc1'][1])
    connect(eng_x + 2, eng_y + 5, uc_positions['uc2'][0] - 11, uc_positions['uc2'][1])

    # Simulation Runtime → uc3, uc4, uc5, uc6
    connect(sim_x - 2, sim_y + 9, uc_positions['uc3'][0] + 11, uc_positions['uc3'][1])
    connect(sim_x - 2, sim_y + 6, uc_positions['uc4'][0] + 11, uc_positions['uc4'][1])
    connect(sim_x - 2, sim_y + 3, uc_positions['uc5'][0] + 11, uc_positions['uc5'][1])
    connect(sim_x - 2, sim_y,     uc_positions['uc6'][0] + 11, uc_positions['uc6'][1])

    # Physical Controller → uc5
    connect(phy_x - 2, phy_y + 8, uc_positions['uc5'][0] + 11, uc_positions['uc5'][1])

    # ── include dependencies ──────────────────────────────────────────────────
    # Publish includes Discover (registry must know about it)
    include_arrow(50, 64.5, 50, 56.5)
    # Assemble includes Discover
    include_arrow(50, 49.5, 50, 41.5)

    save_fig(fig, "usecase_generic")




# =============================================================================
# UML COMPONENT DIAGRAMS  (alternative to architecture_layer*.pdf)
# Saved as component_layer1/2/3.pdf  — originals untouched
# =============================================================================





# -----------------------------------------------------------------------------
# LAYER 1: COMPONENT DIAGRAM
# -----------------------------------------------------------------------------
def make_component_layer1():
    """Publication-quality UML Component Diagram for Layer 1."""
    p = _comp_palette('blue')
    fig, ax = plt.subplots(figsize=(8.4, 4.4), dpi=300)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')

    # Outer Subsystem Box
    sub_x, sub_y, sub_w, sub_h = 9.0, 8.0, 82.0, 84.0
    ax.add_patch(patches.FancyBboxPatch(
        (sub_x, sub_y), sub_w, sub_h, boxstyle='round,pad=0.0,rounding_size=1.5',
        facecolor=p['sub_bg'], edgecolor=p['sub_bd'], linewidth=1.5, linestyle='--', zorder=1))
    
    ax.text(sub_x + 3.0, sub_y + sub_h - 3.2, '«subsystem» Asset Modeling and Configuration Tier',
            ha='left', va='center', fontsize=8.2, fontweight='bold', color=p['sub_bd'], zorder=2)

    # 3 Pipeline Stage Components (clean, no bullets)
    c1_w, c1_h = 22.0, 52.0
    y_c = 18.0
    x1 = 12.5
    x2 = 39.0
    x3 = 65.5

    _draw_component_box(ax, x1, y_c, c1_w, c1_h, "Geometry &\nKinematics Ingest",
                        subtext="Parses 3D geometry,\nextracts part tree &\njoint constraints",
                        bg=p['box_bg'], bd=p['box_bd'], bar_bg=p['bar_bg'], title_fs=7.2)

    _draw_component_box(ax, x2, y_c, c1_w, c1_h, "Semantic &\nPin Annotator",
                        subtext="Maps virtual I/O pins,\nsensing envelopes &\nkinematic limits",
                        bg=p['box_bg'], bd=p['box_bd'], bar_bg=p['bar_bg'], title_fs=7.2)

    _draw_component_box(ax, x3, y_c, c1_w, c1_h, "Standardized\nPackage Compiler",
                        subtext="Compiles submodels,\nbinds global ID &\nvalidates package",
                        bg=p['box_bg'], bd=p['box_bd'], bar_bg=p['bar_bg'], title_fs=7.2)

    # Assembly connectors between stages
    _assembly_conn(ax, x1 + c1_w, y_c + c1_h/2.0, x2, label="Kinematic\nStructure", fs=6.2, label_y_offset=2.6)
    _assembly_conn(ax, x2 + c1_w, y_c + c1_h/2.0, x3, label="Parametrized\nMetadata", fs=6.2, label_y_offset=2.6)

    # Input Socket on the left: «CAD / Mesh Model»
    _socket_iface(ax, (x1, y_c + c1_h/2.0), (2.0, y_c + c1_h/2.0), label="3D Geometry File\n(GLB / URDF)", label_pos='top',
                  color=p['iface_c'], r=1.6, arc_side='left', fs=6.5)

    # Output Lollipop on the right: «Standardized Package»
    _lollipop_iface(ax, (x3 + c1_w, y_c + c1_h/2.0), (98.0, y_c + c1_h/2.0), label="Standard Asset Package\n(Export / Upload)", label_pos='top',
                    color=p['iface_c'], r=1.6, fs=6.5)

    save_fig(fig, "component_layer1")


# -----------------------------------------------------------------------------
# LAYER 2: COMPONENT DIAGRAM
# -----------------------------------------------------------------------------
def make_component_layer2():
    """Publication-quality UML Component Diagram for Layer 2."""
    p = _comp_palette('green')
    fig, ax = plt.subplots(figsize=(8.4, 5.2), dpi=300)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')

    # Outer Subsystem Box
    sub_x, sub_y, sub_w, sub_h = 9.0, 6.0, 82.0, 86.0
    ax.add_patch(patches.FancyBboxPatch(
        (sub_x, sub_y), sub_w, sub_h, boxstyle='round,pad=0.0,rounding_size=1.5',
        facecolor=p['sub_bg'], edgecolor=p['sub_bd'], linewidth=1.5, linestyle='--', zorder=1))
    
    ax.text(sub_x + 3.0, sub_y + sub_h - 3.2, '«subsystem» Semantic Services and Data Tier',
            ha='left', va='center', fontsize=8.2, fontweight='bold', color=p['sub_bd'], zorder=2)

    # 4 Components (2x2 Grid)
    cw, ch = 34.5, 30.0
    x_l = 13.0
    x_r = 52.5
    y_top = 52.0
    y_bot = 12.0

    _draw_component_box(ax, x_l, y_top, cw, ch, "Model Repository Component",
                        subtext="Stores validated descriptors,\ngeometry files & CRUD APIs",
                        bg=p['box_bg'], bd=p['box_bd'], bar_bg=p['bar_bg'], title_fs=7.4)

    _draw_component_box(ax, x_r, y_top, cw, ch, "Asset Registry Component",
                        subtext="Directory service for active twins,\nURI lookup & client routing",
                        bg=p['box_bg'], bd=p['box_bd'], bar_bg=p['bar_bg'], title_fs=7.4)

    _draw_component_box(ax, x_l, y_bot, cw, ch, "Configuration & Metadata Store",
                        subtext="Persistent storage for indices,\nsystem state & revision logs",
                        bg=p['box_bg'], bd=p['box_bd'], bar_bg=p['bar_bg'], title_fs=7.4)

    _draw_component_box(ax, x_r, y_bot, cw, ch, "Supervisory Dashboard (Optional)",
                        subtext="Administrative inspection UI\nfor model validation & monitoring",
                        bg=p['box_bg'], bd=p['box_bd'], bar_bg=p['bar_bg'], title_fs=7.4)

    # Connectors between components
    _assembly_conn(ax, x_l + cw, y_top + ch/2.0, x_r, label="Register &\nIndex", fs=6.2, label_y_offset=2.6)

    # Repo -> Config Store
    _dep_link(ax, (x_l + cw/2.0, y_top), (x_l + cw/2.0, y_bot + ch), label="«persist»", color=p['dep_c'], label_side='right')

    # Registry -> Dashboard
    _dep_link(ax, (x_r + cw/2.0, y_top), (x_r + cw/2.0, y_bot + ch), label="«inspect»", color=p['dep_c'], label_side='right')

    # External Ingress from Layer 1 (Left)
    _socket_iface(ax, (x_l, y_top + ch/2.0), (2.0, y_top + ch/2.0), label="Package Upload\nInterface", label_pos='top',
                  color=p['iface_c'], r=1.6, arc_side='left', fs=6.5)

    # External Egress to Layer 3 (Right)
    _lollipop_iface(ax, (x_r + cw, y_top + ch/2.0 + 5.0), (98.0, y_top + ch/2.0 + 5.0), label="Asset Discovery Service\n(Registry Query)",
                    label_pos='top', color=p['iface_c'], r=1.6, fs=6.5)
    _lollipop_iface(ax, (x_r + cw, y_top + ch/2.0 - 6.0), (98.0, y_top + ch/2.0 - 6.0), label="Model & Data Retrieval\n(Package Stream)",
                    label_pos='bottom', color=p['iface_c'], r=1.6, fs=6.5)

    save_fig(fig, "component_layer2")


# -----------------------------------------------------------------------------
# LAYER 3: COMPONENT DIAGRAM
# -----------------------------------------------------------------------------
def make_component_layer3():
    """Publication-quality UML Component Diagram for Layer 3."""
    p = _comp_palette('mixed')
    fig, ax = plt.subplots(figsize=(8.4, 5.8), dpi=300)
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis('off')

    # Simulation Subsystem Box (Left)
    sub_w = 40.0
    sub_h = 86.0
    y_sub = 6.0
    x_sim = 8.5
    x_phy = 51.5

    ax.add_patch(patches.FancyBboxPatch(
        (x_sim, y_sub), sub_w, sub_h, boxstyle='round,pad=0.0,rounding_size=1.5',
        facecolor=p['sub_bg_sim'], edgecolor=p['sub_bd_sim'], linewidth=1.5, linestyle='--', zorder=1))
    ax.text(x_sim + 3.0, y_sub + sub_h - 3.2, '«subsystem» Simulation Runtime',
            ha='left', va='center', fontsize=8.0, fontweight='bold', color=p['sub_bd_sim'], zorder=2)

    # Physical Subsystem Box (Right)
    ax.add_patch(patches.FancyBboxPatch(
        (x_phy, y_sub), sub_w, sub_h, boxstyle='round,pad=0.0,rounding_size=1.5',
        facecolor=p['sub_bg_phy'], edgecolor=p['sub_bd_phy'], linewidth=1.5, linestyle='--', zorder=1))
    ax.text(x_phy + 3.0, y_sub + sub_h - 3.2, '«subsystem» Physical Automation Plant',
            ha='left', va='center', fontsize=8.0, fontweight='bold', color=p['sub_bd_phy'], zorder=2)

    # Simulation Components (3 vertical stacked, clean no bullets)
    cw_sub = 34.0
    ch_sub = 21.0
    x_in_sim = x_sim + 3.0
    x_in_phy = x_phy + 3.0
    y_c1 = 64.0
    y_c2 = 38.0
    y_c3 = 12.0

    _draw_component_box(ax, x_in_sim, y_c1, cw_sub, ch_sub, "Scene Ingestion Component",
                        subtext="Discovers active descriptors &\ninstantiates virtual 3D hierarchy",
                        bg=p['box_bg_sim'], bd=p['box_bd_sim'], bar_bg=p['bar_bg_sim'])

    _draw_component_box(ax, x_in_sim, y_c2, cw_sub, ch_sub, "Physics & Kinematics Engine",
                        subtext="Simulates surface friction,\nrigid-body contact & kinematics",
                        bg=p['box_bg_sim'], bd=p['box_bd_sim'], bar_bg=p['bar_bg_sim'])

    _draw_component_box(ax, x_in_sim, y_c3, cw_sub, ch_sub, "Drift Corrector & Sync Engine",
                        subtext="Interpolates continuous poses &\napplies discrete sensor snapping",
                        bg=p['box_bg_sim'], bd=p['box_bd_sim'], bar_bg=p['bar_bg_sim'])

    # Internal Simulation Dependencies
    _dep_link(ax, (x_in_sim + cw_sub/2, y_c1), (x_in_sim + cw_sub/2, y_c2 + ch_sub), label="«instantiates»", label_side='right')
    _dep_link(ax, (x_in_sim + cw_sub/2, y_c2), (x_in_sim + cw_sub/2, y_c3 + ch_sub), label="«corrects»", label_side='right')

    # Physical Components (3 vertical stacked)
    _draw_component_box(ax, x_in_phy, y_c1, cw_sub, ch_sub, "Embedded Controller Component",
                        subtext="Deterministic real-time scheduling,\nI/O scan cycle & socket stream",
                        bg=p['box_bg_phy'], bd=p['box_bd_phy'], bar_bg=p['bar_bg_phy'])

    _draw_component_box(ax, x_in_phy, y_c2, cw_sub, ch_sub, "Physical Sensing Subsystem",
                        subtext="Optical & inductive detectors,\nhardware isolation & debounce",
                        bg=p['box_bg_phy'], bd=p['box_bd_phy'], bar_bg=p['bar_bg_phy'])

    _draw_component_box(ax, x_in_phy, y_c3, cw_sub, ch_sub, "Actuation & Field Drives",
                        subtext="Conveyor drive motors, pneumatic\nstoppers & opto-isolated relays",
                        bg=p['box_bg_phy'], bd=p['box_bd_phy'], bar_bg=p['bar_bg_phy'])

    # Internal Physical Dependencies
    _dep_link(ax, (x_in_phy + cw_sub/2, y_c1), (x_in_phy + cw_sub/2, y_c2 + ch_sub), label="«samples»", label_side='right')
    _dep_link(ax, (x_in_phy + cw_sub/2, y_c2), (x_in_phy + cw_sub/2, y_c3 + ch_sub), label="«actuates»", label_side='right')

    # External Ingress from Layer 2 (Left on Scene Ingestion Component)
    _socket_iface(ax, (x_in_sim, y_c1 + 13), (2.0, y_c1 + 13), label="Asset Registry\nService", label_pos='top',
                  color=p['iface_c'], r=1.6, arc_side='left', fs=6.3)
    _socket_iface(ax, (x_in_sim, y_c1 + 4), (2.0, y_c1 + 4), label="Model Download\nService", label_pos='bottom',
                  color=p['iface_c'], r=1.6, arc_side='left', fs=6.3)

    # Telemetry Channel between Physical Controller and Drift Corrector
    y_telem = y_c3 + ch_sub/2.0
    ax.annotate('', xy=(x_in_sim + cw_sub, y_telem), xytext=(x_in_phy, y_telem),
                arrowprops=dict(arrowstyle='<->', color='#b91c1c', lw=2.0), zorder=5)
    
    # Badge for telemetry
    ax.add_patch(patches.FancyBboxPatch(
        (45.5, y_telem - 3.2), 9.0, 6.4, boxstyle='round,pad=0.3',
        facecolor='#fee2e2', edgecolor='#b91c1c', lw=1.2, zorder=6))
    ax.text(50.0, y_telem, "Low-Latency\nTelemetry", ha='center', va='center',
            fontsize=6.0, fontweight='bold', color='#b91c1c', zorder=7)

    save_fig(fig, "component_layer3")
    

if __name__ == "__main__":
    make_architecture_conceptual()
    make_asset_metamodel_conceptual()
    make_individual_metamodel_classes()
    make_architecture_layer1()
    make_architecture_layer2()
    make_architecture_layer3()
    make_usecase_generic()
    make_component_layer1()
    make_component_layer2()
    make_component_layer3()



