#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Actualiza SOLO la sección boxplot de celda 51:
 - Sin grilla (ax.grid(False) explícito)
 - Puntos individuales con jitter
 - Gradiente celeste Flow v3 (de claro a oscuro)
"""
import json
from pathlib import Path

NB_PATH = Path(__file__).resolve().parent.parent / "notebooks" / "05A_datos_terreno.ipynb"
IDX = 50  # celda 51 (0-based)

# Separador que divide boxplot de mapa SIG
SEPARATOR = "# ══════════════════════════════════════════════════════════════════════════\n# MAPA SIG"

# ── Nueva sección boxplot (hasta el separador MAPA SIG) ──────────────────
NEW_BOXPLOT = r'''# =============================================================================
# §18 BOXPLOT VERTICAL — TENDENCIA CENTRAL (MAD) — ESTILO FLOW V3
#     + MAPA SIG INTEGRADO
# =============================================================================
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ── Recopilar flujos MAD-filtrados por TC ─────────────────────────────────
boxplot_data_mad = {}
for pair_name, df_filt in filtered_series.items():
    tc = pair_name.split('_')[0]
    vals = df_filt['flux_hatch_amplitude_mm_day'].dropna().values
    if tc not in boxplot_data_mad:
        boxplot_data_mad[tc] = []
    boxplot_data_mad[tc].extend(vals.tolist())

# ── Estilo Flow v3: sans-serif, limpio, sin grilla ───────────────────────
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Calibri", "Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 9,
    "axes.labelsize": 10,
    "axes.titlesize": 11,
    "axes.edgecolor": "black",
    "axes.linewidth": 0.8,
    "axes.grid": False,
    "text.color": "black",
    "xtick.color": "black",
    "ytick.color": "black",
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})

fig, ax = plt.subplots(figsize=(10, 6))

tc_order = ['TC1', 'TC2', 'TC3', 'TC4', 'TC5']
data_list_f = [np.array(boxplot_data_mad.get(tc, [])) for tc in tc_order]
positions = np.arange(1, len(tc_order) + 1)

# ── Gradiente celeste Flow v3 (claro → oscuro) ──────────────────────────
_FLOW_CELESTE = ['#B3E5FC', '#81D4FA', '#4FC3F7', '#29B6F6', '#0288D1']
colors_box = _FLOW_CELESTE[:len(tc_order)]

# ── Boxplot VERTICAL, sin outliers ────────────────────────────────────────
bp = ax.boxplot(
    data_list_f, positions=positions, patch_artist=True, widths=0.55,
    showfliers=False,
    medianprops=dict(color='black', linewidth=1.8),
    whiskerprops=dict(color='black', linewidth=1.0),
    capprops=dict(color='black', linewidth=1.0),
    boxprops=dict(edgecolor='black', linewidth=1.0),
)

for patch, color in zip(bp['boxes'], colors_box):
    patch.set_facecolor(color)
    patch.set_alpha(0.65)

# ── Puntos individuales con jitter ────────────────────────────────────────
rng = np.random.default_rng(42)
for i, (tc, vals) in enumerate(zip(tc_order, data_list_f)):
    if len(vals) == 0:
        continue
    x_jitter = positions[i] + rng.normal(0, 0.08, size=len(vals))
    ax.scatter(
        x_jitter, vals,
        s=8, alpha=0.35, zorder=5,
        color=colors_box[i], edgecolors='black', linewidths=0.3,
    )

# ── Referencia MATLAB (diamantes) ─────────────────────────────────────────
for i, tc in enumerate(tc_order):
    ref = MATLAB_REFERENCE.get(tc, {})
    if ref:
        ax.scatter(positions[i], ref['mean'], marker='D', s=80, facecolors='none',
                   edgecolors='#01579B', linewidths=1.5, zorder=6,
                   label='Ref. MATLAB VFLUX2' if i == 0 else None)

# ── Anotaciones: med y ref MATLAB encima del bigote ──────────────────────
all_caps_hi = [bp['caps'][2*i+1].get_ydata()[0] for i in range(len(tc_order))]
all_caps_lo = [bp['caps'][2*i].get_ydata()[0] for i in range(len(tc_order))]
y_data_max = max(all_caps_hi)
y_data_min = min(min(all_caps_lo), 0)
y_range = y_data_max - y_data_min

ax.set_ylim(y_data_min - y_range * 0.05, y_data_max + y_range * 0.22)

for i, (tc, vals) in enumerate(zip(tc_order, data_list_f)):
    if len(vals) == 0:
        continue
    med = np.median(vals)
    hi_cap = all_caps_hi[i]
    ref = MATLAB_REFERENCE.get(tc, {})
    ref_str = f'\nMATLAB: {ref["mean"]}' if ref else ''

    ax.annotate(
        f'med = {med:.0f}{ref_str}',
        xy=(positions[i], hi_cap),
        xytext=(positions[i], hi_cap + y_range * 0.04),
        fontsize=8, ha='center', va='bottom',
        color='black',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                  alpha=0.9, edgecolor='#ccc', linewidth=0.5),
        arrowprops=dict(arrowstyle='-', color='#999', linewidth=0.5)
    )

# ── Etiquetas eje X: TC + USCS + n ───────────────────────────────────────
x_labels = []
for tc, vals in zip(tc_order, data_list_f):
    tp = THERMAL_PARAMS_LAB[tc]
    x_labels.append(f"{tc}\n({tp['USCS']})\nn = {len(vals)}")
ax.set_xticks(positions)
ax.set_xticklabels(x_labels, fontsize=9, fontweight='bold')

ax.set_ylabel('Flujo vertical $q$ [mm/día]', fontsize=10)
ax.set_title(
    'Distribución del Flujo Hatch-Amplitude — Tendencia Central (MAD)\n'
    'Río Cuncumén — Dic 2025 a Feb 2026 — sin outliers',
    fontsize=11, fontweight='bold', pad=10
)

ax.axhline(y=0, color='k', linestyle='-', linewidth=0.6, alpha=0.4)

# ── SIN GRILLA — borde completo (Flow v3: boxplot con marco) ─────────────
ax.grid(False)
for spine in ax.spines.values():
    spine.set_visible(True)
    spine.set_linewidth(0.8)
    spine.set_color('black')

ax.tick_params(axis='both', labelsize=8, direction='out', length=4)

# ── Leyenda ──────────────────────────────────────────────────────────────
legend_items = [
    mpatches.Patch(facecolor='#4FC3F7', alpha=0.65, edgecolor='k', linewidth=0.8,
                   label='Rango IQR (Q1–Q3)'),
    plt.Line2D([0], [0], color='k', linewidth=1.8, label='Mediana'),
    plt.Line2D([0], [0], marker='D', color='w', markerfacecolor='none',
               markeredgecolor='#01579B', markersize=8, markeredgewidth=1.5,
               label='Ref. MATLAB VFLUX2'),
    plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#4FC3F7',
               markeredgecolor='black', markersize=5, markeredgewidth=0.3,
               label='Observaciones individuales'),
]
ax.legend(handles=legend_items, loc='upper left', frameon=True,
          framealpha=0.9, edgecolor='#ccc', fontsize=8)

fig.tight_layout()

for ext in ('png', 'pdf'):
    fig.savefig(img_dir / f'boxplot_tendencia_central_informe.{ext}',
                dpi=300, bbox_inches='tight', facecolor='white', pad_inches=0.25)
print(f'✅ Boxplot vertical (MAD, Flow v3, gradiente celeste) → {img_dir}')
plt.show()

# ── Tabla resumen ─────────────────────────────────────────────────────────
print(f"\n{'='*92}")
print(f" RESUMEN ESTADÍSTICO — TENDENCIA CENTRAL (MAD, umbral {MAD_THRESHOLD}) ".center(92))
print(f"{'='*92}")
print(f"{'TC':<8} {'n':>5} {'n_orig':>7} {'Media':>10} {'Mediana':>10} "
      f"{'Q1':>10} {'Q3':>10} {'MAD':>10} {'MATLAB':>10}")
print(f"{'─'*92}")
for tc, vals in zip(tc_order, data_list_f):
    if len(vals) == 0:
        continue
    ref_m = MATLAB_REFERENCE.get(tc, {}).get('mean', np.nan)
    n_orig = len(boxplot_data.get(tc, []))
    mad_val = np.median(np.abs(vals - np.median(vals)))
    print(f"{tc:<8} {len(vals):>5} {n_orig:>7} {np.mean(vals):>10.1f} {np.median(vals):>10.1f} "
          f"{np.percentile(vals,25):>10.1f} {np.percentile(vals,75):>10.1f} "
          f"{mad_val:>10.1f} {ref_m:>10}")
print(f"\n  Filtrado: MAD (umbral={MAD_THRESHOLD}) + mediana móvil (ventana={SMOOTH_WINDOW})")
print(f"  Unidad: mm/día  |  Método: Hatch et al. (2006)  |  Ventana: 48 h, paso 12 h")


'''


def _to_source_lines(text):
    lines = text.split('\n')
    return [line + '\n' for line in lines[:-1]] + [lines[-1]]


def main():
    with open(NB_PATH, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    cell = nb['cells'][IDX]
    old_src = ''.join(cell['source'])

    # Encontrar dónde empieza MAPA SIG
    idx_sep = old_src.find("# " + "═" * 70 + "\n# MAPA SIG")
    if idx_sep < 0:
        # Buscar variante
        for line_i, line in enumerate(old_src.split('\n')):
            if 'MAPA SIG' in line and line.strip().startswith('#'):
                idx_sep = sum(len(l) + 1 for l in old_src.split('\n')[:max(0, line_i - 1)])
                break
    if idx_sep < 0:
        print("ERROR: No se encontró el separador MAPA SIG")
        return

    # Preservar la sección MAPA SIG intacta
    mapa_sig_src = old_src[idx_sep:]

    # Reemplazar solo la parte boxplot
    new_full = NEW_BOXPLOT.rstrip() + '\n\n\n' + mapa_sig_src

    cell['source'] = _to_source_lines(new_full)
    cell['outputs'] = []
    cell['execution_count'] = None

    with open(NB_PATH, 'w', encoding='utf-8') as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)

    print("✅ Celda 51 actualizada:")
    print("   → Gradiente celeste Flow v3")
    print("   → Puntos individuales con jitter")
    print("   → ax.grid(False) explícito")
    print("   → axes.grid: False en rcParams")
    print("   → Mapa SIG preservado")


if __name__ == "__main__":
    main()
