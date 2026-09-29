# -*- coding: utf-8 -*-
"""
Thesis Illustration Utilities
Robust layout, auto-wrapping, and styling helpers for publication-grade thesis diagrams.
"""
import os
import textwrap
import matplotlib.pyplot as plt
import matplotlib.patches as patches

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
POSSIBLE_DIRS = [
    os.path.abspath(os.path.join(SCRIPT_DIR, "..", "5-Figures")),
    os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "5-Figures")),
    os.path.abspath(os.path.join(SCRIPT_DIR, "..", "Figures")),
    os.path.abspath(os.path.join(SCRIPT_DIR, "5-Figures")),
    os.path.abspath("Documentos/5-Figures"),
    os.path.abspath("5-Figures"),
]
OUT_DIRS = [d for d in dict.fromkeys(POSSIBLE_DIRS) if os.path.isdir(d)]

def save_fig(fig, name):
    import time
    for d in OUT_DIRS:
        pdf_path = os.path.join(d, f"{name}.pdf")
        png_path = os.path.join(d, f"{name}.png")
        for attempt in range(5):
            try:
                fig.savefig(pdf_path, bbox_inches='tight', pad_inches=0.06)
                fig.savefig(png_path, bbox_inches='tight', pad_inches=0.06, dpi=300)
                break
            except Exception as e:
                if attempt == 4:
                    print(f"[WARN] Failed to write {name} to {d}: {e}")
                else:
                    time.sleep(0.3)
    plt.close(fig)
    print(f"[OK] Rendered: {name}.pdf / .png (saved to {len(OUT_DIRS)} dirs)")

def wrap_text_list(lines, max_chars):
    wrapped = []
    for line in lines:
        if len(line) <= max_chars:
            wrapped.append(line)
        else:
            prefix = ""
            content = line
            if line.startswith("• "):
                prefix = "• "
                content = line[2:]
            elif line.startswith("- "):
                prefix = "- "
                content = line[2:]
            
            sub = textwrap.wrap(content, width=max_chars - len(prefix))
            for idx, s in enumerate(sub):
                if idx == 0:
                    wrapped.append(prefix + s)
                else:
                    wrapped.append("  " + s)
    return wrapped

def draw_group(ax, x, y, w, h, label, bg, border, fs=10.5, lw=1.6, header_pos='top-left'):
    rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.5,rounding_size=1.2",
                                  facecolor=bg, edgecolor=border, linewidth=lw, zorder=1)
    ax.add_patch(rect)
    if label:
        header_y = y + h - max(0.065 * h, 3.2)
        if header_pos == 'top-left':
            ax.text(x + 2.5, header_y, label, ha='left', va='center', fontsize=fs, fontweight='bold', color=border, zorder=2)
        elif header_pos == 'top-center':
            ax.text(x + w/2, header_y, label, ha='center', va='center', fontsize=fs, fontweight='bold', color=border, zorder=2)

