"""
Actualizar notebook 05A_datos_terreno.ipynb:
1. Cell 49 (series temporales): ejes X e Y compartidos (misma escala)
2. Cell 51 (boxplot+mapa): separar en 2 celdas, quitar "outliers", fix X spacing, exportar tabla
"""
import json, copy, uuid

NB = r"c:\Users\cesar.godoy\Hidrologia-Termocuplas-BH\notebooks\05A_datos_terreno.ipynb"

with open(NB, encoding="utf-8") as f:
    nb = json.load(f)

cells = nb["cells"]

# ── Localizar celdas ──────────────────────────────────────────────────
idx49 = idx51 = None
for i, c in enumerate(cells):
    src = "".join(c.get("source", []))
    if "§17 SERIES TEMPORALES" in src:
        idx49 = i
    if "§18 BOXPLOT VERTICAL" in src:
        idx51 = i

assert idx49 is not None, "No encontré celda §17"
assert idx51 is not None, "No encontré celda §18"
print(f"Celda 49 (series) en idx={idx49}, celda 51 (boxplot+mapa) en idx={idx51}")

# ══════════════════════════════════════════════════════════════════════════
# 1) NUEVA CELDA 49: Series temporales con ejes X e Y compartidos
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

# ── 3) Determinar rango global X (fechas) e Y (flujo) ───────────────────
_all_dates = []
_all_fluxes = []
for pair_name, df_filt in filtered_series.items():
    if len(df_filt) > 0:
        _all_dates.extend(df_filt['datetime'].tolist())
        _all_fluxes.extend(df_filt['flux_smooth'].dropna().tolist())

# Incluir rangos MATLAB en los límites Y
for tc_name in ACTIVE_TCS:
    ref = MATLAB_REFERENCE.get(tc_name, {})
    if ref:
        _all_fluxes.extend([ref['min'], ref['max']])

_global_xmin = min(_all_dates)
_global_xmax = max(_all_dates)
_global_ymin = min(_all_fluxes)
_global_ymax = max(_all_fluxes)
_y_range = _global_ymax - _global_ymin
_global_ymin -= _y_range * 0.07
_global_ymax += _y_range * 0.07

print(f"\n  Rango X: {_global_xmin} → {_global_xmax}")
print(f"  Rango Y: {_global_ymin:.0f} → {_global_ymax:.0f} mm/día")

# ── 4) Gráfico — ejes X e Y compartidos, estilo Flow v3 ─────────────────
n_tcs = len(ACTIVE_TCS)
fig, axes = plt.subplots(n_tcs, 1, figsize=(14, 3.0 * n_tcs), sharex=True)
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

    # Ejes compartidos: misma escala Y para todos los paneles
    ax.set_xlim(_global_xmin, _global_xmax)
    ax.set_ylim(_global_ymin, _global_ymax)

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

    # Ocultar etiquetas X de paneles superiores (sharex se encarga, pero reforzar)
    if ax_idx < n_tcs - 1:
        ax.tick_params(axis='x', labelbottom=False)

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
print(f'\n✅ Series tendencia central (MAD, Flow v3, ejes compartidos) → {img_dir}')
plt.show()
'''

# ══════════════════════════════════════════════════════════════════════════
# 2) NUEVA CELDA 51-A: Solo BOXPLOT + tabla resumen exportada
# ══════════════════════════════════════════════════════════════════════════
CELL51A_CODE = r'''# =============================================================================
# §18 BOXPLOT VERTICAL — TENDENCIA CENTRAL (MAD) — ESTILO FLOW V3
# =============================================================================
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

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

# ── Celeste uniforme Flow v3 ─────────────────────────────────────────────
colors_box = ['#4FC3F7'] * len(tc_order)

# ── Boxplot VERTICAL ─────────────────────────────────────────────────────
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

# ── Etiquetas eje X: TC + USCS + n — sin espacio extra ───────────────────
x_labels = []
for tc, vals in zip(tc_order, data_list_f):
    tp = THERMAL_PARAMS_LAB[tc]
    x_labels.append(f"{tc}\n({tp['USCS']})\nn = {len(vals)}")
ax.set_xticks(positions)
ax.set_xticklabels(x_labels, fontsize=9, fontweight='bold')
ax.tick_params(axis='x', pad=2)  # Reducir espacio entre eje X y etiquetas

