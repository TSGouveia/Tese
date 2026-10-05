# -*- coding: utf-8 -*-
"""
Chapter 5 Benchmark Plot Generator
Generates publication-quality vector PDF and PNG plots for Chapter 5 with comprehensive,
explicit internal legends positioned OUTSIDE the plotting area to avoid any occlusion.
"""
import os
import re
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import seaborn as sns

# ==============================================================================
# PUBLICATION TYPOGRAPHY CONFIGURATION (Matches NOVAthesis 11pt Body Text)
# ==============================================================================
sns.set_theme(style="whitegrid")
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
    'legend.fontsize': 9.2,
    'legend.frameon': True,
    'legend.facecolor': '#ffffff',
    'legend.edgecolor': '#cccccc',
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight'
})

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TESE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
RESULTADOS_DIR = os.path.join(TESE_DIR, "AAS Client", "Resultados")

OUT_DIRS = [
    os.path.abspath(os.path.join(SCRIPT_DIR, "..", "5-Figures")),
    os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "Documentos", "5-Figures")),
    os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "Documentos", "Figures")),
    os.path.abspath(os.path.join(SCRIPT_DIR, "..", "Figures"))
]
OUT_DIRS = [d for d in dict.fromkeys(OUT_DIRS) if os.path.isdir(d)]

def save_plot(fig, name):
    for d in OUT_DIRS:
        pdf_path = os.path.join(d, f"{name}.pdf")
        png_path = os.path.join(d, f"{name}.png")
        fig.savefig(pdf_path, bbox_inches='tight')
        fig.savefig(png_path, bbox_inches='tight', dpi=300)
    plt.close(fig)
    print(f"[OK] Generated: {name}.pdf and {name}.png in {len(OUT_DIRS)} directories")