def draw_card(ax, x, y, w, h, title, lines=None, bg='#ffffff', border='#3b82f6', t_fs=9.2, b_fs=7.8, lw=1.3, align='center', max_chars=None, linestyle='-'):
    rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.0",
                                  facecolor=bg, edgecolor=border, linewidth=lw, linestyle=linestyle, zorder=3)
    ax.add_patch(rect)

    t_lines = title.split('\n')
    if not lines:
        if len(t_lines) == 1:
            ax.text(x + w/2, y + h/2, title, ha='center', va='center', fontsize=t_fs, fontweight='bold', color='#0f172a', zorder=4)
        else:
            n_t = len(t_lines)
            line_spacing = t_fs * 0.35  # coordinate units per line
            total_block_h = (n_t - 1) * line_spacing
            start_y = y + h/2 + total_block_h/2
            for i, tl in enumerate(t_lines):
                ax.text(x + w/2, start_y - i * line_spacing, tl, ha='center', va='center', fontsize=t_fs, fontweight='bold', color='#0f172a', zorder=4)
        return

    # Title with lines below
    title_gap = max(t_fs * 0.42, 3.2)
    if len(t_lines) == 1:
        ax.text(x + w/2, y + h - title_gap * 0.8, t_lines[0], ha='center', va='center', fontsize=t_fs, fontweight='bold', color='#0f172a', zorder=4)
        top_offset = min(title_gap * 1.8, 0.45 * h)
    elif len(t_lines) == 2:
        ax.text(x + w/2, y + h - title_gap * 0.7, t_lines[0], ha='center', va='center', fontsize=t_fs, fontweight='bold', color='#0f172a', zorder=4)
        ax.text(x + w/2, y + h - title_gap * 1.5, t_lines[1], ha='center', va='center', fontsize=t_fs*0.95, fontweight='bold', color='#1e293b', zorder=4)
        top_offset = min(title_gap * 2.5, 0.48 * h)
    else:
        top_offset = min(title_gap * (len(t_lines) + 0.6), 0.5 * h)
        for i, tl in enumerate(t_lines):
            ax.text(x + w/2, y + h - (i + 0.8) * title_gap, tl, ha='center', va='center', fontsize=t_fs, fontweight='bold', color='#0f172a', zorder=4)

    # Wrap body lines - conservative char limit to prevent border clipping
    calc_chars = max_chars if max_chars else max(int(w * 1.10), 12)
    final_lines = wrap_text_list(lines, calc_chars)

    n = len(final_lines)
    avail_h = max(h - top_offset - 0.05 * h, 0.1)
    spacing = avail_h / max(n, 1)
    for i, line in enumerate(final_lines):
        ly = y + h - top_offset - (i + 0.5) * spacing
        if align == 'center':
            ax.text(x + w/2, ly, line, ha='center', va='center', fontsize=b_fs, color='#334155', zorder=4)
        else:
            ax.text(x + 1.8, ly, line, ha='left', va='center', fontsize=b_fs, color='#334155', zorder=4)

def draw_badge(ax, x, y, text, color='#1e293b', bg='#ffffff', border=None, fs=8.0):
    if border is None:
        border = color
    ax.text(x, y, text, ha='center', va='center', fontsize=fs, fontweight='bold', color=color,
            bbox=dict(boxstyle='round,pad=0.22,rounding_size=0.3', facecolor=bg, edgecolor=border, lw=0.9),
            zorder=8)

def draw_arrow(ax, p1, p2, label="", label_pos=None, color='#1e293b', style='->', lw=1.8, dashed=False, b_fs=8.0, head_size=1.0):
    ls = '--' if dashed else '-'
    hl = 0.55 * head_size
    hw = 0.35 * head_size
    if style == '->':
        arr_style = f"-|>,head_length={hl:.2f},head_width={hw:.2f}"
    elif style == '<->':
        arr_style = f"<|-|>,head_length={hl:.2f},head_width={hw:.2f}"
    elif style == '<-':
        arr_style = f"<|-,head_length={hl:.2f},head_width={hw:.2f}"
    else:
        arr_style = style
        
    ax.annotate('', xy=p2, xytext=p1,
                arrowprops=dict(arrowstyle=arr_style, color=color, lw=lw, linestyle=ls, shrinkA=2, shrinkB=2),
                zorder=5)
    if label:
        lx = (p1[0] + p2[0])/2 if label_pos is None else label_pos[0]
        ly = (p1[1] + p2[1])/2 if label_pos is None else label_pos[1]
        draw_badge(ax, lx, ly, label, color=color, bg='#ffffff', border=color, fs=b_fs)

