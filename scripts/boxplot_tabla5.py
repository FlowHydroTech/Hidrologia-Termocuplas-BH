"""Genera boxplot profesional de flujos verticales para Tabla 5 (Río Cuncumén ↔ acuífero).

Usa las estimaciones Hatch-Amplitude por par de sensores (resultados del
procesamiento), no las series temporales de ventana deslizante.
"""
import pathlib, numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

# ── Configuración ──────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'font.size': 10,
    'axes.linewidth': 0.8,
    'axes.edgecolor': '#333333',
    'axes.labelcolor': '#222222',
    'xtick.color': '#333333',
    'ytick.color': '#333333',
    'figure.facecolor': 'white',
    'axes.facecolor': '#FAFAFA',
})

ROOT     = pathlib.Path(__file__).resolve().parent.parent
FLUX_CSV = ROOT / 'resultados_python' / 'terreno_2026_hatch' / 'flujos_hatch_mccallum.csv'
IMG_DIR  = ROOT / 'image' / 'terreno_2026'
IMG_DIR.mkdir(parents=True, exist_ok=True)

ACTIVE_TCS = ['TC1', 'TC2', 'TC3', 'TC4', 'TC5']
TC_COLORS  = {'TC1': '#3274A1', 'TC2': '#E1812C', 'TC3': '#3A923A',
              'TC4': '#9372B2', 'TC5': '#C03D3E'}
PAIR_LABELS = {'sup-int': 'Sup–Int', 'int-inf': 'Int–Inf', 'sup-inf': 'Sup–Inf'}
WINDOW_HOURS = 48
STEP_HOURS   = 12

# ── 1. Leer flujos Hatch-Amplitude por par ─────────────────────────────
df_all = pd.read_csv(FLUX_CSV)
# Filtrar solo Hatch-Amplitude
df_ha = df_all[df_all['M\u00e9todo'].str.contains('Hatch-Amplitude', na=False)].copy()

tc_flux_data: dict[str, list[float]] = {}
tc_pair_names: dict[str, list[str]] = {}

for tc in ACTIVE_TCS:
    mask = df_ha['TC'].str.startswith(tc)
    sub = df_ha.loc[mask].copy()
    vals = sub['q (mm/d\u00eda)'].abs().tolist()
    pairs = sub['Par'].tolist()
    tc_flux_data[tc] = vals
    tc_pair_names[tc] = pairs

tc_names   = [tc for tc in ACTIVE_TCS if tc_flux_data[tc]]
data_boxes = [tc_flux_data[tc] for tc in tc_names]
positions  = list(range(1, len(tc_names) + 1))
colors_box = [TC_COLORS[tc] for tc in tc_names]

print("Datos por par (Hatch-Amplitude):")
for tc in tc_names:
    vals = tc_flux_data[tc]
    pairs = tc_pair_names[tc]
    detail = ', '.join(f'{p}={v:.1f}' for p, v in zip(pairs, vals))
    print(f"  {tc}: {detail}  →  media={np.mean(vals):.1f} mm/d")

# ── 2. Figura ─────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 6))

bp = ax.boxplot(data_boxes, positions=positions, widths=0.45,
                patch_artist=True, showmeans=True, showfliers=False,
                meanprops=dict(marker='D', markerfacecolor='white',
                               markeredgecolor='#333333', markersize=6,
                               markeredgewidth=1.0, zorder=5),
                medianprops=dict(color='#222222', linewidth=1.8),
                whiskerprops=dict(linewidth=1.0, color='#555555'),
                capprops=dict(linewidth=1.0, color='#555555'))

for patch, c in zip(bp['boxes'], colors_box):
    patch.set_facecolor(c)
    patch.set_alpha(0.50)
    patch.set_edgecolor('#444444')
    patch.set_linewidth(0.9)