# ==============================================================================
# DATA LOADERS
# ==============================================================================
def load_fms_data():
    fms_dir = os.path.join(RESULTADOS_DIR, "FMS")
    csv_files = glob.glob(os.path.join(fms_dir, "**", "*.csv"), recursive=True)
    runs = []
    ts_list = []
    
    for idx, f in enumerate(csv_files):
        try:
            df = pd.read_csv(f)
            if df.empty or 'Timestamp_s' not in df.columns:
                continue
            startup_time = df['StartupTime_s'].max()
            if startup_time <= 0:
                completed = df[df['IsStartupComplete'] == 1]
                startup_time = completed['Timestamp_s'].iloc[0] if not completed.empty else np.nan
                
            df_steady = df[df['IsStartupComplete'] == 1]
            if df_steady.empty:
                df_steady = df[df['Timestamp_s'] > startup_time]
            if df_steady.empty:
                df_steady = df.tail(len(df) // 2)
                
            runs.append({
                'Run': idx,
                'StartupTime_s': startup_time,
                'FPS_Mean': df_steady['FPS'].mean(),
                'FPS_Min': df_steady['FPS'].min(),
                'FPS_P01_Low': df_steady['FPS'].quantile(0.01),
                'FrameTime_Mean_ms': df_steady['FrameTime_ms'].mean(),
                'FrameTime_P95_ms': df_steady['FrameTime_ms'].quantile(0.95),
                'FrameTime_P99_ms': df_steady['FrameTime_ms'].quantile(0.99),
                'FrameTime_Std_ms': df_steady['FrameTime_ms'].std()
            })
            
            df_ts = df[['Timestamp_s', 'FPS', 'FrameTime_ms']].copy()
            df_ts['Time_bin'] = df_ts['Timestamp_s'].round(1)
            df_ts['Run'] = idx
            ts_list.append(df_ts)
        except Exception:
            continue
            
    df_runs = pd.DataFrame(runs)
    df_ts = pd.concat(ts_list, ignore_index=True) if ts_list else pd.DataFrame()
    return df_runs, df_ts

def extract_conveyor_count(folder_name):
    match = re.search(r'(\d+)', folder_name)
    return int(match.group(1)) if match else None

def load_stress_data():
    subdirs = [d for d in os.listdir(RESULTADOS_DIR) if os.path.isdir(os.path.join(RESULTADOS_DIR, d))]
    conv_folders = []
    for d in subdirs:
        if d.lower().startswith(('.', 'aasx', 'output', 'graficos', 'charts', 'fms')):
            continue
        c = extract_conveyor_count(d)
        if c is not None:
            conv_folders.append((c, d))
    conv_folders.sort(key=lambda x: x[0])
    
    runs = []
    ts_list = []
    
    for count, folder_name in conv_folders:
        folder_path = os.path.join(RESULTADOS_DIR, folder_name)
        csv_files = glob.glob(os.path.join(folder_path, "**", "*.csv"), recursive=True)
        if count == 5 and len(csv_files) > 100:
            csv_files = sorted(csv_files, key=os.path.getmtime, reverse=True)[:100]
            
        for run_idx, f in enumerate(csv_files):
            try:
                df = pd.read_csv(f)
                if df.empty or 'Timestamp_s' not in df.columns:
                    continue
                startup_time = df['StartupTime_s'].max()
                if startup_time <= 0:
                    completed = df[df['IsStartupComplete'] == 1]
                    startup_time = completed['Timestamp_s'].iloc[0] if not completed.empty else np.nan
                    
                df_startup = df[df['IsStartupComplete'] == 0]
                df_steady = df[df['IsStartupComplete'] == 1]
                if df_steady.empty:
                    df_steady = df
                    
                runs.append({
                    'Conveyors': count,
                    'Run': run_idx,
                    'StartupTime_s': startup_time,
                    'FPS_Mean': df_steady['FPS'].mean(),
                    'FPS_Min': df_steady['FPS'].min(),
                    'FPS_P01_Low': df_steady['FPS'].quantile(0.01),
                    'FrameTime_Mean_ms': df_steady['FrameTime_ms'].mean(),
                    'FrameTime_P95_ms': df_steady['FrameTime_ms'].quantile(0.95),
                    'FrameTime_P99_ms': df_steady['FrameTime_ms'].quantile(0.99),
                    'FrameTime_Std_ms': df_steady['FrameTime_ms'].std(),
                    'Startup_per_Conveyor_ms': (startup_time / count) * 1000.0,
                    'FrameTime_per_Conveyor_us': (df_steady['FrameTime_ms'].mean() / count) * 1000.0
                })
                
                df_ts = df[['Timestamp_s', 'FPS', 'FrameTime_ms']].copy()
                df_ts['Time_bin'] = df_ts['Timestamp_s'].round(0)
                df_ts['Conveyors'] = count
                ts_list.append(df_ts)
            except Exception:
                continue
                
    return pd.DataFrame(runs), pd.concat(ts_list, ignore_index=True) if ts_list else pd.DataFrame()

# ==============================================================================
# PLOT 1: fms_metrics_distributions
# ==============================================================================
def plot_fms_metrics_distributions(df_fms):
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 5.0))
    
    st_m = df_fms['StartupTime_s'].mean()
    st_s = df_fms['StartupTime_s'].std()
    
    # Subplot 1: Startup Time
    bp1 = sns.boxplot(y=df_fms['StartupTime_s'], ax=axes[0], color='#2b5c8f', width=0.30, showmeans=True,
                      meanprops={'marker':'o', 'markerfacecolor':'red', 'markeredgecolor':'black', 'markersize':8})
    axes[0].set_title('Startup Initialization Time', pad=38, fontweight='bold')
    axes[0].set_ylabel('Startup Time (seconds)', fontweight='bold')
    
    leg1_elements = [
        mpatches.Patch(facecolor='#2b5c8f', edgecolor='#222222', label='IQR (25th–75th)'),
        Line2D([0], [0], color='black', linewidth=1.5, label='Median'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markeredgecolor='black', markersize=7, label=f'Mean ({st_m:.2f}s ± {st_s:.2f}s)'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='w', markeredgecolor='#777777', markersize=6, label='Outliers')
    ]
    axes[0].legend(handles=leg1_elements, loc='lower center', bbox_to_anchor=(0.5, 1.01), ncol=2, fontsize=8.2, framealpha=0.95)
    
    # Subplot 2: Steady-State FPS
    fps_m = df_fms['FPS_Mean'].mean()
    fps_s = df_fms['FPS_Mean'].std()
    bp2 = sns.boxplot(y=df_fms['FPS_Mean'], ax=axes[1], color='#27ae60', width=0.30, showmeans=True,
                      meanprops={'marker':'o', 'markerfacecolor':'red', 'markeredgecolor':'black', 'markersize':8})
    axes[1].axhline(60, color='#c0392b', linestyle='--', linewidth=1.8)
    axes[1].set_title('Steady-State Rendering Rate', pad=38, fontweight='bold')
    axes[1].set_ylabel('Frames per Second (FPS)', fontweight='bold')
    
    leg2_elements = [
        mpatches.Patch(facecolor='#27ae60', edgecolor='#222222', label='IQR (25th–75th)'),
        Line2D([0], [0], color='black', linewidth=1.5, label='Median'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='red', markeredgecolor='black', markersize=7, label=f'Mean ({fps_m:.1f} ± {fps_s:.1f} FPS)'),
        Line2D([0], [0], color='#c0392b', linestyle='--', linewidth=1.8, label='60 FPS Target (16.7 ms)')
    ]
    axes[1].legend(handles=leg2_elements, loc='lower center', bbox_to_anchor=(0.5, 1.01), ncol=2, fontsize=8.2, framealpha=0.95)
    
    plt.tight_layout()
    save_plot(fig, "fms_metrics_distributions")

