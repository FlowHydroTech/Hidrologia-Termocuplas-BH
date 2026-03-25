#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Actualiza celdas 48-51 del notebook 05A_datos_terreno.ipynb:
  - §17 Series Temporales Tendencia Central → MAD + publicación (ejes Y indep.)
  - §18 Boxplot Vertical Tendencia Central → MAD + mejores etiquetas + sin grilla
  + Mapa SIG con popup MAD-filtrado
"""
import json
from pathlib import Path

NB_PATH = Path(__file__).resolve().parent.parent / "notebooks" / "05A_datos_terreno.ipynb"

# ── Índices 0-based de las celdas a reemplazar ──────────────────────────
# 47 = md §17,  48 = code series,  49 = md §18,  50 = code boxplot+mapa
IDX_MD17  = 47
IDX_CODE_SERIES = 48
IDX_MD18  = 49
IDX_CODE_BOXPLOT = 50

# ═══════════════════════════════════════════════════════════════════════════
# NUEVA CELDA MARKDOWN §17
# ═══════════════════════════════════════════════════════════════════════════
SRC_MD17 = [
    "---\n",
    "## 17. Series Temporales — Tendencia Central (Publicación)\n",
    "\n",
    "Filtrado robusto mediante **MAD** (*Median Absolute Deviation*, umbral = 2.5σ modificado) con suavizado mediana móvil (ventana = 5 puntos ≈ 60 h).  \n",
    "\n",
    "**¿Por qué MAD y no IQR?** Para distribuciones asimétricas (como los flujos hidrológicos calculados con Hatch), la MAD es más robusta:\n",
    "- **IQR** (usado en §17 anterior): elimina valores fuera de Q1−1.5·IQR / Q3+1.5·IQR, pero en distribuciones asimétricas el rango permitido puede ser demasiado amplio, dejando pasar picos espurios.\n",
    "- **MAD**: mide la desviación absoluta respecto a la *mediana*, y su Z-modificado (0.6745·|x−med|/MAD) es resistente al sesgo. Con umbral 2.5, retiene ~99% de datos en distribución normal pero es más agresivo con outliers en colas pesadas.\n",
    "\n",
    "El resultado muestra la **tendencia central real** del flujo, adecuada para comparación con MATLAB.  \n",
    "Cada TC mantiene **eje Y independiente** (publicación — consistente con §16)."
]

# ═══════════════════════════════════════════════════════════════════════════
# NUEVA CELDA CÓDIGO — SERIES TEMPORALES TENDENCIA CENTRAL (PUBLICACIÓN)
# ═══════════════════════════════════════════════════════════════════════════
SRC_SERIES = r'''# =============================================================================
# §17 SERIES TEMPORALES — TENDENCIA CENTRAL (MAD, PUBLICACIÓN)
# Filtrado: MAD (Median Absolute Deviation), umbral = 2.5
# Suavizado: mediana móvil, ventana = 5 puntos (~60 h)
# Ejes Y independientes por TC (máxima resolución visual)
# =============================================================================
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "figure.dpi": 150,
    "savefig.dpi": 300,
})

_tc_hex = {
    'TC1': '#1f77b4', 'TC2': '#ff7f0e', 'TC3': '#2ca02c',
    'TC4': '#9467bd', 'TC5': '#d62728'
}
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
    """Filtrar outliers usando MAD (Median Absolute Deviation).
    modified_z = 0.6745 · |x - mediana| / MAD
    Más robusto que IQR para distribuciones asimétricas.
    """
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
    df_filt = df_valid.loc[mask_mad].copy()
    df_filt['flux_smooth'] = (
        df_filt['flux_hatch_amplitude_mm_day']
        .rolling(window=SMOOTH_WINDOW, center=True, min_periods=1)
        .median()
    )
    filtered_series[pair_name] = df_filt

# ── 2) Diagnóstico: puntos removidos por MAD ────────────────────────────
print(f"{'Par':<25} {'Total':>6} {'Conserv':>7} {'Remov':>6} {'%Rem':>7}")
print(f"{'─'*55}")
for pn, df_flux in flux_ts_results.items():
    n_total = len(df_flux[df_flux['quality_flag'] == 0])
    n_filt = len(filtered_series.get(pn, pd.DataFrame()))
    pct_r = (n_total - n_filt) / max(n_total, 1) * 100
    print(f"{pn:<25} {n_total:>6} {n_filt:>7} {n_total - n_filt:>6} {pct_r:>6.1f}%")

# ── 3) Gráfico publicación — ejes Y independientes ──────────────────────
n_tcs = len(ACTIVE_TCS)
fig, axes = plt.subplots(n_tcs, 1, figsize=(14, 3.2 * n_tcs), sharex=False)
if n_tcs == 1:
    axes = [axes]

for ax_idx, (ax, tc_name) in enumerate(zip(axes, ACTIVE_TCS)):
    color = _tc_hex[tc_name]
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
            color=color, alpha=0.8,
            marker=_pair_marker.get(pt, 'o'),
            markersize=3.5, linewidth=1.2,
            label=_pair_lbl.get(pt, pt),
            markeredgewidth=0.3, markeredgecolor='white'
        )

    # Banda referencia MATLAB
    if ref:
        ax.axhspan(ref['min'], ref['max'], alpha=0.07, color='#555555', zorder=0)
        ax.axhline(y=ref['mean'], color='#888888', linestyle='--',
                    linewidth=1.0, alpha=0.6, zorder=1,
                    label=f'MATLAB prom: {ref["mean"]} mm/d')

    ax.axhline(y=0, color='k', linestyle='-', linewidth=0.5, alpha=0.3)
    ax.grid(True, axis='both', alpha=0.35, linewidth=0.4, color='#aaaaaa')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    ax.set_ylabel('$q$ (mm/día)', fontsize=11)
    alpha_e = tp['alpha_e']
    title_str = (f'{tc_name} — {tp["USCS"]} | '
                 f'$\\alpha_e$ = {alpha_e:.2e} m²/s')
    if ref:
        title_str += f' | ref MATLAB: {ref["mean"]} mm/d'
    ax.set_title(title_str, fontsize=10, fontweight='bold', pad=6, loc='left')

    ax.legend(loc='upper right', fontsize=7.5, frameon=True,
              framealpha=0.92, edgecolor='#ccc', ncol=2, handlelength=2.5)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%b'))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
    ax.tick_params(axis='both', labelsize=9)

axes[-1].set_xlabel('Fecha', fontsize=11)

fig.suptitle(
    'Series Temporales de Flujo — Tendencia Central (MAD, filtrado robusto)\n'
    'Río Cuncumén — Monitoreo Dic 2025 – Feb 2026 — Ventanas deslizantes 48 h',
    fontsize=13, fontweight='bold', y=1.01
)
fig.tight_layout()

for ext in ('png', 'pdf'):
    fig.savefig(img_dir / f'series_tendencia_central_informe.{ext}',
                dpi=300, bbox_inches='tight', facecolor='white', pad_inches=0.2)
print(f'\n✅ Series tendencia central (MAD) guardadas en {img_dir}')
print(f'   → series_tendencia_central_informe.png | .pdf')
plt.show()
'''.strip()

# ═══════════════════════════════════════════════════════════════════════════
# NUEVA CELDA MARKDOWN §18
# ═══════════════════════════════════════════════════════════════════════════
SRC_MD18 = [
    "---\n",
    "## 18. Boxplot Vertical — Tendencia Central (MAD, sin outliers)\n",
    "\n",
    "Réplica del boxplot original (§15) pero con datos **filtrados por MAD** — solo tendencia central.  \n",
    "Sin grilla, sin puntos jitter, anotaciones mejoradas para legibilidad.  \n",
    "Se regenera el **mapa SIG interactivo** con popups actualizados (datos MAD, boxplot horizontal)."
]

# ═══════════════════════════════════════════════════════════════════════════
# NUEVA CELDA CÓDIGO — BOXPLOT VERTICAL + MAPA SIG
# ═══════════════════════════════════════════════════════════════════════════
SRC_BOXPLOT = r'''# =============================================================================
# §18 BOXPLOT VERTICAL — TENDENCIA CENTRAL (MAD, SIN OUTLIERS)
#     + REGENERACIÓN MAPA SIG INTEGRADO
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

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "DejaVu Serif"],
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "figure.dpi": 150,
    "savefig.dpi": 300,
})

fig, ax = plt.subplots(figsize=(10, 6))

tc_order = ['TC1', 'TC2', 'TC3', 'TC4', 'TC5']
data_list_f = [np.array(boxplot_data_mad.get(tc, [])) for tc in tc_order]
positions = np.arange(1, len(tc_order) + 1)
colors_box = [TC_COLORS[tc] for tc in tc_order]

# ── Boxplot VERTICAL, sin outliers ────────────────────────────────────────
bp = ax.boxplot(
    data_list_f, positions=positions, patch_artist=True, widths=0.55,
    showfliers=False,
    medianprops=dict(color='black', linewidth=1.8),
    whiskerprops=dict(linewidth=1.2),
    capprops=dict(linewidth=1.2),
)

for patch, color in zip(bp['boxes'], colors_box):
    patch.set_facecolor(color)
    patch.set_alpha(0.55)
    patch.set_edgecolor('black')
    patch.set_linewidth(1.0)

# ── Referencia MATLAB (diamantes) ─────────────────────────────────────────
for i, tc in enumerate(tc_order):
    ref = MATLAB_REFERENCE.get(tc, {})
    if ref:
        ax.scatter(positions[i], ref['mean'], marker='D', s=90, facecolors='none',
                   edgecolors='#1565C0', linewidths=1.5, zorder=6,
                   label='Ref. MATLAB VFLUX2' if i == 0 else None)

# ── Calcular rango para posicionar anotaciones ───────────────────────────
all_caps_hi = [bp['caps'][2*i+1].get_ydata()[0] for i in range(len(tc_order))]
all_caps_lo = [bp['caps'][2*i].get_ydata()[0] for i in range(len(tc_order))]
y_data_max = max(all_caps_hi)
y_data_min = min(min(all_caps_lo), 0)
y_range = y_data_max - y_data_min

# Ajustar ylim con margen para anotaciones
ax.set_ylim(y_data_min - y_range * 0.05, y_data_max + y_range * 0.22)

# ── Anotaciones mejoradas: encima de cada bigote superior ────────────────
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
        fontsize=8.5, ha='center', va='bottom',
        color='#222',
        bbox=dict(boxstyle='round,pad=0.25', facecolor='white',
                  alpha=0.92, edgecolor='#ccc', linewidth=0.5),
        arrowprops=dict(arrowstyle='-', color='#999', linewidth=0.6)
    )

# ── Eje X: TC + USCS + n ─────────────────────────────────────────────────
x_labels = []
for tc, vals in zip(tc_order, data_list_f):
    tp = THERMAL_PARAMS_LAB[tc]
    x_labels.append(f"{tc}\n({tp['USCS']})\nn = {len(vals)}")
ax.set_xticks(positions)
ax.set_xticklabels(x_labels, fontsize=10, fontweight='bold')

ax.set_ylabel('Flujo vertical $q$ (mm/día)', fontsize=12)
ax.set_title(
    'Distribución del Flujo Hatch-Amplitude — Tendencia Central (MAD)\n'
    'Río Cuncumén — Dic 2025 a Feb 2026 — sin outliers',
    fontsize=13, fontweight='bold', pad=12
)

ax.axhline(y=0, color='k', linestyle='-', linewidth=0.6, alpha=0.4)
# ── SIN GRILLA ────────────────────────────────────────────────────────────
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# ── Leyenda ──────────────────────────────────────────────────────────────
legend_items = [
    mpatches.Patch(facecolor='#aaa', alpha=0.55, edgecolor='k', linewidth=0.8,
                   label='Rango IQR (Q1–Q3)'),
    plt.Line2D([0], [0], color='k', linewidth=1.8, label='Mediana'),
    plt.Line2D([0], [0], marker='D', color='w', markerfacecolor='none',
               markeredgecolor='#1565C0', markersize=8, markeredgewidth=1.5,
               label='Ref. MATLAB VFLUX2'),
]
ax.legend(handles=legend_items, loc='upper left', frameon=True,
          framealpha=0.92, edgecolor='#ccc', fontsize=9)

fig.tight_layout()

for ext in ('png', 'pdf'):
    fig.savefig(img_dir / f'boxplot_tendencia_central_informe.{ext}',
                dpi=300, bbox_inches='tight', facecolor='white', pad_inches=0.25)
print(f'✅ Boxplot vertical (MAD) guardado en {img_dir}')
print(f'   → boxplot_tendencia_central_informe.png | .pdf')
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
    n_orig = len(boxplot_data.get(tc, []))  # datos sin filtrar (de celda 43)
    mad_val = np.median(np.abs(vals - np.median(vals)))
    print(f"{tc:<8} {len(vals):>5} {n_orig:>7} {np.mean(vals):>10.1f} {np.median(vals):>10.1f} "
          f"{np.percentile(vals,25):>10.1f} {np.percentile(vals,75):>10.1f} "
          f"{mad_val:>10.1f} {ref_m:>10}")
print(f"\n  Filtrado: MAD (umbral={MAD_THRESHOLD}) + mediana móvil (ventana={SMOOTH_WINDOW})")
print(f"  Unidad: mm/día  |  Método: Hatch et al. (2006)  |  Ventana: 48 h, paso 12 h")


# ══════════════════════════════════════════════════════════════════════════
# REGENERAR MAPA SIG INTEGRADO — popups con datos MAD-filtrados
# ══════════════════════════════════════════════════════════════════════════
import json as _json
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
_pair_col2 = {'sup_int':'#0072BD','int_inf':'#D95319','sup_inf':'#EDB120'}
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
      ?"Ventana: "+new Date(xMin).toLocaleDateString("es-CL")+" \u2013 "+new Date(xMax).toLocaleDateString("es-CL")
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
        +"<td>"+q3.toFixed(0)+"</td><td>"+mn.toFixed(0)+(mn>0?" \u2193":" \u2191")
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
    """Popup HTML con datos MAD-filtrados y boxplot horizontal."""
    utm_c = STATION_COORDS_UTM[tc]
    color = _tc_hex_p2.get(tc, '#555')
    tp = THERMAL_PARAMS_LAB[tc]
    tc_map = TC_CONFIG[tc]
    ds = sorted(set(_SMAP2[tc].values()))
    ds_str = ' / '.join(f'{d*100:.0f}' for d in ds) + ' cm'

    # ── 1) Serie de temperatura ──────────────────────────────────────
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
        yaxis=dict(title=dict(text='°C', font=dict(size=9)),
                   tickfont=dict(size=8)),
        template='plotly_white', height=170, width=480,
        margin=dict(l=35, r=8, t=28, b=28),
        legend=dict(orientation='h', font=dict(size=8),
                    y=1.15, x=0.5, xanchor='center'))
    ht = fig_t.to_html(include_plotlyjs=False, full_html=False,
                        config={'displayModeBar': False})

    # ── 2) Flujo Hatch-Amplitude — datos MAD-filtrados ──────────────
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
        fig_f.add_hrect(y0=ref['min'], y1=ref['max'],
                        fillcolor='gray', opacity=0.12, line_width=0)
        fig_f.add_hline(y=ref['mean'], line_dash='dash', line_color='gray',
                        line_width=1,
                        annotation_text=f'MATLAB {ref["mean"]}',
                        annotation_position='top right',
                        annotation_font_size=8)

    fig_f.update_layout(
        title=dict(text='Flujo Hatch-Amp — Tendencia Central (MAD)',
                   font=dict(size=11)),
        xaxis=dict(
            rangeslider=dict(visible=True, thickness=0.12),
            rangeselector=dict(
                buttons=[
                    dict(count=3, label='3d', step='day', stepmode='backward'),
                    dict(count=7, label='1sem', step='day', stepmode='backward'),
                    dict(count=14, label='2sem', step='day', stepmode='backward'),
                    dict(step='all', label='Todo')],
                font=dict(size=8)),
            showgrid=False, tickfont=dict(size=8), tickformat='%d-%b'),
        yaxis=dict(title=dict(text='mm/d', font=dict(size=9)),
                   tickfont=dict(size=8)),
        template='plotly_white', height=230, width=480,
        margin=dict(l=40, r=8, t=35, b=25),
        legend=dict(orientation='h', font=dict(size=7),
                    y=1.18, x=0.5, xanchor='center'))
    hf = fig_f.to_html(include_plotlyjs=False, full_html=False,
                        config={'displayModeBar': False}, div_id='flux-chart')

    # ── 3) Boxplot HORIZONTAL — datos MAD-filtrados ──────────────────
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
                x=vb, name=_pair_lbl2.get(pt_b, pt_b),
                marker_color=color,
                boxmean=True, opacity=0.8,
                boxpoints=False,
                orientation='h',
                hovertemplate='%{x:.0f} mm/d<extra></extra>'))

    _xrng = None
    if _bp_all:
        _bpa = np.array(_bp_all)
        _q1b, _q3b = np.percentile(_bpa, 25), np.percentile(_bpa, 75)
        _iqrb = _q3b - _q1b
        _xrng = [max(_bpa.min(), _q1b - 1.5*_iqrb) - _iqrb*0.15,
                 min(_bpa.max(), _q3b + 1.5*_iqrb) + _iqrb*0.15]
    fig_b.update_layout(
        title=dict(text='Boxplot (tendencia central MAD)', font=dict(size=11)),
        xaxis=dict(title=dict(text='mm/d', font=dict(size=9)),
                   tickfont=dict(size=8), range=_xrng),
        yaxis=dict(tickfont=dict(size=8)),
        template='plotly_white', height=160, width=480,
        margin=dict(l=40, r=8, t=28, b=28), showlegend=False)
    hb = fig_b.to_html(include_plotlyjs=False, full_html=False,
                        config={'displayModeBar': False})

    ref_h = ''
    if ref:
        ref_h = (f'<div style="font-size:9px;color:#666;margin-top:2px;">'
                 f'Ref MATLAB: {ref["min"]}–{ref["max"]} mm/d '
                 f'(prom {ref["mean"]})</div>')
    js = _JS_TMPL2.replace('__DATA__', _json.dumps(raw))

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
body{{font-family:'Segoe UI',Arial,sans-serif;margin:0;padding:8px;background:#fefefe;color:#222}}
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
#rng-info{{text-align:center;font-size:10px;color:#777;margin:2px 0 4px;
  background:#f8f9fa;border-radius:4px;padding:3px}}
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


# ══════════════════════════════════════════════════════════════════════════
# Construir Mapa SIG con datos MAD-filtrados
# ══════════════════════════════════════════════════════════════════════════
tc_list2 = list(STATION_COORDS_UTM.keys())
clat2 = np.mean([coords_wgs84_v2[t]['lat'] for t in tc_list2])
clon2 = np.mean([coords_wgs84_v2[t]['lon'] for t in tc_list2])

m2 = folium.Map(location=[clat2, clon2], zoom_start=14,
                tiles=None, control_scale=True)
folium.TileLayer(
    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/'
          'World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attr='Esri', name='Satélite ESRI', max_zoom=19).add_to(m2)
folium.TileLayer(
    tiles='https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
    attr='OpenTopoMap', name='Topográfico').add_to(m2)
folium.TileLayer(
    tiles='https://server.arcgisonline.com/ArcGIS/rest/services/'
          'Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
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
print(f'\n✅ Mapa SIG (MAD): {map_path2.name}')
print(f'   → Datos MAD-filtrados en cada popup')
print(f'   → {map_path2}')
display(m2)
'''.strip()


def _to_source_lines(text):
    """Convierte un string multi-línea a lista de líneas con \\n."""
    lines = text.split('\n')
    return [line + '\n' for line in lines[:-1]] + [lines[-1]]


def main():
    with open(NB_PATH, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    cells = nb['cells']
    n = len(cells)
    print(f"Notebook actual: {n} celdas")
    assert n >= 51, f"Se esperaban ≥51 celdas, hay {n}"

    # ── Reemplazar source de celdas 48-51 (índices 47-50) ────────────
    # Celda 48 (markdown §17)
    cells[IDX_MD17]['source'] = SRC_MD17
    print(f"  [48] Markdown §17 actualizado")

    # Celda 49 (code series)
    cells[IDX_CODE_SERIES]['source'] = _to_source_lines(SRC_SERIES)
    cells[IDX_CODE_SERIES]['outputs'] = []
    cells[IDX_CODE_SERIES]['execution_count'] = None
    print(f"  [49] Code — series temporales MAD actualizado")

    # Celda 50 (markdown §18)
    cells[IDX_MD18]['source'] = SRC_MD18
    print(f"  [50] Markdown §18 actualizado")

    # Celda 51 (code boxplot + mapa)
    cells[IDX_CODE_BOXPLOT]['source'] = _to_source_lines(SRC_BOXPLOT)
    cells[IDX_CODE_BOXPLOT]['outputs'] = []
    cells[IDX_CODE_BOXPLOT]['execution_count'] = None
    print(f"  [51] Code — boxplot vertical MAD + mapa actualizado")

    # ── Guardar ──────────────────────────────────────────────────────
    with open(NB_PATH, 'w', encoding='utf-8') as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)

    print(f"\n✅ Notebook guardado: {n} celdas ({NB_PATH.name})")
    print("   Cambios:")
    print("   → §17: Series temporales — MAD + publicación (ejes Y indep.)")
    print("   → §18: Boxplot vertical — MAD + mejores etiquetas + sin grilla")
    print("   → Mapa SIG con popups MAD-filtrados")


if __name__ == "__main__":
    main()