def draw_ellipse_uc(ax, x, y, w, h, title, subtitle="", bg='#e0f2fe', border='#0284c7', t_fs=8.8, s_fs=7.5):
    ell = patches.Ellipse((x, y), w, h, facecolor=bg, edgecolor=border, linewidth=1.5, zorder=3)
    ax.add_patch(ell)
    if subtitle:
        ax.text(x, y + h*0.18, title, ha='center', va='center', fontsize=t_fs, fontweight='bold', color='#0f172a', zorder=4)
        ax.text(x, y - h*0.18, subtitle, ha='center', va='center', fontsize=s_fs, color='#334155', zorder=4)
    else:
        tl = title.split('\n')
        if len(tl) == 1:
            ax.text(x, y, title, ha='center', va='center', fontsize=t_fs, fontweight='bold', color='#0f172a', zorder=4)
        elif len(tl) == 2:
            ax.text(x, y + h * 0.18, tl[0], ha='center', va='center', fontsize=t_fs, fontweight='bold', color='#0f172a', zorder=4)
            ax.text(x, y - h * 0.18, tl[1], ha='center', va='center', fontsize=t_fs, fontweight='bold', color='#0f172a', zorder=4)
        else:
            ax.text(x, y + h * 0.27, tl[0], ha='center', va='center', fontsize=t_fs, fontweight='bold', color='#0f172a', zorder=4)
            ax.text(x, y,            tl[1], ha='center', va='center', fontsize=t_fs, fontweight='bold', color='#0f172a', zorder=4)
            ax.text(x, y - h * 0.27, tl[2], ha='center', va='center', fontsize=t_fs, fontweight='bold', color='#0f172a', zorder=4)

def draw_actor(ax, x, y, label="Automation\nEngineer", color='#b45309', bg='#fef3c7'):
    c = patches.Circle((x, y + 4.2), 2.0, facecolor=bg, edgecolor=color, linewidth=1.6, zorder=4)
    ax.add_patch(c)
    ax.plot([x, x], [y + 2.2, y - 2.2], color=color, lw=2.0, zorder=4)
    ax.plot([x - 2.8, x + 2.8], [y + 0.8, y + 0.8], color=color, lw=2.0, zorder=4)
    ax.plot([x, x - 2.4], [y - 2.2, y - 6.2], color=color, lw=2.0, zorder=4)
    ax.plot([x, x + 2.4], [y - 2.2, y - 6.2], color=color, lw=2.0, zorder=4)
    ax.text(x, y - 9.0, label, ha='center', va='center', fontsize=8.8, fontweight='bold', color='#0f172a', zorder=4)

# =============================================================================
# UML FORMAL NOTATION UTILITIES
# =============================================================================
def draw_uml_class(ax, x, y, w, h, class_name, stereotype="", attributes=None, operations=None, 
                   bg='#ffffff', border='#1e293b', t_fs=8.8, b_fs=7.2, header_bg=None, header_h=None):
    """Draws a formal UML class box with distinct compartments for name, attributes, and operations."""
    # Main outer rectangle
    rect = patches.Rectangle((x, y), w, h, facecolor=bg, edgecolor=border, linewidth=1.4, zorder=3)
    ax.add_patch(rect)
    
    # Calculate compartment heights
    has_ops = operations is not None and len(operations) > 0
    has_attrs = attributes is not None and len(attributes) > 0
    
    if header_h is None:
        header_h = max(0.22 * h, 5.2) if stereotype else max(0.18 * h, 4.0)
    if header_bg:
        h_rect = patches.Rectangle((x, y + h - header_h), w, header_h, facecolor=header_bg, edgecolor='none', zorder=3.5)
        ax.add_patch(h_rect)
    
    # Divider below header
    ax.plot([x, x + w], [y + h - header_h, y + h - header_h], color=border, lw=1.2, zorder=4)
    
    # Header text
    if stereotype:
        ax.text(x + w/2, y + h - header_h * 0.35, f"«{stereotype}»", ha='center', va='center', fontsize=t_fs*0.82, style='italic', color='#475569', zorder=5)
        ax.text(x + w/2, y + h - header_h * 0.72, class_name, ha='center', va='center', fontsize=t_fs, fontweight='bold', color='#0f172a', zorder=5)
    else:
        ax.text(x + w/2, y + h - header_h * 0.50, class_name, ha='center', va='center', fontsize=t_fs, fontweight='bold', color='#0f172a', zorder=5)
        
    rem_h = h - header_h
    n_attr = len(attributes) if has_attrs else 0
    n_ops = len(operations) if has_ops else 0
    
    if has_ops and has_attrs:
        total_items = n_attr + n_ops
        attr_h = rem_h * (n_attr / total_items)
        op_h = rem_h - attr_h
        ax.plot([x, x + w], [y + op_h, y + op_h], color=border, lw=1.0, zorder=4)
    elif has_ops:
        attr_h = 0
        op_h = rem_h
    else:
        attr_h = rem_h
        op_h = 0
        
    # Attributes
    if has_attrs:
        sp = attr_h / (len(attributes) + 1)
        for idx, attr in enumerate(attributes):
            ay = y + h - header_h - (idx + 1) * sp
            ax.text(x + 1.2, ay, attr, ha='left', va='center', fontsize=b_fs, color='#1e293b', zorder=5)
            
    # Operations
    if has_ops:
        sp_o = op_h / (len(operations) + 1)
        for idx, op in enumerate(operations):
            oy = y + op_h - (idx + 1) * sp_o
            ax.text(x + 1.2, oy, op, ha='left', va='center', fontsize=b_fs, color='#334155', style='italic', zorder=5)