# ==============================================================================
# PLOT 2: fms_timeseries_evolution (Legend outside on top)
# ==============================================================================
def plot_fms_timeseries_evolution(df_fms_runs, df_fms_ts):
    st_m = df_fms_runs['StartupTime_s'].mean()
    
    ts_agg = df_fms_ts.groupby('Time_bin').agg({
        'FPS': ['mean', 'std'],
        'FrameTime_ms': ['mean', 'std']
    }).reset_index()
    ts_agg.columns = ['Time_bin', 'FPS_mean', 'FPS_std', 'FT_mean', 'FT_std']
    ts_agg = ts_agg[ts_agg['Time_bin'] <= 7.5]
    
    fig, ax1 = plt.subplots(figsize=(10.0, 5.0))
    
    # Left Axis: FPS (Green)
    c_fps = '#27ae60'
    ax1.set_xlabel('Elapsed Simulation Time (s)', fontweight='bold')
    ax1.set_ylabel('Mean Rendering Rate (FPS)', color=c_fps, fontweight='bold')
    line_fps = ax1.plot(ts_agg['Time_bin'], ts_agg['FPS_mean'], color=c_fps, linewidth=2.2, label='Mean Steady-State FPS')
    band_fps = ax1.fill_between(ts_agg['Time_bin'], 
                                ts_agg['FPS_mean'] - ts_agg['FPS_std'], 
                                ts_agg['FPS_mean'] + ts_agg['FPS_std'], 
                                color=c_fps, alpha=0.22, label='±1 Std Dev Band')
    ax1.tick_params(axis='y', labelcolor=c_fps)
    
    # Vertical Boundary Line
    line_boundary = ax1.axvline(st_m, color='#2980b9', linestyle=':', linewidth=2.2, 
                                label=f'Startup Boundary (t = {st_m:.2f}s)')
    
    # Right Axis: Frame Time (Orange)
    ax2 = ax1.twinx()
    c_ft = '#d35400'
    ax2.set_ylabel('Frame Latency (ms)', color=c_ft, fontweight='bold')
    line_ft = ax2.plot(ts_agg['Time_bin'], ts_agg['FT_mean'], color=c_ft, linewidth=2.0, linestyle='--', 
                       label='Frame Render Latency (ms)')
    ax2.tick_params(axis='y', labelcolor=c_ft)
    ax2.grid(False)
    
    # Combined Unified Legend OUTSIDE ON TOP (Single row, 4 columns)
    handles = [
        line_fps[0],
        mpatches.Patch(facecolor=c_fps, alpha=0.3, label='±1 Std Dev Band'),
        line_ft[0],
        line_boundary
    ]
    ax1.legend(handles=handles, loc='lower center', bbox_to_anchor=(0.5, 1.02), ncol=4, framealpha=0.95, fontsize=8.5)
    
    ax1.set_title('Dynamic Execution Timeline of the Physical FMS Pilot Bench', pad=32)
    plt.tight_layout()
    save_plot(fig, "fms_timeseries_evolution")

