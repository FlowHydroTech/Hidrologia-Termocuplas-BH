"""
Actualización integral Flow v3 para celdas 49 y 51.

Celda 49 (series temporales):
  - Color celeste suave ÚNICO para todas las TCs (#4FC3F7)
  - Grilla visible gris (ambos ejes)
  - Marcadores sin relleno, borde pronunciado
  - TC1_int_inf: fallback si MAD elimina >90%

Celda 51 (boxplot + mapa SIG):
  - Popup boxplot VERTICAL (no horizontal)
  - Popup series limpia, estilo Flow
  - Solo tendencias centrales ajustadas a MATLAB
"""
import json
from pathlib import Path

NB = Path(r"c:\Users\cesar.godoy\Hidrologia-Termocuplas-BH\notebooks\05A_datos_terreno.ipynb")

# ══════════════════════════════════════════════════════════════════════════
# CELDA 49 — SERIES TEMPORALES
# ══════════════════════════════════════════════════════════════════════════
CELL49_CODE = r'''# =============================================================================
# §17 SERIES TEMPORALES — TENDENCIA CENTRAL (MAD, ESTILO FLOW V3)
# =============================================================================
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

# ── Estilo Flow v3: sans-serif, grilla suave ─────────────────────────────
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Calibri", "Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 9,
    "axes.labelsize": 10,
    "axes.titlesize": 11,
    "axes.edgecolor": "black",
    "axes.linewidth": 0.8,
    "axes.grid": True,
    "grid.color": "#c8c8c8",
    "grid.linewidth": 0.4,
    "grid.alpha": 0.7,
    "text.color": "black",
    "xtick.color": "black",
    "ytick.color": "black",
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
})

# Celeste suave único — Flow v3
_FLOW_CELESTE = '#4FC3F7'

_pair_dash = {'sup_int': '-', 'int_inf': '--', 'sup_inf': '-.'}
_pair_marker = {'sup_int': 'o', 'int_inf': 's', 'sup_inf': '^'}
_pair_lbl = {
    'sup_int': 'Sup → Int ($z_1$–$z_2$)',
    'int_inf': 'Int → Inf ($z_2$–$z_3$)',
    'sup_inf': 'Sup → Inf ($z_1$–$z_3$)'
}

MAD_THRESHOLD = 2.5
SMOOTH_WINDOW = 5

def mad_filter(values, threshold=MAD_THRESHOLD):
    """Filtrar outliers con MAD (Median Absolute Deviation)."""
    med = np.median(values)
    mad = np.median(np.abs(values - med))
    if mad < 1e-10:
        return np.ones(len(values), dtype=bool)
    mod_z = 0.6745 * np.abs(values - med) / mad
    return mod_z < threshold


# ── 1) Filtrado MAD + suavizado mediana móvil ────────────────────────────
filtered_series = {}
for pair_name, df_flux in flux_ts_results.items():
    df_valid = df_flux[df_flux['quality_flag'] == 0].copy()
    if len(df_valid) == 0 or 'flux_hatch_amplitude_mm_day' not in df_valid.columns:
        continue
    vals = df_valid['flux_hatch_amplitude_mm_day'].values
    mask_mad = mad_filter(vals, MAD_THRESHOLD)
    n_kept = mask_mad.sum()

    # Fallback: si MAD elimina >90%, relajar umbral progresivamente
    if n_kept < max(3, len(vals) * 0.10):
        for fallback_th in [3.5, 5.0]:
            mask_mad = mad_filter(vals, fallback_th)
            n_kept = mask_mad.sum()
            if n_kept >= 3:
                print(f"  ⚠ {pair_name}: MAD {MAD_THRESHOLD} eliminó todo → "
                      f"umbral relajado a {fallback_th} (n={n_kept})")
                break
        else:
            # Último recurso: usar todos los datos
            mask_mad = np.ones(len(vals), dtype=bool)
            print(f"  ⚠ {pair_name}: sin filtro MAD (datos muy dispersos, n={len(vals)})")

    df_filt = df_valid.loc[mask_mad].copy()
    df_filt['flux_smooth'] = (
        df_filt['flux_hatch_amplitude_mm_day']
        .rolling(window=SMOOTH_WINDOW, center=True, min_periods=1)
        .median()
    )
    filtered_series[pair_name] = df_filt

# ── 2) Diagnóstico ──────────────────────────────────────────────────────
print(f"\n{'Par':<25} {'Total':>6} {'Conserv':>7} {'Remov':>6} {'%Rem':>7}")
print(f"{'─'*55}")
for pn, df_flux in flux_ts_results.items():
    n_total = len(df_flux[df_flux['quality_flag'] == 0])
    n_filt = len(filtered_series.get(pn, pd.DataFrame()))
    pct_r = (n_total - n_filt) / max(n_total, 1) * 100
    print(f"{pn:<25} {n_total:>6} {n_filt:>7} {n_total - n_filt:>6} {pct_r:>6.1f}%")

# ── 3) Gráfico — ejes Y independientes, estilo Flow v3 ──────────────────
n_tcs = len(ACTIVE_TCS)
fig, axes = plt.subplots(n_tcs, 1, figsize=(14, 3.0 * n_tcs), sharex=False)
if n_tcs == 1:
    axes = [axes]

for ax_idx, (ax, tc_name) in enumerate(zip(axes, ACTIVE_TCS)):
    ref = MATLAB_REFERENCE.get(tc_name, {})
    tp = THERMAL_PARAMS_LAB[tc_name]

    for pair_name, df_filt in filtered_series.items():
        if tc_name not in pair_name:
            continue
        if len(df_filt) == 0:
            continue
        pt = pair_name.split('_', 1)[1]
        ax.plot(
            df_filt['datetime'], df_filt['flux_smooth'],
            linestyle=_pair_dash.get(pt, '-'),
            color=_FLOW_CELESTE, alpha=0.9,
            marker=_pair_marker.get(pt, 'o'),
            markersize=5, linewidth=1.3,
            label=_pair_lbl.get(pt, pt),
            markerfacecolor='none',
            markeredgewidth=1.0, markeredgecolor=_FLOW_CELESTE
        )

    # Banda referencia MATLAB
    if ref:
        ax.axhspan(ref['min'], ref['max'], alpha=0.07, color='#555555', zorder=0)
        ax.axhline(y=ref['mean'], color='#888888', linestyle='--',
                    linewidth=1.0, alpha=0.6, zorder=1,
                    label=f'MATLAB prom: {ref["mean"]} mm/d')

    ax.axhline(y=0, color='k', linestyle='-', linewidth=0.5, alpha=0.3)

    # Grilla suave gris (horizontal + vertical) — Flow v3
    ax.grid(True, axis='both', color='#c8c8c8', linewidth=0.4, alpha=0.7)
    ax.set_axisbelow(True)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(0.8)
    ax.spines['bottom'].set_linewidth(0.8)

    ax.set_ylabel('$q$ [mm/día]', fontsize=10)
    alpha_e = tp['alpha_e']
    title_str = (f'{tc_name} — {tp["USCS"]} | '
                 f'$\\alpha_e$ = {alpha_e:.2e} m²/s')
    if ref:
        title_str += f' | ref MATLAB: {ref["mean"]} mm/d'
    ax.set_title(title_str, fontsize=9, fontweight='bold', pad=5, loc='left')

    ax.legend(loc='upper right', fontsize=8, frameon=True,
              framealpha=0.92, edgecolor='#ccc', ncol=2, handlelength=2.5)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
    ax.tick_params(axis='both', labelsize=8, direction='out', length=4)

axes[-1].set_xlabel('Fecha', fontsize=10)

fig.suptitle(
    'Series Temporales de Flujo — Tendencia Central (MAD)\n'
    'Río Cuncumén — Dic 2025 – Feb 2026 — Ventanas deslizantes 48 h',
    fontsize=11, fontweight='bold', y=1.01
)
fig.tight_layout()

for ext in ('png', 'pdf'):
    fig.savefig(img_dir / f'series_tendencia_central_informe.{ext}',
                dpi=300, bbox_inches='tight', facecolor='white', pad_inches=0.2)
print(f'\n✅ Series tendencia central (MAD, Flow v3) → {img_dir}')
plt.show()
'''

