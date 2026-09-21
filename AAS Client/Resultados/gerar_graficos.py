import os
import re
import glob
import argparse
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Estilo visual moderno e limpo para artigos/tese
sns.set_theme(style="whitegrid", palette="deep")
plt.rcParams.update({
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.titlesize': 14,
    'figure.dpi': 300
})

def extract_conveyor_count(folder_name):
    """Extrai o número de conveyors a partir do nome da pasta (ex: '50 conveyors' -> 50)."""
    match = re.search(r'(\d+)', folder_name)
    return int(match.group(1)) if match else None

def get_conveyor_folders(base_dir):
    """Descobre e ordena as pastas de testes por número de conveyors, ignorando pastas irrelevantes."""
    subdirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    
    conveyor_folders = []
    for d in subdirs:
        if d.lower().startswith(('.', 'aasx', 'output', 'graficos', 'charts')):
            continue
        count = extract_conveyor_count(d)
        if count is not None:
            conveyor_folders.append((count, d))
            
    conveyor_folders.sort(key=lambda x: x[0])
    return conveyor_folders

def load_data(base_dir):
    """
    Lê todos os ficheiros CSV de cada pasta de teste e calcula métricas ricas por execução
    e agrega séries temporais.
    """
    conveyor_folders = get_conveyor_folders(base_dir)
    print(f"Pastas detetadas: {[d for _, d in conveyor_folders]}")

    runs_data = []
    timeseries_data = []

    for count, folder_name in conveyor_folders:
        folder_path = os.path.join(base_dir, folder_name)
        csv_files = glob.glob(os.path.join(folder_path, "**", "*.csv"), recursive=True)
        
        if count == 5 and len(csv_files) > 100:
            csv_files = sorted(csv_files, key=os.path.getmtime, reverse=True)[:100]

        print(f"Processando '{folder_name}' ({count} conveyors) - {len(csv_files)} ficheiros CSV...")

        for run_idx, filepath in enumerate(csv_files):
            try:
                df = pd.read_csv(filepath)
                if df.empty or 'Timestamp_s' not in df.columns:
                    continue

                # Startup Time
                startup_time = df['StartupTime_s'].max()
                if startup_time <= 0:
                    completed = df[df['IsStartupComplete'] == 1]
                    if not completed.empty:
                        startup_time = completed['Timestamp_s'].iloc[0]
                    else:
                        startup_time = np.nan

                # Separação de fases: Startup vs Regime Estacionário
                df_startup = df[df['IsStartupComplete'] == 0]
                df_steady = df[df['IsStartupComplete'] == 1]
                if df_steady.empty:
                    df_steady = df

                # Métricas de FPS
                fps_mean = df_steady['FPS'].mean()
                fps_median = df_steady['FPS'].median()
                fps_min = df_steady['FPS'].min()
                fps_max = df_steady['FPS'].max()
                fps_std = df_steady['FPS'].std()
                fps_p01 = df_steady['FPS'].quantile(0.01) # 1% low (micro-stuttering)
                fps_p05 = df_steady['FPS'].quantile(0.05)

                # Métricas de Frame Time
                frametime_mean = df_steady['FrameTime_ms'].mean()
                frametime_median = df_steady['FrameTime_ms'].median()
                frametime_max = df_steady['FrameTime_ms'].max()
                frametime_std = df_steady['FrameTime_ms'].std()
                frametime_p95 = df_steady['FrameTime_ms'].quantile(0.95)
                frametime_p99 = df_steady['FrameTime_ms'].quantile(0.99) # 99th percentile

                # Frame drops / drops de fluidez
                pct_frames_below_60 = (df_steady['FPS'] < 59.0).mean() * 100.0
                pct_frames_below_30 = (df_steady['FPS'] < 29.0).mean() * 100.0

                # RAM
                ram_alloc_max = df['RAM_Allocated_MB'].max()
                ram_alloc_mean = df_steady['RAM_Allocated_MB'].mean()
                ram_res_max = df['RAM_TotalReserved_MB'].max()
                ram_res_mean = df_steady['RAM_TotalReserved_MB'].mean()
                ram_unallocated = ram_res_max - ram_alloc_max

                # Startup vs Steady FPS ratio / gap
                fps_startup_mean = df_startup['FPS'].mean() if not df_startup.empty else np.nan

                # Produtos Ativos
                active_prod_max = df['ActiveProducts'].max() if 'ActiveProducts' in df.columns else np.nan
                active_prod_mean = df_steady['ActiveProducts'].mean() if 'ActiveProducts' in df.columns else np.nan

                # Duração total da execução
                duration_s = df['Timestamp_s'].max() - df['Timestamp_s'].min()

                runs_data.append({
                    'Conveyors': count,
                    'FolderName': folder_name,
                    'RunFile': os.path.basename(filepath),
                    'StartupTime_s': startup_time,
                    'FPS_Mean': fps_mean,
                    'FPS_Median': fps_median,
                    'FPS_Min': fps_min,
                    'FPS_Max': fps_max,
                    'FPS_Std': fps_std,
                    'FPS_P01_Low': fps_p01,
                    'FPS_P05_Low': fps_p05,
                    'FPS_Startup_Mean': fps_startup_mean,
                    'FrameTime_Mean_ms': frametime_mean,
                    'FrameTime_Median_ms': frametime_median,
                    'FrameTime_Max_ms': frametime_max,
                    'FrameTime_Std_ms': frametime_std,
                    'FrameTime_P95_ms': frametime_p95,
                    'FrameTime_P99_ms': frametime_p99,
                    'Pct_Frames_Below_60': pct_frames_below_60,
                    'Pct_Frames_Below_30': pct_frames_below_30,
                    'RAM_Alloc_Max_MB': ram_alloc_max,
                    'RAM_Alloc_Mean_MB': ram_alloc_mean,
                    'RAM_Reserved_Max_MB': ram_res_max,
                    'RAM_Reserved_Mean_MB': ram_res_mean,
                    'RAM_Unallocated_Max_MB': ram_unallocated,
                    'ActiveProducts_Max': active_prod_max,
                    'ActiveProducts_Mean': active_prod_mean,
                    'Duration_s': duration_s
                })

                # Para time series: bin a cada 1s
                df_ts = df[['Timestamp_s', 'FPS', 'FrameTime_ms', 'RAM_Allocated_MB', 'RAM_TotalReserved_MB']].copy()
                df_ts['Time_bin'] = df_ts['Timestamp_s'].round(0)
                df_ts['Conveyors'] = count
                df_ts['Run'] = run_idx
                timeseries_data.append(df_ts)

            except Exception as e:
                print(f"Erro ao ler {filepath}: {e}")

    df_runs = pd.DataFrame(runs_data)
    df_ts_all = pd.concat(timeseries_data, ignore_index=True) if timeseries_data else pd.DataFrame()

    return df_runs, df_ts_all