# ==============================================================================
# PLOT 3: eval_startup_complexity (Legend outside on top)
# ==============================================================================
def plot_eval_startup_complexity(df_runs):
    stats = df_runs.groupby('Conveyors').agg({
        'StartupTime_s': ['mean', 'std'],
        'Startup_per_Conveyor_ms': ['mean', 'std']
    }).reset_index()
    stats.columns = ['Conveyors', 'Startup_Mean', 'Startup_Std', 'UnitCost_Mean', 'UnitCost_Std']
    
    fig, ax1 = plt.subplots(figsize=(9.6, 4.8))
    
    # Left Axis: Total Startup Time (Blue)
    c_total = '#1f77b4'
    ax1.set_xlabel('Number of Conveyor Modules (Scale N)', fontweight='bold')
    ax1.set_ylabel('Total Startup Time (s)', color=c_total, fontweight='bold')
    line_total = ax1.plot(stats['Conveyors'], stats['Startup_Mean'], marker='o', markersize=7,
                          color=c_total, linewidth=2.2, label='Total Startup Time (s) [Left Axis]')
    ax1.tick_params(axis='y', labelcolor=c_total)
    
    # Right Axis: Unit Cost per Conveyor (Orange)
    ax2 = ax1.twinx()
    c_unit = '#ff7f0e'
    ax2.set_ylabel('Unit Instantiation Cost (ms / conveyor)', color=c_unit, fontweight='bold')
    line_unit = ax2.plot(stats['Conveyors'], stats['UnitCost_Mean'], marker='s', markersize=7,
                         color=c_unit, linewidth=2.2, linestyle='--', label='Unit Instantiation Cost (ms/conveyor) [Right Axis]')
    ax2.tick_params(axis='y', labelcolor=c_unit)
    ax2.grid(False)
    
    # Combined Unified Legend OUTSIDE ON TOP
    handles = [line_total[0], line_unit[0]]
    labels = [h.get_label() for h in handles]
    ax1.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, 1.02), ncol=2, framealpha=0.95, fontsize=9.2)
    
    ax1.set_title('Startup Scalability: Total Initialization Time vs. Unit Instantiation Cost', pad=34)
    plt.tight_layout()
    save_plot(fig, "eval_startup_complexity")

