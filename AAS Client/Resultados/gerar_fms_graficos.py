import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
import glob, os, re

sns.set_theme(style='whitegrid', palette='deep')
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

fms_csvs = glob.glob('AAS Client/Resultados/FMS/**/*.csv', recursive=True)
runs = []
ts_list = []

for f in fms_csvs:
    df = pd.read_csv(f)
    fname = os.path.basename(f)
    match = re.search(r'run_metrics_(\\d+)_(\\d+)', fname)
    run_id = f'{match.group(1)}_{match.group(2)}' if match else fname
    startup_time = df['StartupTime_s'].max()
    df_steady = df[df['IsStartupComplete'] == 1]
    if df_steady.empty:
        df_steady = df[df['Timestamp_s'] > startup_time]
    if df_steady.empty:
        df_steady = df.tail(len(df)//2)
    
    fps_mean = df_steady['FPS'].mean()
    fps_min = df_steady['FPS'].min()
    fps_p01 = df_steady['FPS'].quantile(0.01)
    
    ft_mean = df_steady['FrameTime_ms'].mean()
    ft_p95 = df_steady['FrameTime_ms'].quantile(0.95)
    ft_p99 = df_steady['FrameTime_ms'].quantile(0.99)
    ft_std = df_steady['FrameTime_ms'].std()
    
    runs.append({
        'RunID': run_id,
        'StartupTime_s': startup_time,
        'FPS_Mean': fps_mean,
        'FPS_Min': fps_min,
        'FPS_P01_Low': fps_p01,
        'FrameTime_Mean_ms': ft_mean,
        'FrameTime_P95_ms': ft_p95,
        'FrameTime_P99_ms': ft_p99,
        'FrameTime_Std_ms': ft_std,
        'Duration_s': df['Timestamp_s'].max()
    })
    
    df_ts = df[['Timestamp_s', 'FPS', 'FrameTime_ms']].copy()
    df_ts['Time_bin'] = df_ts['Timestamp_s'].round(1)
    ts_list.append(df_ts)

df_runs = pd.DataFrame(runs)
df_ts = pd.concat(ts_list, ignore_index=True)

out_dirs = ['AAS Client/Resultados/graficos_fms', 'Documentos/5-Figures']
for od in out_dirs:
    os.makedirs(od, exist_ok=True)

def save_plot(fig, name):
    for od in out_dirs:
        path = os.path.join(od, name)
        fig.savefig(path, dpi=300, bbox_inches='tight')
    plt.close(fig)

# 1. Distribution of Startup and FPS (High-Clarity 2-Panel Plot)
fig, axes = plt.subplots(1, 2, figsize=(9, 4.2))

# Subplot 1: Startup Time
st_mean = df_runs['StartupTime_s'].mean()
st_std = df_runs['StartupTime_s'].std()
sns.boxplot(y=df_runs['StartupTime_s'], ax=axes[0], color='#2b5c8f', width=0.35, showmeans=True,
            meanprops={'marker':'o', 'markerfacecolor':'red', 'markeredgecolor':'black', 'markersize':8})
axes[0].set_title(f'Startup Initialization Time\n(Mean: {st_mean:.2f}s \u00b1 {st_std:.2f}s)', pad=10)
axes[0].set_ylabel('Startup Time (seconds)')

# Subplot 2: FPS
fps_mean_val = df_runs['FPS_Mean'].mean()
fps_std_val = df_runs['FPS_Mean'].std()
sns.boxplot(y=df_runs['FPS_Mean'], ax=axes[1], color='#27ae60', width=0.35, showmeans=True,
            meanprops={'marker':'o', 'markerfacecolor':'red', 'markeredgecolor':'black', 'markersize':8})
axes[1].axhline(60, color='#c0392b', linestyle='--', linewidth=1.5, label='60 FPS Reference Target')
axes[1].set_title(f'Steady-State Rendering Rate\n(Mean: {fps_mean_val:.1f} \u00b1 {fps_std_val:.1f} FPS)', pad=10)
axes[1].set_ylabel('Frames per Second (FPS)')
axes[1].legend(loc='lower right')

fig.tight_layout()
save_plot(fig, 'fms_metrics_distributions.pdf')
save_plot(fig, 'fms_metrics_distributions.png')

# 2. Time Series of FMS execution
ts_agg = df_ts.groupby('Time_bin').agg({
    'FPS': ['mean', 'std'],
    'FrameTime_ms': ['mean', 'std']
}).reset_index()
ts_agg.columns = ['Time_bin', 'FPS_mean', 'FPS_std', 'FT_mean', 'FT_std']
ts_agg = ts_agg[ts_agg['Time_bin'] <= 7.5]

fig, ax1 = plt.subplots(figsize=(8, 4.5))
color = '#27ae60'
ax1.set_xlabel('Elapsed Time (s)')
ax1.set_ylabel('Mean FPS', color=color)
ax1.plot(ts_agg['Time_bin'], ts_agg['FPS_mean'], color=color, linewidth=2, label='Mean FPS')
ax1.fill_between(ts_agg['Time_bin'], ts_agg['FPS_mean'] - ts_agg['FPS_std'], ts_agg['FPS_mean'] + ts_agg['FPS_std'], color=color, alpha=0.2)
ax1.tick_params(axis='y', labelcolor=color)
ax1.axvline(st_mean, color='#2980b9', linestyle=':', linewidth=2, label=f'Startup Completion (~{st_mean:.2f}s)')

ax2 = ax1.twinx()
color = '#e67e22'
ax2.set_ylabel('Frame Time (ms)', color=color)
ax2.plot(ts_agg['Time_bin'], ts_agg['FT_mean'], color=color, linewidth=2, linestyle='--', label='Frame Time (ms)')
ax2.tick_params(axis='y', labelcolor=color)

fig.suptitle('Dynamic Execution Timeline of the Physical FMS Pilot Bench', y=1.02)
fig.tight_layout()
save_plot(fig, 'fms_timeseries_evolution.pdf')
save_plot(fig, 'fms_timeseries_evolution.png')

# 3. CDF of FMS Frame Time and Startup Time
fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
vals_ft = np.sort(df_runs['FrameTime_Mean_ms'].dropna())
y_ft = np.arange(1, len(vals_ft) + 1) / len(vals_ft)
axes[0].step(vals_ft, y_ft, color='#e67e22', linewidth=2.2, label='FMS Bench Frame Time')
axes[0].axvline(16.67, color='green', linestyle=':', label='60 FPS Target (16.7 ms)')
axes[0].set_title('Empirical CDF of Mean Frame Time')
axes[0].set_xlabel('Mean Frame Time (ms)')
axes[0].set_ylabel('Cumulative Probability P(X <= x)')
axes[0].legend()

vals_st = np.sort(df_runs['StartupTime_s'].dropna())
y_st = np.arange(1, len(vals_st) + 1) / len(vals_st)
axes[1].step(vals_st, y_st, color='#2b5c8f', linewidth=2.2, label='FMS Startup Time')
axes[1].set_title('Empirical CDF of Startup Time')
axes[1].set_xlabel('Startup Time (s)')
axes[1].set_ylabel('Cumulative Probability P(X <= x)')
axes[1].legend()

fig.tight_layout()
save_plot(fig, 'fms_cdfs.pdf')
save_plot(fig, 'fms_cdfs.png')

print('All FMS plots successfully generated in AAS Client/Resultados/graficos_fms and Documentos/5-Figures!')