# ══════════════════════════════════════════════════════════════════════════
# CELDA 51 — BOXPLOT + MAPA SIG (solo se modifica la parte del mapa popup)
# ══════════════════════════════════════════════════════════════════════════
# Leemos la celda 51 y reemplazamos:
#  1) El boxplot del popup: orientation='h' → vertical
#  2) Limpieza estilo Flow en popups

with open(NB, encoding="utf-8") as f:
    nb = json.load(f)

# ── Actualizar celda 49 ──────────────────────────────────────────────────
cell49 = nb["cells"][48]
cell49["source"] = [line + "\n" for line in CELL49_CODE.strip().split("\n")]
cell49["outputs"] = []
cell49["execution_count"] = None

# ── Actualizar celda 51: popup boxplot vertical + cleaner series ─────────
cell51 = nb["cells"][50]
src51 = "".join(cell51["source"])

# 1) Cambiar boxplot popup de horizontal a vertical
src51 = src51.replace(
    "x=vb, name=_pair_lbl2.get(pt_b, pt_b),",
    "y=vb, name=_pair_lbl2.get(pt_b, pt_b),"
)
src51 = src51.replace(
    "boxpoints=False, orientation='h',",
    "boxpoints=False, orientation='v',"
)
src51 = src51.replace(
    "hovertemplate='%{x:.0f} mm/d<extra></extra>'))",
    "hovertemplate='%{y:.0f} mm/d<extra></extra>'))"
)

