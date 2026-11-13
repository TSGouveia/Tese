"""Single-column (vertical) versions of the evaluation plots for the paper.

Data loaders are reused, read-only, from the thesis script
(Documentos Atualizado/tools/generate_chapter5_eval_plots.py); output goes ONLY to
Paper/figures/paper_*.pdf, so the thesis figures are never touched.
Figures are drawn at the IEEE column width (3.5 in) so font sizes are 1:1 in the PDF.

Run from the Tese folder:  python Paper/tools/paper_plots.py
"""
import importlib.util
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.patches as mpatches

PAPER = Path(__file__).resolve().parent.parent
TESE = PAPER.parent
OUT = PAPER / 'figures'

spec = importlib.util.spec_from_file_location(
    'thesis_plots', TESE / 'Documentos Atualizado' / 'tools' / 'generate_chapter5_eval_plots.py')
thesis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(thesis)

plt.rcdefaults()
plt.rcParams.update({
    'font.family': 'sans-serif', 'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'font.size': 8, 'axes.labelsize': 8, 'xtick.labelsize': 7, 'ytick.labelsize': 7,
    'legend.fontsize': 7, 'legend.frameon': False, 'axes.linewidth': 0.6,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.grid': True, 'grid.color': '#dddddd', 'grid.linewidth': 0.5,
    'xtick.major.width': 0.6, 'ytick.major.width': 0.6, 'lines.linewidth': 1.4,
    'savefig.bbox': 'tight', 'savefig.pad_inches': 0.02, 'pdf.fonttype': 42,
})
W = 3.5
BLUE, GREEN, ORANGE, RED, GREY = '#2b5c8f', '#2a9d55', '#d35400', '#c0392b', '#666666'


def save(fig, name):
    fig.savefig(OUT / f'{name}.pdf')
    fig.savefig(OUT / f'{name}.png', dpi=300)
    plt.close(fig)
    print('wrote', OUT / f'{name}.pdf')


def box(ax, data, color):
    ax.boxplot(data, widths=0.45, patch_artist=True, showmeans=True,
               boxprops=dict(facecolor=color, alpha=0.75, edgecolor='#222', linewidth=0.7),
               medianprops=dict(color='black', linewidth=1.0),
               whiskerprops=dict(linewidth=0.7), capprops=dict(linewidth=0.7),
               meanprops=dict(marker='o', markerfacecolor='white', markeredgecolor='black', markersize=4),
               flierprops=dict(marker='o', markersize=2.5, markerfacecolor='none', markeredgecolor=GREY))
    ax.set_xticks([])
    ax.grid(axis='x', visible=False)


def fms_distributions(runs):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(W, 2.3))
    st, fps = runs['StartupTime_s'].dropna(), runs['FPS_Mean'].dropna()
    box(a1, st, BLUE)
    a1.set_ylabel('Startup time (s)')
    a1.set_title(f'Startup: {st.mean():.2f} ± {st.std():.2f} s', fontsize=7.5)
    box(a2, fps, GREEN)
    a2.set_ylabel('Mean frame rate (FPS)')
    a2.set_title(f'Steady state: {fps.mean():.0f} ± {fps.std():.0f} FPS', fontsize=7.5)
    h = [mpatches.Patch(facecolor='#999', alpha=0.75, edgecolor='#222', label='IQR'),
         Line2D([], [], color='black', label='Median'),
         Line2D([], [], marker='o', ls='', mfc='white', mec='black', ms=4, label='Mean'),
         Line2D([], [], marker='o', ls='', mfc='none', mec=GREY, ms=3, label='Outlier')]
    fig.legend(handles=h, loc='lower center', ncol=4, bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=(0, 0.07, 1, 1), w_pad=1.5)
    save(fig, 'paper_fms_distributions')


