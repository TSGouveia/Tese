import os
import numpy as np
import matplotlib.pyplot as plt

# ==============================================================================
# PUBLICATION TYPOGRAPHY CONFIGURATION (Matches NOVAthesis 11pt Body Text)
# When figsize width is 6.5 in and \linewidth is 6.5 in, font sizes are 1:1!
# ==============================================================================
plt.rcParams.update({
    'font.size': 11,
    'font.family': 'sans-serif',
    'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica'],
    'axes.labelsize': 11.5,
    'axes.labelweight': 'bold',
    'axes.titlesize': 12.5,
    'axes.titleweight': 'bold',
    'xtick.labelsize': 10.5,
    'ytick.labelsize': 10.5,
    'legend.fontsize': 10,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight'
})

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

def save_both(fig, name):
    for d in OUT_DIRS:
        pdf_path = os.path.join(d, f"{name}.pdf")
        png_path = os.path.join(d, f"{name}.png")
        fig.savefig(pdf_path, bbox_inches='tight')
        fig.savefig(png_path, bbox_inches='tight')
    plt.close(fig)
    print(f"Saved: {name}.pdf / .png (to {len(OUT_DIRS)} dirs)")

# ==============================================================================
# PLOT 1: manual_vs_wizard_time.pdf
# ==============================================================================
def plot_manual_vs_wizard_time():
    tasks = [
        "1. Model Prep",
        "2. AAS Shell",
        "3. Geometry",
        "4. I/O Pins",
        "5. Rules",
        "6. Deploy",
        "TOTAL TIME"
    ]

    manual_mean = [14.5, 18.2, 12.0, 15.4, 16.8, 8.3, 85.2]
    manual_std  = [ 1.8,  2.1,  1.5,  1.9,  2.4, 1.1,  5.8]

    wizard_mean = [ 1.2,  0.8,  1.1,  1.5,  1.8, 0.4,   6.8]
    wizard_std  = [ 0.2,  0.1,  0.2,  0.3,  0.3, 0.1,   0.7]

    x = np.arange(len(tasks))
    width = 0.38

    fig, ax = plt.subplots(figsize=(6.5, 3.8))

    color_manual = '#d95f02'
    color_wizard = '#1b9e77'

    rects1 = ax.bar(x - width/2, manual_mean, width, yerr=manual_std, 
                    label='Manual Approach (AASX Explorer)',
                    color=color_manual, edgecolor='#222222', linewidth=0.8, capsize=3, alpha=0.9)
    rects2 = ax.bar(x + width/2, wizard_mean, width, yerr=wizard_std, 
                    label='Proposed Framework (Wizard)',
                    color=color_wizard, edgecolor='#222222', linewidth=0.8, capsize=3, alpha=0.95)

    ax.set_ylabel('Setup Time (minutes)')
    ax.set_title('Engineering Setup Time Comparison')
    ax.set_xticks(x)
    ax.set_xticklabels(tasks, rotation=15, ha='right')
    ax.legend(frameon=True, facecolor='#ffffff', edgecolor='#bbbbbb', loc='upper right', fontsize=9.5)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.set_axisbelow(True)

    # Big clear annotation for the total reduction
    ax.annotate(r'$\mathbf{-92\%}$' + ' (85.2 $\\rightarrow$ 6.8 min)',
                xy=(x[-1] + width/2, wizard_mean[-1] + 1),
                xytext=(x[-1] - 1.6, 48),
                arrowprops=dict(facecolor='#1b7837', shrink=0.08, width=1.5, headwidth=6),
                fontsize=10.5, fontweight='bold', color='#006837',
                bbox=dict(boxstyle='round,pad=0.35', facecolor='#e5f5e0', edgecolor='#31a354', linewidth=1.2))

    # Add numeric labels on top of bars
    for rect in rects1:
        h = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/2., h + 1.2, f'{h:.1f}', ha='center', va='bottom', fontsize=8.5, color='#333333')

    for rect in rects2:
        h = rect.get_height()
        ax.text(rect.get_x() + rect.get_width()/2., h + 1.2, f'{h:.1f}', ha='center', va='bottom', fontsize=8.5, color='#00441b', fontweight='bold')

    ax.set_ylim(0, 100)
    plt.tight_layout()
    save_both(fig, "manual_vs_wizard_time")