ax.set_ylabel('Flujo vertical $q$ [mm/día]', fontsize=10)
ax.set_title(
    'Distribución del Flujo Hatch-Amplitude — Tendencia Central (MAD)\n'
    'Río Cuncumén — Dic 2025 a Feb 2026',
    fontsize=11, fontweight='bold', pad=10
)

ax.axhline(y=0, color='k', linestyle='-', linewidth=0.6, alpha=0.4)

# ── SIN GRILLA — borde completo (Flow v3: boxplot con marco) ─────────────
ax.grid(False)
for spine in ax.spines.values():
    spine.set_visible(True)
    spine.set_linewidth(0.8)
    spine.set_color('black')

ax.tick_params(axis='y', labelsize=8, direction='out', length=4)

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
print(f'✅ Boxplot vertical (MAD, Flow v3, celeste uniforme) → {img_dir}')
plt.show()

# ── Tabla resumen (consola) ───────────────────────────────────────────────
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

# ── Exportar tabla en formato CSV para pegar en informe ───────────────────
_rows = []
for tc, vals in zip(tc_order, data_list_f):
    if len(vals) == 0:
        continue
    ref_m = MATLAB_REFERENCE.get(tc, {}).get('mean', np.nan)
    n_orig = len(boxplot_data.get(tc, []))
    mad_val = np.median(np.abs(vals - np.median(vals)))
    _rows.append({
        'TC': tc,
        'USCS': THERMAL_PARAMS_LAB[tc]['USCS'],
        'n': len(vals),
        'n_orig': n_orig,
        'Media [mm/d]': round(np.mean(vals), 1),
        'Mediana [mm/d]': round(np.median(vals), 1),
        'Q1 [mm/d]': round(np.percentile(vals, 25), 1),
        'Q3 [mm/d]': round(np.percentile(vals, 75), 1),
        'MAD': round(mad_val, 1),
        'MATLAB [mm/d]': ref_m,
    })

df_resumen = pd.DataFrame(_rows)

# Guardar CSV
_csv_path = img_dir / 'resumen_estadistico_tendencia_central_MAD.csv'
df_resumen.to_csv(_csv_path, index=False, encoding='utf-8-sig')
print(f'\n✅ Tabla resumen exportada → {_csv_path.name}')

# Guardar Excel
_xlsx_path = img_dir / 'resumen_estadistico_tendencia_central_MAD.xlsx'
df_resumen.to_excel(_xlsx_path, index=False, sheet_name='Resumen MAD')
print(f'✅ Tabla resumen Excel → {_xlsx_path.name}')

# Mostrar tabla formateada
print(f'\n  Tabla lista para copiar/pegar:\n')
print(df_resumen.to_string(index=False))
'''

# ══════════════════════════════════════════════════════════════════════════
# 3) NUEVA CELDA 51-B: Solo MAPA SIG (satélite por defecto)
# ══════════════════════════════════════════════════════════════════════════
CELL51B_CODE = r'''# =============================================================================
# §19 MAPA SIG — TENDENCIA CENTRAL MAD (satélite por defecto)
# =============================================================================
import json as _json
import numpy as np
import plotly.graph_objects as go
import folium, folium.plugins
from pyproj import Transformer
from IPython.display import display, HTML

_tf2 = Transformer.from_crs('EPSG:32719', 'EPSG:4326', always_xy=True)
coords_wgs84_v2 = {}
for _st, _utm in STATION_COORDS_UTM.items():
    _lon, _lat = _tf2.transform(_utm['easting'], _utm['northing'])
    coords_wgs84_v2[_st] = {'lat': _lat, 'lon': _lon}

_pos_short2 = {'surface': 'sup', 'intermediate': 'int', 'deep': 'inf'}
_pos_dash2 = {'surface': 'solid', 'intermediate': 'dash', 'deep': 'dot'}
_tc_hex_p2 = {'TC1':'#1f77b4','TC2':'#ff7f0e','TC3':'#e377c2',
              'TC4':'#2ca02c','TC5':'#d62728'}