# ==============================================================================
# PLOT 4: eval_fps_degradation (Legend outside to the right)
# ==============================================================================
def plot_eval_fps_degradation(df_runs):
    stats = df_runs.groupby('Conveyors').agg({
        'FPS_Mean': ['mean', 'std'],
        'FPS_P01_Low': ['mean', 'std']
    }).reset_index()
    stats.columns = ['Conveyors', 'FPS_Mean_m', 'FPS_Mean_s', 'FPS_Low_m', 'FPS_Low_s']
    
    fig, ax = plt.subplots(figsize=(10.6, 4.8))
    
    # Mean FPS
    c_mean = '#2ca02c'
    l1 = ax.plot(stats['Conveyors'], stats['FPS_Mean_m'], marker='o', markersize=7,
                 color=c_mean, linewidth=2.4, label='Mean Steady-State FPS')
    b1 = ax.fill_between(stats['Conveyors'], 
                         stats['FPS_Mean_m'] - stats['FPS_Mean_s'], 
                         stats['FPS_Mean_m'] + stats['FPS_Mean_s'], 
                         color=c_mean, alpha=0.25, label='±1 Std Dev Band')
    
    # 1% Low FPS
    c_low = '#d62728'
    l2 = ax.plot(stats['Conveyors'], stats['FPS_Low_m'], marker='^', markersize=7,
                 color=c_low, linewidth=2.2, linestyle='--', label='1% Low FPS (Transient Drops)')
    
    # Thresholds
    t60 = ax.axhline(60, color='#3b82f6', linestyle='--', linewidth=1.8, label='60 FPS Target (16.7 ms)')
    t30 = ax.axhline(30, color='#ef4444', linestyle='--', linewidth=1.8, label='30 FPS Threshold (33.3 ms)')
    
    ax.set_xlabel('Number of Conveyor Modules (Scale N)', fontweight='bold')
    ax.set_ylabel('Frames per Second (FPS)', fontweight='bold')
    ax.set_title('Rendering Fluidity: Mean FPS Degradation and 1% Low FPS', pad=12)
    
    # Legend placed OUTSIDE TO THE RIGHT
    handles = [l1[0], mpatches.Patch(facecolor=c_mean, alpha=0.3, label='±1 Std Dev Band'), l2[0], t60, t30]
    ax.legend(handles=handles, loc='center left', bbox_to_anchor=(1.02, 0.5), framealpha=0.95, fontsize=9.2)
    
    plt.tight_layout()
    save_plot(fig, "eval_fps_degradation")

# ==============================================================================
# PLOT 5: eval_unit_frame_cost (Legend outside on top)
# ==============================================================================
def plot_eval_unit_frame_cost(df_runs):
    fig, ax = plt.subplots(figsize=(9.6, 4.8))
    
    conv_order = sorted(df_runs['Conveyors'].unique())
    sns.barplot(data=df_runs, x='Conveyors', y='FrameTime_per_Conveyor_us', order=conv_order,
                hue='Conveyors', legend=False, palette='viridis', ax=ax, errorbar='sd', capsize=0.15, 
                edgecolor='#222222', linewidth=0.8)
    
    ax.set_xlabel('Number of Conveyor Modules (Scale N)', fontweight='bold')
    ax.set_ylabel('Unit Frame Processing Cost (µs / conveyor)', fontweight='bold')
    ax.set_title('Unit Computational Frame Cost per Conveyor Module', pad=34)
    
    # Add a clear legend placed OUTSIDE ON TOP
    legend_elements = [
        mpatches.Patch(facecolor='#440154', edgecolor='#222222', label='Mean Unit Frame Cost (µs/conveyor)'),
        Line2D([0], [0], color='#222222', linewidth=1.8, marker='_', markersize=10, label='±1 Standard Deviation (Error Bar)')
    ]
    ax.legend(handles=legend_elements, loc='lower center', bbox_to_anchor=(0.5, 1.02), ncol=2, framealpha=0.95, fontsize=9.2)
    
    plt.tight_layout()
    save_plot(fig, "eval_unit_frame_cost")