def draw_uml_composition(ax, p_parent, p_child, mult_parent="1", mult_child="1..*", color='#1e293b', lw=1.4,
                         mult_parent_offset=(1.8, -1.8), mult_child_offset=(1.8, 1.8)):
    """Draws a formal UML composition line with solid black diamond at p_parent and multiplicity."""
    ax.plot([p_parent[0], p_child[0]], [p_parent[1], p_child[1]], color=color, lw=lw, zorder=3)
    
    # Diamond at parent end
    dx = p_child[0] - p_parent[0]
    dy = p_child[1] - p_parent[1]
    import numpy as np
    L = np.hypot(dx, dy)
    if L > 0:
        ux, uy = dx / L, dy / L
        vx, vy = -uy, ux
        d_len = 2.4
        d_w = 1.3
        pts = [
            (p_parent[0], p_parent[1]),
            (p_parent[0] + ux * d_len + vx * d_w, p_parent[1] + uy * d_len + vy * d_w),
            (p_parent[0] + ux * (2 * d_len), p_parent[1] + uy * (2 * d_len)),
            (p_parent[0] + ux * d_len - vx * d_w, p_parent[1] + uy * d_len - vy * d_w)
        ]
        poly = patches.Polygon(pts, closed=True, facecolor=color, edgecolor=color, zorder=6)
        ax.add_patch(poly)
        
    if mult_parent:
        ax.text(p_parent[0] + mult_parent_offset[0], p_parent[1] + mult_parent_offset[1],
                mult_parent, fontsize=7.2, fontweight='bold', color=color, zorder=6)
    if mult_child:
        ax.text(p_child[0] + mult_child_offset[0], p_child[1] + mult_child_offset[1],
                mult_child, fontsize=7.2, fontweight='bold', color=color, zorder=6)

def draw_uml_node(ax, x, y, w, h, name, stereotype="device", d=2.0, bg='#ffffff', border='#334155'):
    """Draws a formal 3D isometric UML Deployment Node."""
    # Front face
    front = patches.Rectangle((x, y), w - d, h - d, facecolor=bg, edgecolor=border, lw=1.3, zorder=2)
    ax.add_patch(front)
    # Top face
    pts_top = [(x, y + h - d), (x + d, y + h), (x + w, y + h), (x + w - d, y + h - d)]
    poly_top = patches.Polygon(pts_top, closed=True, facecolor='#e2e8f0', edgecolor=border, lw=1.2, zorder=2)
    ax.add_patch(poly_top)
    # Right face
    pts_right = [(x + w - d, y), (x + w, y + d), (x + w, y + h), (x + w - d, y + h - d)]
    poly_right = patches.Polygon(pts_right, closed=True, facecolor='#cbd5e1', edgecolor=border, lw=1.2, zorder=2)
    ax.add_patch(poly_right)
    # Text in header bar
    ax.text(x + 2.0, y + h - d - 1.8, f"«{stereotype}» {name}", ha='left', va='center', fontsize=8.0, fontweight='bold', color='#1e293b', zorder=4)

print("Updated thesis_art_utils with formal UML notation.")