_pair_col2 = {'sup_int':'#4FC3F7','int_inf':'#29B6F6','sup_inf':'#0288D1'}
_pair_lbl2 = {'sup_int':'sup→int','int_inf':'int→inf','sup_inf':'sup→inf'}
_SMAP2 = {
    'TC1': {'surface':0.00,'intermediate':0.28,'deep':0.56},
    'TC2': {'surface':0.00,'intermediate':0.20,'deep':0.40},
    'TC3': {'surface':0.00,'intermediate':0.20,'deep':0.40},
    'TC4': {'surface':0.00,'intermediate':0.28,'deep':0.56},
    'TC5': {'surface':0.00,'intermediate':0.28,'deep':0.56},
}

_mask2 = (df_aligned['fecha'] >= cutoff_start) & (df_aligned['fecha'] <= cutoff_end)
_df_pop2 = df_aligned[_mask2].copy()

_JS_TMPL2 = """<script>
(function(){
  var FR=__DATA__;
  var pk=Object.keys(FR);
  function pct(a,p){var s=a.slice().sort(function(x,y){return x-y});
    var i=p/100*(s.length-1),lo=Math.floor(i),hi=Math.ceil(i);
    return lo===hi?s[lo]:s[lo]+(i-lo)*(s[hi]-s[lo]);}
  function upd(xMin,xMax){
    var tb=document.getElementById("stats-body");if(!tb)return;
    tb.innerHTML="";
    var ri=document.getElementById("rng-info");
    if(ri){ri.textContent=xMin&&xMax
      ?"Ventana: "+new Date(xMin).toLocaleDateString("es-CL")+" \\u2013 "+new Date(xMax).toLocaleDateString("es-CL")
      :"Ventana: serie completa";}
    var all=[];
    pk.forEach(function(k){
      var dt=FR[k].dt,v=FR[k].flux,f=[];
      for(var i=0;i<dt.length;i++){if((!xMin||dt[i]>=xMin)&&(!xMax||dt[i]<=xMax))f.push(v[i]);}
      if(!f.length)return; all=all.concat(f);
      var q1=pct(f,25),md=pct(f,50),q3=pct(f,75);
      var mn=f.reduce(function(a,b){return a+b},0)/f.length;
      tb.innerHTML+="<tr><td style='color:"+FR[k].color+"'>"+FR[k].label+"</td>"
        +"<td>"+q1.toFixed(0)+"</td><td style='font-weight:600'>"+md.toFixed(0)+"</td>"
        +"<td>"+q3.toFixed(0)+"</td><td>"+mn.toFixed(0)+(mn>0?" \\u2193":" \\u2191")
        +"</td><td>"+f.length+"</td></tr>";
    });
    if(all.length){
      var tq1=pct(all,25),tmd=pct(all,50),tq3=pct(all,75);
      var tmn=all.reduce(function(a,b){return a+b},0)/all.length;
      tb.innerHTML+="<tr style='border-top:2px solid #333;font-weight:700'><td>TOTAL</td>"
        +"<td>"+tq1.toFixed(0)+"</td><td>"+tmd.toFixed(0)+"</td>"
        +"<td>"+tq3.toFixed(0)+"</td><td>"+tmn.toFixed(0)+"</td>"
        +"<td>"+all.length+"</td></tr>";}
  }
  upd(null,null);
  var fc=document.getElementById("flux-chart");
  if(fc)fc.on("plotly_relayout",function(ev){
    var xMin=ev["xaxis.range[0]"]||(ev["xaxis.range"]&&ev["xaxis.range"][0])||null;
    var xMax=ev["xaxis.range[1]"]||(ev["xaxis.range"]&&ev["xaxis.range"][1])||null;
    if(ev["xaxis.autorange"]){xMin=null;xMax=null;}
    upd(xMin,xMax);
  });
})();</script>"""