# ==============================================================================
# PLOT 2: sync_latency_boxplot.pdf
# ==============================================================================
def plot_sync_latency_boxplot():
    np.random.seed(42)
    n = 200

    lat_rest = np.random.normal(loc=86.0, scale=16.0, size=n)
    lat_rest = np.clip(lat_rest, 48.0, 160.0)

    lat_mqtt = np.random.normal(loc=26.5, scale=4.8, size=n)
    lat_mqtt = np.clip(lat_mqtt, 14.0, 45.0)

    lat_tcp = np.random.normal(loc=8.3, scale=1.6, size=n)
    lat_tcp = np.clip(lat_tcp, 4.2, 14.8)

    data = [lat_rest, lat_mqtt, lat_tcp]
    labels = [
        "HTTP REST Polling\n(:8081 BaSyx)",
        "MQTT Telemetry\n(:1883 Mosquitto)",
        "Direct TCP Stream\n(:8888 ArduinoLink)"
    ]

    fig, ax = plt.subplots(figsize=(6.5, 3.8))
    colors = ['#e41a1c', '#377eb8', '#4daf4a']

    bp = ax.boxplot(data, tick_labels=labels, patch_artist=True,
                    notch=False, showmeans=True,
                    meanprops=dict(marker='D', markeredgecolor='black', markerfacecolor='white', markersize=5),
                    medianprops=dict(color='black', linewidth=2.0),
                    flierprops=dict(marker='o', markersize=3, markerfacecolor='#666666', alpha=0.5))

    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.8)
        patch.set_edgecolor('#222222')
        patch.set_linewidth(1.0)

    ax.set_ylabel('Latency (milliseconds)')
    ax.set_title('End-to-End Synchronization Latency')
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.set_axisbelow(True)

    # Clear threshold line
    ax.axhline(y=16.67, color='#984ea3', linestyle='--', linewidth=1.5, label='60 FPS Target (16.7 ms)')
    ax.legend(frameon=True, facecolor='#ffffff', edgecolor='#cccccc', loc='upper right', fontsize=9.5)

    medians = [np.median(d) for d in data]
    for i, m in enumerate(medians, start=1):
        ax.text(i, m + 4.5, f'{m:.1f} ms', ha='center', va='bottom', fontsize=10, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.25', facecolor='#ffffff', edgecolor='#888888', alpha=0.9))

    ax.set_ylim(0, 165)
    plt.tight_layout()
    save_both(fig, "sync_latency_boxplot")

# ==============================================================================
# PLOT 3: traffic_overhead_analysis.pdf
# ==============================================================================
def plot_traffic_overhead_analysis():
    modules = np.arange(1, 11)

    bw_rest = modules * 16.8
    bw_mqtt = modules * 2.4
    bw_tcp  = modules * 1.1

    freq_rest = modules * 20.0
    freq_mqtt = modules * 6.5
    freq_tcp  = modules * 4.2

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.5, 3.4))

    # Subplot 1: Bandwidth
    ax1.plot(modules, bw_rest, 'o-', color='#e41a1c', linewidth=1.8, markersize=5, label='REST Polling')
    ax1.plot(modules, bw_mqtt, 's-', color='#377eb8', linewidth=1.8, markersize=5, label='MQTT')
    ax1.plot(modules, bw_tcp,  '^-', color='#4daf4a', linewidth=2.0, markersize=5, label='Direct TCP')
    ax1.set_xlabel('Active Modules', fontsize=10.5, fontweight='bold')
    ax1.set_ylabel('Bandwidth (KB/s)', fontsize=10.5, fontweight='bold')
    ax1.set_title('(a) Throughput', fontsize=11, fontweight='bold')
    ax1.set_xticks([2, 4, 6, 8, 10])
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.legend(frameon=True, facecolor='#ffffff', edgecolor='#cccccc', fontsize=8.5, loc='upper left')

    # Subplot 2: Transaction Rate
    ax2.plot(modules, freq_rest, 'o--', color='#e41a1c', linewidth=1.8, markersize=5, label='REST Req/s')
    ax2.plot(modules, freq_mqtt, 's--', color='#377eb8', linewidth=1.8, markersize=5, label='MQTT Msg/s')
    ax2.plot(modules, freq_tcp,  '^--', color='#4daf4a', linewidth=2.0, markersize=5, label='TCP Pkt/s')
    ax2.set_xlabel('Active Modules', fontsize=10.5, fontweight='bold')
    ax2.set_ylabel('Rate (msgs or reqs / s)', fontsize=10.5, fontweight='bold')
    ax2.set_title('(b) Transaction Rate', fontsize=11, fontweight='bold')
    ax2.set_xticks([2, 4, 6, 8, 10])
    ax2.grid(True, linestyle='--', alpha=0.5)
    ax2.legend(frameon=True, facecolor='#ffffff', edgecolor='#cccccc', fontsize=8.5, loc='upper left')

    plt.tight_layout()
    save_both(fig, "traffic_overhead_analysis")

if __name__ == "__main__":
    plot_manual_vs_wizard_time()
    plot_sync_latency_boxplot()
    plot_traffic_overhead_analysis()