# ==============================================================================
# PLOT 6: eval_timeseries_fps (Legend outside to the right)
# ==============================================================================
def plot_eval_timeseries_fps(df_runs, df_ts):
    conveyors_order = sorted(df_runs['Conveyors'].unique())
    colors = sns.color_palette("tab10", len(conveyors_order))
    
    df_ts_filt = df_ts[df_ts['Time_bin'] <= 65]
    ts_mean = df_ts_filt.groupby(['Conveyors', 'Time_bin'])[['FPS']].mean().reset_index()
    
    fig, ax = plt.subplots(figsize=(10.6, 5.0))
    
    # Plot each conveyor curve
    lines = []
    for idx, c in enumerate(conveyors_order):
        sub = ts_mean[ts_mean['Conveyors'] == c]
        l = ax.plot(sub['Time_bin'], sub['FPS'], label=f"{c} conveyors", linewidth=2.0, color=colors[idx % len(colors)])
        lines.append(l[0])
        
    # Reference thresholds
    t60 = ax.axhline(60, color='#666666', linestyle=':', linewidth=1.8, label='60 FPS Target')
    t30 = ax.axhline(30, color='#999999', linestyle='--', linewidth=1.8, label='30 FPS Threshold')
    
    ax.set_xlabel('Elapsed Simulation Time (s)', fontweight='bold')
    ax.set_ylabel('Mean Rendering Rate (FPS)', fontweight='bold')
    ax.set_title('Mean FPS Evolution Over Simulation Time Across Module Counts', pad=12)
    
    # Legend placed OUTSIDE TO THE RIGHT
    handles = lines + [t60, t30]
    ax.legend(handles=handles, title='Scale & Thresholds', loc='center left', bbox_to_anchor=(1.02, 0.5), framealpha=0.95, fontsize=8.8)
    
    plt.tight_layout()
    save_plot(fig, "eval_timeseries_fps")

# ==============================================================================
# PLOT 7: eval_correlation_matrix
# ==============================================================================
def plot_eval_correlation_matrix(df_runs):
    fig, ax = plt.subplots(figsize=(8.8, 6.6))
    
    corr_cols = ['Conveyors', 'StartupTime_s', 'FPS_Mean', 'FPS_P01_Low', 'FrameTime_Mean_ms', 'FrameTime_P95_ms']
    corr_labels = ['Conveyors', 'Startup Time', 'Mean FPS', '1% Low FPS', 'Mean Frame Time', 'Frame Time P95']
    
    df_corr = df_runs[corr_cols].copy()
    df_corr.columns = corr_labels
    corr = df_corr.corr()
    
    sns.heatmap(corr, annot=True, fmt=".2f", cmap='vlag', vmin=-1, vmax=1,
                linewidths=1.0, linecolor='#ffffff', square=True, ax=ax,
                cbar_kws={'label': 'Pearson Correlation Coefficient (r)', 'shrink': 0.85})
    
    ax.set_title('Linear Correlation Matrix of Scalability Metrics', pad=15)
    plt.tight_layout()
    save_plot(fig, "eval_correlation_matrix")

# ==============================================================================
# MAIN
# ==============================================================================
def main():
    print("================================================================")
    print("  GENERATING CHAPTER 5 BENCHMARK PLOTS WITH EXTERNAL LEGENDS    ")
    print("================================================================")
    
    print("\n[1/3] Loading FMS Pilot Bench Data...")
    df_fms_runs, df_fms_ts = load_fms_data()
    print(f"Loaded {len(df_fms_runs)} FMS runs.")
    
    print("\n[2/3] Loading Parametric Scalability Stress Data...")
    df_stress_runs, df_stress_ts = load_stress_data()
    print(f"Loaded {len(df_stress_runs)} stress test runs.")
    
    print("\n[3/3] Rendering and Exporting Figures...")
    plot_fms_metrics_distributions(df_fms_runs)
    plot_fms_timeseries_evolution(df_fms_runs, df_fms_ts)
    plot_eval_startup_complexity(df_stress_runs)
    plot_eval_fps_degradation(df_stress_runs)
    plot_eval_unit_frame_cost(df_stress_runs)
    plot_eval_timeseries_fps(df_stress_runs, df_stress_ts)
    plot_eval_correlation_matrix(df_stress_runs)
    
    print("\n================================================================")
    print("  ALL CHAPTER 5 PLOTS SUCCESSFULLY REGENERATED!                 ")
    print("================================================================")

if __name__ == '__main__':
    main()