# Superponer puntos individuales por par de sensores
PAIR_MARKERS = {'sup-int': 'o', 'int-inf': 's', 'sup-inf': '^'}
for i, tc in enumerate(tc_names):
    vals = tc_flux_data[tc]
    pairs = tc_pair_names[tc]
    for v, p in zip(vals, pairs):
        # Extraer clave corta del par
        pkey = p.lower().replace('–', '-').replace(' ', '-')
        for candidate in PAIR_MARKERS:
            if candidate in pkey:
                mk = PAIR_MARKERS[candidate]
                break
        else:
            mk = 'o'
        ax.scatter(positions[i], v, marker=mk, s=50, color=TC_COLORS[tc],
                   edgecolors='#333333', linewidths=0.7, zorder=6, alpha=0.85)

# ── 3. Anotar media ──────────────────────────────────────────────────
for i, tc in enumerate(tc_names):
    v = np.array(tc_flux_data[tc])
    py_mean = v.mean()
    n = len(v)
    y_top = max(v)
    y_ann = y_top + 20
    ax.annotate(f'$\\bar{{x}}$={py_mean:.0f}  (n={n})',
                xy=(positions[i], y_ann),
                ha='center', va='bottom', fontsize=7.5, fontweight='bold',
                color=TC_COLORS[tc],
                bbox=dict(boxstyle='round,pad=0.15', facecolor='white',
                          edgecolor='none', alpha=0.75))

# ── 4. Ejes y grilla ─────────────────────────────────────────────────
ax.set_xticks(positions)
ax.set_xticklabels(tc_names, fontsize=11, fontweight='bold')
ax.set_ylabel('Flujo vertical (mm/día)', fontsize=11.5, fontweight='bold')
ax.set_xlabel('Estación de monitoreo', fontsize=11, fontweight='bold')

ax.set_title('Flujos verticales entre río Cuncumén y acuífero\n'
             'Método Hatch–Amplitude por par de sensores  ·  Parámetros térmicos IDIEM  ·  Dic 2025 – Feb 2026',
             fontsize=11.5, fontweight='bold', pad=10, color='#1a1a1a',
             linespacing=1.6)

ax.yaxis.grid(True, alpha=0.45, color='#BBBBBB', linewidth=0.5, linestyle='--')
ax.xaxis.grid(False)
ax.set_axisbelow(True)
ax.set_xlim(0.4, len(tc_names) + 0.6)
ax.set_ylim(bottom=0)

ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# ── 5. Leyenda ────────────────────────────────────────────────────────
legend_items = [
    Line2D([0], [0], marker='D', color='w', markerfacecolor='white',
           markeredgecolor='#333333', markersize=6, markeredgewidth=1.0,
           label='Media ($\\bar{x}$)'),
    Line2D([0], [0], color='#222222', linewidth=1.8,
           label='Mediana'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='#888888',
           markeredgecolor='#333333', markersize=6, label='Sup–Int'),
    Line2D([0], [0], marker='s', color='w', markerfacecolor='#888888',
           markeredgecolor='#333333', markersize=6, label='Int–Inf'),
    Line2D([0], [0], marker='^', color='w', markerfacecolor='#888888',
           markeredgecolor='#333333', markersize=6, label='Sup–Inf'),
]
ax.legend(handles=legend_items, loc='upper center', fontsize=8.5,
          framealpha=0.90, edgecolor='#cccccc', fancybox=False,
          ncol=5)

# ── 6. Nota al pie ───────────────────────────────────────────────────
ax.text(0.99, -0.12,
        'Dirección: infiltración (río → acuífero)  |  '
        'Estimaciones por par: superficial–intermedio, intermedio–inferior, superficial–inferior  |  '
        'Elaboración propia',
        transform=ax.transAxes, fontsize=7.5, ha='right', va='top',
        color='#777777', style='italic')

fig.tight_layout()

# ── 7. Exportar ───────────────────────────────────────────────────────
out_png = IMG_DIR / 'boxplot_flujos_verticales_tabla5.png'
fig.savefig(out_png, dpi=300, bbox_inches='tight', facecolor='white')
print(f"✔ Boxplot exportado: {out_png}")
plt.close(fig)