def fms_timeseries(runs, ts):
    st = runs['StartupTime_s'].mean()
    agg = ts.groupby('Time_bin').agg(F=('FPS', 'mean'), Fs=('FPS', 'std'),
                                     T=('FrameTime_ms', 'mean'), Ts=('FrameTime_ms', 'std')).reset_index()
    agg = agg[agg['Time_bin'] <= 7.5]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(W, 3.2), sharex=True)
    t = agg['Time_bin']
    a1.plot(t, agg['F'], color=GREEN, label='Mean')
    a1.fill_between(t, agg['F'] - agg['Fs'], agg['F'] + agg['Fs'], color=GREEN, alpha=0.2, lw=0, label='±1 SD')
    a1.set_ylabel('Frame rate (FPS)')
    a2.plot(t, agg['T'], color=ORANGE, label='Mean')
    a2.fill_between(t, (agg['T'] - agg['Ts']).clip(lower=0), agg['T'] + agg['Ts'],
                    color=ORANGE, alpha=0.2, lw=0, label='±1 SD')
    a2.set_ylabel('Frame time (ms)')
    a2.set_xlabel('Elapsed time (s)')
    for a in (a1, a2):
        a.axvline(st, color=BLUE, ls=':', lw=1.2)
    a1.text(st, 1.0, f' startup complete ({st:.2f} s)', transform=a1.get_xaxis_transform(),
            color=BLUE, fontsize=6.5, va='top', ha='left')
    a1.legend(loc='lower right', ncol=2)
    a2.legend(loc='upper right', ncol=2)
    fig.tight_layout(h_pad=0.6)
    save(fig, 'paper_fms_timeseries')


def startup_complexity(runs):
    s = runs.groupby('Conveyors').agg(T=('StartupTime_s', 'mean'), Ts=('StartupTime_s', 'std'),
                                      U=('Startup_per_Conveyor_ms', 'mean'),
                                      Us=('Startup_per_Conveyor_ms', 'std')).reset_index()
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(W, 3.2), sharex=True)
    a1.errorbar(s['Conveyors'], s['T'], yerr=s['Ts'], color=BLUE, marker='o', ms=3.5, capsize=2, elinewidth=0.7)
    a1.set_yscale('log')
    a1.set_ylabel('Total startup time (s)')
    a2.errorbar(s['Conveyors'], s['U'], yerr=s['Us'], color=ORANGE, marker='s', ms=3.5, capsize=2, elinewidth=0.7)
    a2.set_ylabel('Startup per module (ms)')
    a2.set_xlabel('Number of conveyor modules $N$')
    a2.set_xscale('log')
    a2.set_xticks(s['Conveyors'])
    a2.set_xticklabels(s['Conveyors'])
    a1.minorticks_off()
    a2.minorticks_off()
    fig.tight_layout(h_pad=0.6)
    save(fig, 'paper_eval_startup')


def fps_degradation(runs):
    s = runs.groupby('Conveyors').agg(M=('FPS_Mean', 'mean'), Ms=('FPS_Mean', 'std'),
                                      L=('FPS_P01_Low', 'mean')).reset_index()
    fig, ax = plt.subplots(figsize=(W, 2.6))
    ax.plot(s['Conveyors'], s['M'], color=GREEN, marker='o', ms=3.5, label='Mean FPS')
    ax.fill_between(s['Conveyors'], (s['M'] - s['Ms']).clip(lower=0), s['M'] + s['Ms'],
                    color=GREEN, alpha=0.2, lw=0, label='±1 SD')
    ax.plot(s['Conveyors'], s['L'], color=RED, marker='^', ms=3.5, ls='--', label='1% low FPS')
    ax.axhline(60, color=BLUE, ls=':', lw=1.0, label='60 FPS')
    ax.axhline(30, color=GREY, ls='-.', lw=1.0, label='30 FPS')
    ax.set_xscale('log')
    ax.set_xticks(s['Conveyors'])
    ax.set_xticklabels(s['Conveyors'])
    ax.minorticks_off()
    ax.set_xlabel('Number of conveyor modules $N$')
    ax.set_ylabel('Frame rate (FPS)')
    ax.set_ylim(bottom=0)
    ax.legend(loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=5, handlelength=1.6, columnspacing=0.9)
    fig.tight_layout()
    save(fig, 'paper_eval_fps')


if __name__ == '__main__':
    fms_runs, fms_ts = thesis.load_fms_data()
    st_runs, _ = thesis.load_stress_data()
    print(len(fms_runs), 'FMS runs;', len(st_runs), 'stress runs')
    print(st_runs.groupby('Conveyors')[['StartupTime_s', 'FPS_Mean', 'FPS_P01_Low']].mean().round(2))
    fms_distributions(fms_runs)
    fms_timeseries(fms_runs, fms_ts)
    startup_complexity(st_runs)
    fps_degradation(st_runs)