# 2) Ajustar ejes del boxplot popup (x↔y)
src51 = src51.replace(
    "xaxis=dict(title=dict(text='mm/d', font=dict(size=9)), tickfont=dict(size=8), range=_xrng),\n        yaxis=dict(tickfont=dict(size=8)),",
    "yaxis=dict(title=dict(text='mm/d', font=dict(size=9)), tickfont=dict(size=8), range=_xrng),\n        xaxis=dict(tickfont=dict(size=8)),"
)

# 3) Usar paleta celeste suave uniforme en popup boxplot
src51 = src51.replace(
    "marker_color=color, boxmean=True, opacity=0.8,",
    "marker_color='#4FC3F7', boxmean=True, opacity=0.8,"
)

# 4) Series en popup: color celeste uniforme
src51 = src51.replace(
    "_pair_col2 = {'sup_int':'#0072BD','int_inf':'#D95319','sup_inf':'#EDB120'}",
    "_pair_col2 = {'sup_int':'#4FC3F7','int_inf':'#29B6F6','sup_inf':'#0288D1'}"
)

# 5) Boxplot estático: color celeste uniforme (ya tiene gradiente, cambiamos)
src51 = src51.replace(
    "_FLOW_CELESTE = ['#B3E5FC', '#81D4FA', '#4FC3F7', '#29B6F6', '#0288D1']",
    "_FLOW_CELESTE = ['#4FC3F7', '#4FC3F7', '#4FC3F7', '#4FC3F7', '#4FC3F7']"
)

cell51["source"] = src51.splitlines(keepends=True)
if cell51["source"] and not cell51["source"][-1].endswith("\n"):
    cell51["source"][-1] += "\n"
cell51["outputs"] = []
cell51["execution_count"] = None

with open(NB, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("✅ Celdas 49 y 51 actualizadas:")
print("   Celda 49 — Series temporales:")
print("     → Celeste suave único (#4FC3F7) para TODAS las TCs")
print("     → Grilla gris visible (H+V)")
print("     → Marcadores sin relleno, borde pronunciado")
print("     → TC1_int_inf: fallback si MAD elimina >90%")
print("   Celda 51 — Boxplot + Mapa SIG:")
print("     → Popup boxplot VERTICAL (era horizontal)")
print("     → Popup series con paleta celeste Flow")
print("     → Boxplot estático celeste uniforme")
