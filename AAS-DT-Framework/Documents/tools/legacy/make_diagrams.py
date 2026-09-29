# -*- coding: utf-8 -*-
"""
Thesis Diagram Generator
Generates clean, ultra-readable, publication-grade vector PDF/PNG diagrams for the MSc Thesis.
"""
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

def draw_group(ax, x, y, w, h, label, bg, border, fs=11, lw=1.8, header_pos='top-left'):
    rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.5,rounding_size=1.2",
                                  facecolor=bg, edgecolor=border, linewidth=lw, zorder=1)
    ax.add_patch(rect)
    if label:
        if header_pos == 'top-left':
            ax.text(x + 1.8, y + h - 2.5, label, ha='left', va='center', fontsize=fs, fontweight='bold', color=border, zorder=2)
        elif header_pos == 'top-center':
            ax.text(x + w/2, y + h - 2.5, label, ha='center', va='center', fontsize=fs, fontweight='bold', color=border, zorder=2)

def draw_card(ax, x, y, w, h, title, lines=None, bg='#ffffff', border='#3b82f6', t_fs=10, b_fs=8.5, lw=1.4, align='center'):
    rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.0",
                                  facecolor=bg, edgecolor=border, linewidth=lw, zorder=3)
    ax.add_patch(rect)
    
    if not lines:
        ax.text(x + w/2, y + h/2, title, ha='center', va='center', fontsize=t_fs, fontweight='bold', color='#0f172a', zorder=4)
        return

    if align == 'center':
        ax.text(x + w/2, y + h - 2.8, title, ha='center', va='center', fontsize=t_fs, fontweight='bold', color='#0f172a', zorder=4)
        n = len(lines)
        avail_h = h - 4.5
        spacing = avail_h / max(n, 1)
        for i, line in enumerate(lines):
            ly = y + h - 4.5 - (i + 0.5) * spacing
            ax.text(x + w/2, ly, line, ha='center', va='center', fontsize=b_fs, color='#334155', zorder=4)
    else:
        ax.text(x + 1.8, y + h - 2.6, title, ha='left', va='center', fontsize=t_fs, fontweight='bold', color='#0f172a', zorder=4)
        n = len(lines)
        avail_h = h - 4.2
        spacing = avail_h / max(n, 1)
        for i, line in enumerate(lines):
            ly = y + h - 4.2 - (i + 0.5) * spacing
            ax.text(x + 1.8, ly, line, ha='left', va='center', fontsize=b_fs, color='#334155', zorder=4)

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

print("Base utilities defined.")