def _build_popup_mad(tc):
    """Popup HTML con datos MAD-filtrados."""
    utm_c = STATION_COORDS_UTM[tc]
    color = _tc_hex_p2.get(tc, '#555')
    tp = THERMAL_PARAMS_LAB[tc]
    tc_map = TC_CONFIG[tc]
    ds = sorted(set(_SMAP2[tc].values()))
    ds_str = ' / '.join(f'{d*100:.0f}' for d in ds) + ' cm'

    fig_t = go.Figure()
    for pos in ['surface', 'intermediate', 'deep']:
        col = tc_map[pos]
        dcm = depths_m[col] * 100
        d = _df_pop2.dropna(subset=[col])
        st = max(1, len(d) // 200)
        fig_t.add_trace(go.Scatter(
            x=d.iloc[::st]['fecha'], y=d.iloc[::st][col], mode='lines',
            name=f'{_pos_short2[pos]} ({dcm:.0f}cm)',
            line=dict(width=1.5, dash=_pos_dash2[pos]),
            hovertemplate='%{x|%d-%b %H:%M}<br>%{y:.1f}°C<extra></extra>'))
    fig_t.update_layout(
        title=dict(text='Temperatura', font=dict(size=12)),
        xaxis=dict(showgrid=False, tickfont=dict(size=8), tickformat='%d-%b'),
        yaxis=dict(title=dict(text='°C', font=dict(size=9)), tickfont=dict(size=8)),
        template='plotly_white', height=170, width=480,
        margin=dict(l=35, r=8, t=28, b=28),
        legend=dict(orientation='h', font=dict(size=8), y=1.15, x=0.5, xanchor='center'))
    ht = fig_t.to_html(include_plotlyjs=False, full_html=False,
                        config={'displayModeBar': False})

    fig_f = go.Figure()
    raw = {}
    has_f = False
    for pn in sorted(filtered_series.keys()):
        if tc not in pn:
            continue
        df_filt = filtered_series[pn]
        if len(df_filt) == 0:
            continue
        has_f = True
        pt = pn.split('_', 1)[1]
        raw[pt] = {
            'dt': df_filt['datetime'].dt.strftime('%Y-%m-%dT%H:%M:%S').tolist(),
            'flux': df_filt['flux_smooth'].round(2).tolist(),
            'label': _pair_lbl2.get(pt, pt),
            'color': _pair_col2.get(pt, '#888')}
        sf = max(1, len(df_filt) // 150)
        fig_f.add_trace(go.Scatter(
            x=df_filt.iloc[::sf]['datetime'],
            y=df_filt.iloc[::sf]['flux_smooth'],
            mode='lines+markers', name=_pair_lbl2.get(pt, pt),
            marker=dict(size=3),
            line=dict(width=1.5, color=_pair_col2.get(pt, '#888')),
            hovertemplate='%{x|%d-%b %H:%M}<br>%{y:.0f} mm/d<extra></extra>'))
    ref = MATLAB_REFERENCE.get(tc, {})
    if ref and has_f:
        fig_f.add_hrect(y0=ref['min'], y1=ref['max'], fillcolor='gray', opacity=0.12, line_width=0)
        fig_f.add_hline(y=ref['mean'], line_dash='dash', line_color='gray', line_width=1,
                        annotation_text=f'MATLAB {ref["mean"]}',
                        annotation_position='top right', annotation_font_size=8)
    fig_f.update_layout(
        title=dict(text='Flujo Hatch-Amp — Tendencia Central (MAD)', font=dict(size=11)),
        xaxis=dict(rangeslider=dict(visible=True, thickness=0.12),
                   rangeselector=dict(buttons=[
                       dict(count=3, label='3d', step='day', stepmode='backward'),
                       dict(count=7, label='1sem', step='day', stepmode='backward'),
                       dict(count=14, label='2sem', step='day', stepmode='backward'),
                       dict(step='all', label='Todo')], font=dict(size=8)),
                   showgrid=False, tickfont=dict(size=8), tickformat='%d-%b'),
        yaxis=dict(title=dict(text='mm/d', font=dict(size=9)), tickfont=dict(size=8)),
        template='plotly_white', height=230, width=480,
        margin=dict(l=40, r=8, t=35, b=25),
        legend=dict(orientation='h', font=dict(size=7), y=1.18, x=0.5, xanchor='center'))
    hf = fig_f.to_html(include_plotlyjs=False, full_html=False,
                        config={'displayModeBar': False}, div_id='flux-chart')

    fig_b = go.Figure()
    _bp_all = []
    for pn_b in sorted(filtered_series.keys()):
        if tc not in pn_b:
            continue
        df_b = filtered_series[pn_b]
        if len(df_b) == 0:
            continue
        pt_b = pn_b.split('_', 1)[1]
        vb = df_b['flux_hatch_amplitude_mm_day'].dropna().values
        if len(vb) > 0:
            _bp_all.extend(vb.tolist())
            fig_b.add_trace(go.Box(
                y=vb, name=_pair_lbl2.get(pt_b, pt_b),
                marker_color='#4FC3F7', boxmean=True, opacity=0.8,
                boxpoints=False, orientation='v',
                hovertemplate='%{y:.0f} mm/d<extra></extra>'))
    _xrng = None
    if _bp_all:
        _bpa = np.array(_bp_all)
        _q1b, _q3b = np.percentile(_bpa, 25), np.percentile(_bpa, 75)
        _iqrb = _q3b - _q1b
        _xrng = [max(_bpa.min(), _q1b - 1.5*_iqrb) - _iqrb*0.15,
                 min(_bpa.max(), _q3b + 1.5*_iqrb) + _iqrb*0.15]
    fig_b.update_layout(
        title=dict(text='Boxplot (tendencia central MAD)', font=dict(size=11)),
        yaxis=dict(title=dict(text='mm/d', font=dict(size=9)), tickfont=dict(size=8), range=_xrng),
        xaxis=dict(tickfont=dict(size=8)),
        template='plotly_white', height=160, width=480,
        margin=dict(l=40, r=8, t=28, b=28), showlegend=False)
    hb = fig_b.to_html(include_plotlyjs=False, full_html=False,
                        config={'displayModeBar': False})

    ref_h = ''
    if ref:
        ref_h = (f'<div style="font-size:9px;color:#666;margin-top:2px;">'
                 f'Ref MATLAB: {ref["min"]}–{ref["max"]} mm/d (prom {ref["mean"]})</div>')
    js = _JS_TMPL2.replace('__DATA__', _json.dumps(raw))

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
body{{font-family:'Calibri','Segoe UI',Arial,sans-serif;margin:0;padding:8px;background:#fefefe;color:#222}}
.hdr{{display:flex;align-items:center;gap:8px;border-bottom:3px solid {color};padding-bottom:4px;margin-bottom:5px}}
.hdr h3{{margin:0;color:{color};font-size:14px}}
.badge{{background:{color};color:#fff;font-size:9px;padding:2px 6px;border-radius:10px}}
.info{{font-size:10px;color:#555;line-height:1.4;margin-bottom:4px}}
.info b{{color:#333}}
.chart-box{{border:1px solid #e8e8e8;border-radius:4px;padding:1px;margin-bottom:4px;background:#fff}}
.mc{{font-size:10px;margin-top:2px}}
.mc table{{width:100%;border-collapse:collapse}}
.mc th{{background:#2c3e50;color:white;padding:2px 5px;font-size:9px;text-align:center}}
.mc td{{padding:1px 5px;border-bottom:1px solid #eee;text-align:center;font-size:10px}}
.mc td:first-child{{text-align:left}}
#rng-info{{text-align:center;font-size:10px;color:#777;margin:2px 0 4px;background:#f8f9fa;border-radius:4px;padding:3px}}
</style></head><body>
<div class="hdr"><h3>\U0001f4cd {tc}</h3><span class="badge">{tp['USCS']}</span></div>
<div class="info">
  <b>UTM 19S:</b> {utm_c['easting']}E, {utm_c['northing']}N &nbsp;|&nbsp;
  <b>Prof:</b> {ds_str}<br>
  <b>IDIEM:</b> \u03bb={tp['lambda_sediment']:.3f} W/m\u00b7K |
  C={tp['C_sediment']/1e6:.3f} MJ/m\u00b3\u00b7K |
  \u03b1={tp['alpha_e']:.2e} m\u00b2/s
</div>
<div class="chart-box">{ht}</div>
<div class="chart-box">{hf}</div>
<div id="rng-info">Ventana: serie completa \u2014 mueva el slider o use botones</div>
<div class="chart-box">{hb}</div>
<div class="mc">
  <b>Flujo Hatch-Amp (mm/d) \u2014 tendencia central MAD:</b>
  <table><thead><tr>
    <th>Par</th><th>Q1</th><th>Mediana</th><th>Q3</th><th>Promedio</th><th>n</th>
  </tr></thead>
  <tbody id="stats-body"></tbody></table>
  {ref_h}
</div>
{js}
</body></html>"""


tc_list2 = list(STATION_COORDS_UTM.keys())
clat2 = np.mean([coords_wgs84_v2[t]['lat'] for t in tc_list2])
clon2 = np.mean([coords_wgs84_v2[t]['lon'] for t in tc_list2])

m2 = folium.Map(location=[clat2, clon2], zoom_start=14, tiles=None, control_scale=True)
folium.TileLayer(
    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attr='Esri', name='Satélite ESRI', max_zoom=19, show=True).add_to(m2)
folium.TileLayer(
    tiles='https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
    attr='OpenTopoMap', name='Topográfico', show=False).add_to(m2)
folium.TileLayer(
    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
    attr='Esri Labels', name='Etiquetas', overlay=True).add_to(m2)

for st2, wgs2 in coords_wgs84_v2.items():
    html_pop2 = _build_popup_mad(st2)
    iframe2 = folium.IFrame(html=html_pop2, width=520, height=800)
    popup2 = folium.Popup(iframe2, max_width=530)
    folium.Marker(
        location=[wgs2['lat'], wgs2['lon']], popup=popup2,
        tooltip=f"{st2} ({THERMAL_PARAMS_LAB[st2]['USCS']}) — MAD filtrado",
        icon=folium.Icon(color='red', icon='thermometer-half', prefix='fa')
    ).add_to(m2)

ordered2 = ['TC5', 'TC4', 'TC3', 'TC2', 'TC1']
folium.PolyLine(
    [[coords_wgs84_v2[s]['lat'], coords_wgs84_v2[s]['lon']]
     for s in ordered2 if s in coords_wgs84_v2],
    color='cyan', weight=3, opacity=0.7,
    dash_array='10', tooltip='Perfil del río').add_to(m2)

folium.plugins.MeasureControl(position='bottomleft').add_to(m2)
folium.plugins.Fullscreen().add_to(m2)
folium.plugins.MiniMap(toggle_display=True).add_to(m2)
folium.LayerControl().add_to(m2)

map_path2 = img_dir / 'panel_sig_tendencia_central_mad.html'
m2.save(str(map_path2))
print(f'\n✅ Mapa SIG (MAD, satélite por defecto): {map_path2.name}')
print(f'   → {map_path2}')
display(m2)
'''

# ══════════════════════════════════════════════════════════════════════════
# APLICAR CAMBIOS AL NOTEBOOK
# ══════════════════════════════════════════════════════════════════════════
def source_lines(code):
    """Convertir código a lista de líneas con \n."""
    lines = code.split('\n')
    return [l + '\n' for l in lines[:-1]] + ([lines[-1]] if lines[-1] else [])

def make_code_cell(source_code):
    """Crear una celda de código nueva."""
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source_lines(source_code)
    }

def make_markdown_cell(source_text):
    """Crear una celda markdown."""
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": source_lines(source_text)
    }

# 1) Reemplazar celda 49 (series temporales → ejes compartidos)
cells[idx49]["source"] = source_lines(CELL49_CODE)
cells[idx49]["outputs"] = []
cells[idx49]["execution_count"] = None
print("✓ Celda 49 actualizada (ejes compartidos)")

# 2) Reemplazar celda 51 con SOLO boxplot + tabla exportada
cells[idx51]["source"] = source_lines(CELL51A_CODE)
cells[idx51]["outputs"] = []
cells[idx51]["execution_count"] = None
print("✓ Celda 51 → solo Boxplot + tabla exportada")

# 3) Insertar markdown separador + nueva celda mapa SIG DESPUÉS de celda 51
md_sep = make_markdown_cell(
    "## §19 — Mapa SIG Interactivo — Tendencia Central MAD\n\n"
    "Mapa satelital con popups interactivos por estación "
    "(series de temperatura, flujo y boxplot)."
)
code_mapa = make_code_cell(CELL51B_CODE)

cells.insert(idx51 + 1, md_sep)
cells.insert(idx51 + 2, code_mapa)
print("✓ Celda mapa SIG insertada como nueva celda separada")

# Guardar
with open(NB, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print(f"\n✅ Notebook guardado. Total celdas: {len(cells)}")
print("   → Celda 49: series con ejes X/Y compartidos")
print("   → Celda 51: boxplot (sin 'outliers', X axis ajustado, tabla CSV/XLSX)")
print("   → Celda 52: markdown separador")
print("   → Celda 53: mapa SIG (satélite por defecto)")