def save_single_plot(fig, output_dir, filename):
    filepath = os.path.join(output_dir, filename)
    fig.tight_layout()
    fig.savefig(filepath, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f" -> Guardado: {filename}")

def plot_all(df_runs, df_ts, output_dir):
    """
    Gera cada gráfico individualmente (1 gráfico por imagem) cobrindo todas as perspetivas:
    - Boxplots e violinos
    - Curvas lineares e logarítmicas
    - Percentis de fluidez (P95, P99, 1% low)
    - Memória detalhada (alocada vs reservada vs overhead)
    - Eficiência por conveyor (custo computacional por unidade)
    - Evolução temporal
    - Matriz de correlação
    """
    os.makedirs(output_dir, exist_ok=True)
    conveyors_order = sorted(df_runs['Conveyors'].unique())
    conveyors_str = [str(c) for c in conveyors_order]

    # Agregações de apoio
    stats = df_runs.groupby('Conveyors').agg({
        'StartupTime_s': ['mean', 'std', 'median'],
        'FPS_Mean': ['mean', 'std', 'median'],
        'FPS_P01_Low': ['mean', 'std'],
        'FPS_Startup_Mean': ['mean', 'std'],
        'FrameTime_Mean_ms': ['mean', 'std', 'median'],
        'FrameTime_P95_ms': ['mean', 'std'],
        'FrameTime_P99_ms': ['mean', 'std'],
        'Pct_Frames_Below_60': ['mean'],
        'Pct_Frames_Below_30': ['mean'],
        'RAM_Alloc_Max_MB': ['mean', 'std'],
        'RAM_Alloc_Mean_MB': ['mean', 'std'],
        'RAM_Reserved_Max_MB': ['mean', 'std'],
        'RAM_Reserved_Mean_MB': ['mean', 'std']
    }).reset_index()
    stats.columns = ['_'.join(c).strip('_') for c in stats.columns.values]

    palette_base = "crest"
    colors_conv = sns.color_palette("tab10", len(conveyors_order))

    # =========================================================================
    # GROUP 1: STARTUP TIME
    # =========================================================================
    # 01. Boxplot Startup
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(data=df_runs, x='Conveyors', y='StartupTime_s', hue='Conveyors', legend=False, palette='Blues_d', ax=ax, showmeans=True,
                meanprops={"marker":"o", "markerfacecolor":"red", "markeredgecolor":"black", "markersize": 6})
    ax.set_title("Startup Time Distribution (Boxplot)")
    ax.set_xlabel("Number of Conveyors")
    ax.set_ylabel("Startup Time (s)")
    save_single_plot(fig, output_dir, "01_startup_time_boxplot.png")

    # 02. Violin Plot Startup
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.violinplot(data=df_runs, x='Conveyors', y='StartupTime_s', hue='Conveyors', legend=False, palette='Blues', ax=ax, inner="quartile")
    ax.set_title("Startup Time Density and Distribution (Violin Plot)")
    ax.set_xlabel("Number of Conveyors")
    ax.set_ylabel("Startup Time (s)")
    save_single_plot(fig, output_dir, "02_startup_time_violin.png")

    # 03. Linear Trend Startup
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(stats['Conveyors'], stats['StartupTime_s_mean'], marker='o', color='#1f77b4', linewidth=2.2, label='Mean')
    ax.fill_between(stats['Conveyors'], 
                     stats['StartupTime_s_mean'] - stats['StartupTime_s_std'], 
                     stats['StartupTime_s_mean'] + stats['StartupTime_s_std'], 
                     alpha=0.25, color='#1f77b4', label='±1 Standard Deviation')
    ax.set_title("Mean Startup Time vs. Scale")
    ax.set_xlabel("Number of Conveyors")
    ax.set_ylabel("Mean Startup Time (s)")
    ax.legend()
    save_single_plot(fig, output_dir, "03_startup_time_trend.png")

    # 04. Startup Time in Log-Log Scale
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(stats['Conveyors'], stats['StartupTime_s_mean'], marker='s', color='#2b5c8f', linewidth=2, label='Mean (Log-Log Scale)')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_title("Startup Time in Log-Log Scale (Complexity Analysis)")
    ax.set_xlabel("Number of Conveyors (log)")
    ax.set_ylabel("Startup Time (s, log)")
    ax.grid(True, which="both", ls="--", alpha=0.5)
    ax.legend()
    save_single_plot(fig, output_dir, "04_startup_time_loglog.png")

    # 05. Startup Time per Unit Conveyor
    df_runs['Startup_per_Conveyor_ms'] = (df_runs['StartupTime_s'] / df_runs['Conveyors']) * 1000.0
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(data=df_runs, x='Conveyors', y='Startup_per_Conveyor_ms', hue='Conveyors', legend=False, palette='mako', ax=ax, errorbar='sd', capsize=0.1)
    ax.set_title("Mean Startup Time per Conveyor")
    ax.set_xlabel("Number of Conveyors")
    ax.set_ylabel("Time per Conveyor (ms/conveyor)")
    save_single_plot(fig, output_dir, "05_startup_time_per_conveyor.png")

    # =========================================================================
    # GROUP 2: FPS (FRAMES PER SECOND)
    # =========================================================================
    # 06. FPS Mean Boxplot
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(data=df_runs, x='Conveyors', y='FPS_Mean', hue='Conveyors', legend=False, palette='Greens_d', ax=ax, showmeans=True,
                meanprops={"marker":"o", "markerfacecolor":"red", "markeredgecolor":"black", "markersize": 6})
    ax.axhline(60, color='blue', linestyle='--', alpha=0.6, label='60 FPS')
    ax.axhline(30, color='red', linestyle='--', alpha=0.6, label='30 FPS')
    ax.set_title("Mean FPS Distribution (Boxplot)")
    ax.set_xlabel("Number of Conveyors")
    ax.set_ylabel("Frames per Second (FPS)")
    ax.legend(loc='upper right')
    save_single_plot(fig, output_dir, "06_fps_mean_boxplot.png")

    # 07. FPS Mean Violin Plot
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.violinplot(data=df_runs, x='Conveyors', y='FPS_Mean', hue='Conveyors', legend=False, palette='Greens', ax=ax, inner="quartile")
    ax.axhline(60, color='blue', linestyle='--', alpha=0.6, label='60 FPS')
    ax.axhline(30, color='red', linestyle='--', alpha=0.6, label='30 FPS')
    ax.set_title("Mean FPS Density (Violin Plot)")
    ax.set_xlabel("Number of Conveyors")
    ax.set_ylabel("Mean FPS")
    ax.legend(loc='upper right')
    save_single_plot(fig, output_dir, "07_fps_mean_violin.png")

    # 08. FPS Trend with Standard Deviation
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(stats['Conveyors'], stats['FPS_Mean_mean'], marker='o', color='#2ca02c', linewidth=2.2, label='Mean FPS')
    ax.fill_between(stats['Conveyors'], 
                    stats['FPS_Mean_mean'] - stats['FPS_Mean_std'], 
                    stats['FPS_Mean_mean'] + stats['FPS_Mean_std'], 
                    alpha=0.25, color='#2ca02c', label='±1 Std Dev')
    ax.axhline(60, color='blue', linestyle='--', alpha=0.7, label='60 FPS')
    ax.axhline(30, color='red', linestyle='--', alpha=0.7, label='30 FPS')
    ax.set_title("Mean FPS Degradation vs. Conveyor Scale")
    ax.set_xlabel("Number of Conveyors")
    ax.set_ylabel("Frames per Second (FPS)")
    ax.legend()
    save_single_plot(fig, output_dir, "08_fps_mean_trend.png")

    # 09. FPS Mean vs FPS 1% Low (Micro-stuttering)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(stats['Conveyors'], stats['FPS_Mean_mean'], marker='o', color='#2ca02c', linewidth=2, label='Mean FPS')
    ax.plot(stats['Conveyors'], stats['FPS_P01_Low_mean'], marker='^', color='#d62728', linewidth=2, linestyle='--', label='1% Low FPS')
    ax.axhline(60, color='gray', linestyle=':', alpha=0.6, label='60 FPS')
    ax.axhline(30, color='gray', linestyle='--', alpha=0.6, label='30 FPS')
    ax.set_title("Smoothness Stability: Mean FPS vs. 1% Low FPS")
    ax.set_xlabel("Number of Conveyors")
    ax.set_ylabel("Frames per Second (FPS)")
    ax.legend()
    save_single_plot(fig, output_dir, "09_fps_stability_1pct_low.png")

    # 10. Absolute Minimum FPS per Run
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(data=df_runs, x='Conveyors', y='FPS_Min', hue='Conveyors', legend=False, palette='YlOrRd', ax=ax)
    ax.set_title("Minimum Recorded FPS per Run")
    ax.set_xlabel("Number of Conveyors")
    ax.set_ylabel("Minimum FPS")
    save_single_plot(fig, output_dir, "10_fps_min_boxplot.png")

    # 11. FPS During Startup vs Steady State
    fig, ax = plt.subplots(figsize=(8, 5))
    stats_fps_phases = pd.DataFrame({
        'Conveyors': stats['Conveyors'],
        'Startup': stats['FPS_Startup_Mean_mean'],
        'Steady State': stats['FPS_Mean_mean']
    }).melt(id_vars='Conveyors', var_name='Phase', value_name='FPS')
    sns.barplot(data=stats_fps_phases, x='Conveyors', y='FPS', hue='Phase', palette=['#ff7f0e', '#2ca02c'], ax=ax)
    ax.set_title("FPS Comparison: Startup Phase vs. Steady State")
    ax.set_xlabel("Number of Conveyors")
    ax.set_ylabel("Mean FPS")
    save_single_plot(fig, output_dir, "11_fps_startup_vs_steady.png")

    # 12. Percentage of Frames Below 60 FPS and Below 30 FPS
    fig, ax = plt.subplots(figsize=(8, 5))
    df_pct_melted = df_runs.melt(id_vars=['Conveyors'], value_vars=['Pct_Frames_Below_60', 'Pct_Frames_Below_30'],
                                  var_name='Criterion', value_name='Percentage')
    df_pct_melted['Criterion'] = df_pct_melted['Criterion'].map({
        'Pct_Frames_Below_60': '< 60 FPS',
        'Pct_Frames_Below_30': '< 30 FPS'
    })
    sns.barplot(data=df_pct_melted, x='Conveyors', y='Percentage', hue='Criterion', palette=['#f39c12', '#c0392b'], ax=ax, errorbar='sd', capsize=0.1)
    ax.set_title("Mean Percentage of Frames with Performance Degradation")
    ax.set_xlabel("Number of Conveyors")
    ax.set_ylabel("% of Affected Frames")
    save_single_plot(fig, output_dir, "12_fps_drop_percentages.png")

    # =========================================================================
    # GROUP 3: FRAME TIME (MILLISECONDS)
    # =========================================================================
    # 13. Mean Frame Time Boxplot
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(data=df_runs, x='Conveyors', y='FrameTime_Mean_ms', hue='Conveyors', legend=False, palette='Oranges_d', ax=ax, showmeans=True,
                meanprops={"marker":"o", "markerfacecolor":"blue", "markeredgecolor":"black", "markersize": 6})
    ax.axhline(16.67, color='green', linestyle='--', alpha=0.7, label='16.7 ms (60 FPS)')
    ax.axhline(33.33, color='red', linestyle='--', alpha=0.7, label='33.3 ms (30 FPS)')
    ax.set_title("Mean Frame Rendering Time (Frame Time)")
    ax.set_xlabel("Number of Conveyors")
    ax.set_ylabel("Frame Time (ms)")
    ax.legend()
    save_single_plot(fig, output_dir, "13_frametime_mean_boxplot.png")

    # 14. Mean Frame Time Violin Plot
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.violinplot(data=df_runs, x='Conveyors', y='FrameTime_Mean_ms', hue='Conveyors', legend=False, palette='Oranges', ax=ax, inner="quartile")
    ax.axhline(16.67, color='green', linestyle='--', alpha=0.7, label='16.7 ms (60 FPS)')
    ax.axhline(33.33, color='red', linestyle='--', alpha=0.7, label='33.3 ms (30 FPS)')
    ax.set_title("Mean Frame Time Density (Violin Plot)")
    ax.set_xlabel("Number of Conveyors")
    ax.set_ylabel("Frame Time (ms)")
    ax.legend()
    save_single_plot(fig, output_dir, "14_frametime_mean_violin.png")

    # 15. Frame Time 95th Percentile (P95) Boxplot
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(data=df_runs, x='Conveyors', y='FrameTime_P95_ms', hue='Conveyors', legend=False, palette='copper', ax=ax)
    ax.axhline(16.67, color='green', linestyle='--', alpha=0.7, label='16.7 ms (60 FPS)')
    ax.axhline(33.33, color='red', linestyle='--', alpha=0.7, label='33.3 ms (30 FPS)')
    ax.set_title("Frame Time - 95th Percentile (P95) vs. Scale")
    ax.set_xlabel("Number of Conveyors")
    ax.set_ylabel("Frame Time P95 (ms)")
    ax.legend()
    save_single_plot(fig, output_dir, "15_frametime_p95_boxplot.png")

    # 16. Frame Time 99th Percentile (P99 - Tail Latency) Boxplot
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(data=df_runs, x='Conveyors', y='FrameTime_P99_ms', hue='Conveyors', legend=False, palette='inferno', ax=ax)
    ax.set_title("Frame Time - 99th Percentile (P99 / Tail Latency)")
    ax.set_xlabel("Number of Conveyors")
    ax.set_ylabel("Frame Time P99 (ms)")
    save_single_plot(fig, output_dir, "16_frametime_p99_boxplot.png")

    # 17. Comparison of Latency Metrics (Mean, P95 and P99)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(stats['Conveyors'], stats['FrameTime_Mean_ms_mean'], marker='o', color='#2b5c8f', linewidth=2, label='Mean')
    ax.plot(stats['Conveyors'], stats['FrameTime_P95_ms_mean'], marker='s', color='#e67e22', linewidth=2, label='P95')
    ax.plot(stats['Conveyors'], stats['FrameTime_P99_ms_mean'], marker='^', color='#c0392b', linewidth=2, linestyle='--', label='P99')
    ax.axhline(16.67, color='green', linestyle=':', label='16.7 ms (60 FPS)')
    ax.axhline(33.33, color='red', linestyle=':', label='33.3 ms (30 FPS)')
    ax.set_title("Latency Scaling: Mean vs. P95 vs. P99")
    ax.set_xlabel("Number of Conveyors")
    ax.set_ylabel("Milliseconds (ms)")
    ax.legend()
    save_single_plot(fig, output_dir, "17_frametime_latencies_comparison.png")

    # 18. Frame Time in Logarithmic Scale
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(stats['Conveyors'], stats['FrameTime_Mean_ms_mean'], marker='o', color='#d35400', linewidth=2.2, label='Mean Frame Time')
    ax.set_yscale('log')
    ax.axhline(16.67, color='green', linestyle='--', alpha=0.7, label='16.7 ms (60 FPS)')
    ax.axhline(33.33, color='red', linestyle='--', alpha=0.7, label='33.3 ms (30 FPS)')
    ax.set_title("Mean Frame Time in Semi-Logarithmic Scale")
    ax.set_xlabel("Number of Conveyors")
    ax.set_ylabel("Frame Time (ms, log scale)")
    ax.legend()
    save_single_plot(fig, output_dir, "18_frametime_semilog.png")

    # 19. Frame Time Standard Deviation (Jitter)
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(data=df_runs, x='Conveyors', y='FrameTime_Std_ms', hue='Conveyors', legend=False, palette='magma', ax=ax)
    ax.set_title("Frame Time Jitter (Standard Deviation per Run)")
    ax.set_xlabel("Number of Conveyors")
    ax.set_ylabel("Frame Time Standard Deviation (ms)")
    save_single_plot(fig, output_dir, "19_frametime_jitter_std.png")

    # 20. Unit Frame Time per Conveyor
    df_runs['FrameTime_per_Conveyor_us'] = (df_runs['FrameTime_Mean_ms'] / df_runs['Conveyors']) * 1000.0
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(data=df_runs, x='Conveyors', y='FrameTime_per_Conveyor_us', hue='Conveyors', legend=False, palette='viridis', ax=ax, errorbar='sd', capsize=0.1)
    ax.set_title("Unit Frame Computational Cost per Conveyor")
    ax.set_xlabel("Number of Conveyors")
    ax.set_ylabel("Unit Frame Time (µs / conveyor)")
    save_single_plot(fig, output_dir, "20_frametime_per_conveyor_unit.png")

    # =========================================================================
    # GROUP 4: RAM MEMORY (ALLOCATED, TOTAL RESERVED AND OVERHEAD)
    # =========================================================================
    # 21. Max Allocated RAM Boxplot
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(data=df_runs, x='Conveyors', y='RAM_Alloc_Max_MB', hue='Conveyors', legend=False, palette='Purples_d', ax=ax, showmeans=True)
    ax.set_title("Peak Allocated RAM (Managed Heap)")
    ax.set_xlabel("Number of Conveyors")
    ax.set_ylabel("Peak Allocated RAM (MB)")
    save_single_plot(fig, output_dir, "21_ram_allocated_max_boxplot.png")

    # 22. Max Reserved RAM Boxplot
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(data=df_runs, x='Conveyors', y='RAM_Reserved_Max_MB', hue='Conveyors', legend=False, palette='Reds_d', ax=ax, showmeans=True)
    ax.set_title("Peak Process Reserved RAM")
    ax.set_xlabel("Number of Conveyors")
    ax.set_ylabel("Peak Reserved RAM (MB)")
    save_single_plot(fig, output_dir, "22_ram_reserved_max_boxplot.png")

    # 23. Comparison of Mean Curves: Allocated vs Reserved RAM
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(stats['Conveyors'], stats['RAM_Reserved_Max_MB_mean'], marker='s', color='#d62728', linewidth=2.2, label='Peak Reserved RAM')
    ax.fill_between(stats['Conveyors'], 
                    stats['RAM_Reserved_Max_MB_mean'] - stats['RAM_Reserved_Max_MB_std'], 
                    stats['RAM_Reserved_Max_MB_mean'] + stats['RAM_Reserved_Max_MB_std'], 
                    alpha=0.2, color='#d62728')
    ax.plot(stats['Conveyors'], stats['RAM_Alloc_Max_MB_mean'], marker='o', color='#9467bd', linewidth=2.2, label='Peak Allocated RAM')
    ax.fill_between(stats['Conveyors'], 
                    stats['RAM_Alloc_Max_MB_mean'] - stats['RAM_Alloc_Max_MB_std'], 
                    stats['RAM_Alloc_Max_MB_mean'] + stats['RAM_Alloc_Max_MB_std'], 
                    alpha=0.2, color='#9467bd')
    ax.set_title("Mean RAM Consumption Comparison: Allocated vs. Reserved")
    ax.set_xlabel("Number of Conveyors")
    ax.set_ylabel("RAM Memory (MB)")
    ax.legend()
    save_single_plot(fig, output_dir, "23_ram_alloc_vs_reserved_curves.png")

    # 24. Unallocated Reserved RAM (Engine Overhead)
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.boxplot(data=df_runs, x='Conveyors', y='RAM_Unallocated_Max_MB', hue='Conveyors', legend=False, palette='coolwarm', ax=ax)
    ax.set_title("Engine Memory Overhead (Reserved RAM - Allocated RAM)")
    ax.set_xlabel("Number of Conveyors")
    ax.set_ylabel("Unallocated Reserved Heap (MB)")
    save_single_plot(fig, output_dir, "24_ram_overhead_unallocated.png")

    # 25. RAM Consumption per Conveyor (Unit Memory Footprint)
    df_runs['RAM_Alloc_per_Conveyor_KB'] = (df_runs['RAM_Alloc_Max_MB'] / df_runs['Conveyors']) * 1024.0
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(data=df_runs, x='Conveyors', y='RAM_Alloc_per_Conveyor_KB', hue='Conveyors', legend=False, palette='crest', ax=ax, errorbar='sd', capsize=0.1)
    ax.set_title("Unit Memory Footprint per Conveyor (Allocated RAM / Conveyors)")
    ax.set_xlabel("Number of Conveyors")
    ax.set_ylabel("RAM per Conveyor (KB/conveyor)")
    save_single_plot(fig, output_dir, "25_ram_footprint_per_conveyor.png")

    # 26. Total RAM Consumption in Semi-Log Scale
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(stats['Conveyors'], stats['RAM_Reserved_Max_MB_mean'], marker='s', color='#d62728', linewidth=2, label='Peak Reserved RAM')
    ax.plot(stats['Conveyors'], stats['RAM_Alloc_Max_MB_mean'], marker='o', color='#9467bd', linewidth=2, label='Peak Allocated RAM')
    ax.set_xscale('log')
    ax.set_title("Memory Consumption vs. Scale in Semi-Log X Scale")
    ax.set_xlabel("Number of Conveyors (log)")
    ax.set_ylabel("Memory (MB)")
    ax.grid(True, which="both", ls="--", alpha=0.5)
    ax.legend()
    save_single_plot(fig, output_dir, "26_ram_semilog_scale.png")

    # =========================================================================
    # GROUP 5: TIME SERIES (SIMULATION TIMELINE EVOLUTION)
    # =========================================================================
    if not df_ts.empty:
        df_ts_filt = df_ts[df_ts['Time_bin'] <= 65]
        ts_mean = df_ts_filt.groupby(['Conveyors', 'Time_bin']).agg({
            'FPS': 'mean',
            'FrameTime_ms': 'mean',
            'RAM_Allocated_MB': 'mean',
            'RAM_TotalReserved_MB': 'mean'
        }).reset_index()

        # 27. FPS Time Series
        fig, ax = plt.subplots(figsize=(9, 5))
        for idx, c in enumerate(conveyors_order):
            sub = ts_mean[ts_mean['Conveyors'] == c]
            ax.plot(sub['Time_bin'], sub['FPS'], label=f"{c} conveyors", linewidth=1.8, color=colors_conv[idx % len(colors_conv)])
        ax.set_title("Mean FPS Evolution Over Simulation Time")
        ax.set_xlabel("Elapsed Time (s)")
        ax.set_ylabel("Mean FPS")
        ax.axhline(60, color='gray', linestyle=':', alpha=0.5)
        ax.axhline(30, color='gray', linestyle='--', alpha=0.5)
        ax.legend(title="Scale", bbox_to_anchor=(1.02, 1), loc='upper left')
        save_single_plot(fig, output_dir, "27_timeseries_fps.png")

        # 28. Frame Time Time Series
        fig, ax = plt.subplots(figsize=(9, 5))
        for idx, c in enumerate(conveyors_order):
            sub = ts_mean[ts_mean['Conveyors'] == c]
            ax.plot(sub['Time_bin'], sub['FrameTime_ms'], label=f"{c} conveyors", linewidth=1.8, color=colors_conv[idx % len(colors_conv)])
        ax.set_title("Mean Frame Time Evolution Over Simulation Time")
        ax.set_xlabel("Elapsed Time (s)")
        ax.set_ylabel("Frame Time (ms)")
        ax.axhline(16.67, color='green', linestyle=':', label='60 FPS')
        ax.axhline(33.33, color='red', linestyle=':', label='30 FPS')
        ax.legend(title="Scale", bbox_to_anchor=(1.02, 1), loc='upper left')
        save_single_plot(fig, output_dir, "28_timeseries_frametime.png")

        # 29. Allocated RAM Time Series
        fig, ax = plt.subplots(figsize=(9, 5))
        for idx, c in enumerate(conveyors_order):
            sub = ts_mean[ts_mean['Conveyors'] == c]
            ax.plot(sub['Time_bin'], sub['RAM_Allocated_MB'], label=f"{c} conveyors", linewidth=1.8, color=colors_conv[idx % len(colors_conv)])
        ax.set_title("Allocated RAM Evolution Over Simulation Time")
        ax.set_xlabel("Elapsed Time (s)")
        ax.set_ylabel("Allocated RAM (MB)")
        ax.legend(title="Scale", bbox_to_anchor=(1.02, 1), loc='upper left')
        save_single_plot(fig, output_dir, "29_timeseries_ram_allocated.png")

        # 30. Total Reserved RAM Time Series
        fig, ax = plt.subplots(figsize=(9, 5))
        for idx, c in enumerate(conveyors_order):
            sub = ts_mean[ts_mean['Conveyors'] == c]
            ax.plot(sub['Time_bin'], sub['RAM_TotalReserved_MB'], label=f"{c} conveyors", linewidth=1.8, color=colors_conv[idx % len(colors_conv)])
        ax.set_title("Reserved RAM Evolution Over Simulation Time")
        ax.set_xlabel("Elapsed Time (s)")
        ax.set_ylabel("Reserved RAM (MB)")
        ax.legend(title="Scale", bbox_to_anchor=(1.02, 1), loc='upper left')
        save_single_plot(fig, output_dir, "30_timeseries_ram_reserved.png")

    # =========================================================================
    # GROUP 6: CORRELATIONS, CDFs AND SCATTER PLOTS
    # =========================================================================
    # 31. Frame Time Empirical Cumulative Distribution Function (CDF)
    fig, ax = plt.subplots(figsize=(8, 5))
    for idx, c in enumerate(conveyors_order):
        vals = np.sort(df_runs[df_runs['Conveyors'] == c]['FrameTime_Mean_ms'].dropna())
        if len(vals) > 0:
            y = np.arange(1, len(vals) + 1) / len(vals)
            ax.step(vals, y, label=f"{c} conveyors", linewidth=2, color=colors_conv[idx % len(colors_conv)])
    ax.axvline(16.67, color='green', linestyle=':', label='16.7 ms')
    ax.axvline(33.33, color='red', linestyle=':', label='33.3 ms')
    ax.set_title("CDF (Cumulative Distribution Function) of Mean Frame Time")
    ax.set_xlabel("Mean Frame Time (ms)")
    ax.set_ylabel("Cumulative Probability P(X ≤ x)")
    ax.legend()
    save_single_plot(fig, output_dir, "31_cdf_frametime.png")

    # 32. Startup Time CDF
    fig, ax = plt.subplots(figsize=(8, 5))
    for idx, c in enumerate(conveyors_order):
        vals = np.sort(df_runs[df_runs['Conveyors'] == c]['StartupTime_s'].dropna())
        if len(vals) > 0:
            y = np.arange(1, len(vals) + 1) / len(vals)
            ax.step(vals, y, label=f"{c} conveyors", linewidth=2, color=colors_conv[idx % len(colors_conv)])
    ax.set_title("CDF of Startup Time")
    ax.set_xlabel("Startup Time (s)")
    ax.set_ylabel("Cumulative Probability P(X ≤ x)")
    ax.legend()
    save_single_plot(fig, output_dir, "32_cdf_startup_time.png")

    # 33. Scatter: Startup Time vs Peak Allocated RAM
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.scatterplot(data=df_runs, x='StartupTime_s', y='RAM_Alloc_Max_MB', hue='Conveyors', palette='viridis', style='Conveyors', s=60, ax=ax)
    ax.set_title("Startup Time vs. Peak Allocated RAM")
    ax.set_xlabel("Startup Time (s)")
    ax.set_ylabel("Peak Allocated RAM (MB)")
    ax.legend(title="Conveyors")
    save_single_plot(fig, output_dir, "33_scatter_startup_vs_ram.png")

    # 34. Scatter: Mean Frame Time vs Peak Reserved RAM
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.scatterplot(data=df_runs, x='RAM_Reserved_Max_MB', y='FrameTime_Mean_ms', hue='Conveyors', palette='turbo', s=60, ax=ax)
    ax.set_title("Peak Reserved RAM vs. Mean Frame Time")
    ax.set_xlabel("Peak Reserved RAM (MB)")
    ax.set_ylabel("Mean Frame Time (ms)")
    ax.legend(title="Conveyors")
    save_single_plot(fig, output_dir, "34_scatter_ram_vs_frametime.png")

    # 35. Scatter: Mean FPS vs Startup Time
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.scatterplot(data=df_runs, x='StartupTime_s', y='FPS_Mean', hue='Conveyors', palette='tab10', s=60, ax=ax)
    ax.axhline(60, color='gray', linestyle=':', alpha=0.5)
    ax.axhline(30, color='gray', linestyle='--', alpha=0.5)
    ax.set_title("Performance Trade-off: Mean FPS vs. Startup Time")
    ax.set_xlabel("Startup Time (s)")
    ax.set_ylabel("Mean FPS")
    ax.legend(title="Conveyors")
    save_single_plot(fig, output_dir, "35_scatter_fps_vs_startup.png")

    # 36. Correlation Heatmap
    corr_cols = [
        'Conveyors', 'StartupTime_s', 'FPS_Mean', 'FPS_P01_Low',
        'FrameTime_Mean_ms', 'FrameTime_P95_ms'
    ]
    rename_labels = {
        'Conveyors': 'Conveyors',
        'StartupTime_s': 'Startup Time',
        'FPS_Mean': 'Mean FPS',
        'FPS_P01_Low': '1% Low FPS',
        'FrameTime_Mean_ms': 'Mean Frame Time',
        'FrameTime_P95_ms': 'Frame Time P95'
    }
    df_corr = df_runs[corr_cols].rename(columns=rename_labels).corr()
    fig, ax = plt.subplots(figsize=(8, 6.5))
    sns.heatmap(df_corr, annot=True, fmt=".2f", cmap='vlag', vmin=-1, vmax=1, ax=ax, square=True, cbar_kws={'label': "Pearson's Correlation (r)"})
    ax.set_title("Linear Correlation Matrix between Performance Metrics")
    save_single_plot(fig, output_dir, "36_correlation_heatmap.png")

    # 37. Coefficient of Variation (CV = Std / Mean)
    stats['StartupTime_CV_%'] = (stats['StartupTime_s_std'] / stats['StartupTime_s_mean']) * 100.0
    stats['FPS_CV_%'] = (stats['FPS_Mean_std'] / stats['FPS_Mean_mean']) * 100.0
    stats['FrameTime_CV_%'] = (stats['FrameTime_Mean_ms_std'] / stats['FrameTime_Mean_ms_mean']) * 100.0
    stats['RAM_Alloc_CV_%'] = (stats['RAM_Alloc_Max_MB_std'] / stats['RAM_Alloc_Max_MB_mean']) * 100.0

    df_cv_melted = stats.melt(id_vars=['Conveyors'], value_vars=['StartupTime_CV_%', 'FPS_CV_%', 'FrameTime_CV_%', 'RAM_Alloc_CV_%'],
                              var_name='Metric', value_name='CV_pct')
    df_cv_melted['Metric'] = df_cv_melted['Metric'].map({
        'StartupTime_CV_%': 'Startup Time',
        'FPS_CV_%': 'Mean FPS',
        'FrameTime_CV_%': 'Mean Frame Time',
        'RAM_Alloc_CV_%': 'Allocated RAM'
    })
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(data=df_cv_melted, x='Conveyors', y='CV_pct', hue='Metric', palette='Set2', ax=ax)
    ax.set_title("Experimental Stability: Coefficient of Variation (CV %)")
    ax.set_xlabel("Number of Conveyors")
    ax.set_ylabel("Coefficient of Variation (%)")
    save_single_plot(fig, output_dir, "37_coefficient_of_variation.png")

    # Export summary tables
    stats.to_csv(os.path.join(output_dir, "summary_statistics_complete.csv"), index=False, float_format="%.2f")
    try:
        stats.to_latex(os.path.join(output_dir, "summary_statistics_complete.tex"), index=False, float_format="%.2f")
    except Exception:
        pass

    print(f"\n[OK] 37 Gráficos individuais (1 a 1) gerados com sucesso na pasta: {output_dir}")

def main():
    parser = argparse.ArgumentParser(description="Gera gráficos comparativos individuais a partir dos dados das pastas de conveyors.")
    parser.add_argument("--dir", default=".", help="Diretório base que contém as pastas de testes (padrão: atual)")
    parser.add_argument("--output", default="graficos_individuais", help="Diretório de saída para os gráficos")
    args = parser.parse_args()

    df_runs, df_ts = load_data(args.dir)
    if df_runs.empty:
        print("Nenhum dado encontrado para gerar gráficos.")
        return

    plot_all(df_runs, df_ts, args.output)

if __name__ == "__main__":
    main()
