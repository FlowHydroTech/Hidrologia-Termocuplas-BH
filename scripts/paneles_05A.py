#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
paneles_05A.py — Generación de paneles interactivos HTML para el análisis 05A.

Ejecutar desde la raíz del proyecto:
    python scripts/paneles_05A.py

Requiere:
  - Haber ejecutado pipeline_05A.py (o que existan los CSVs en OUT_DIR).
  - plotly, folium, pyproj

Archivos generados (image/terreno_2026/):
  1. selector_ventana_TC{1-5}.html  — Selector interactivo por TC
  2. perfil_flujo_rio_05A.html      — Perfil longitudinal del río (Plotly)
  3. panel_sig_integrado_05A.html   — Panel SIG Folium con popups interactivos
"""

import sys
from pathlib import Path
import json as _json

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import folium
import folium.plugins
from pyproj import Transformer

from config_05A import (
    PROJECT_ROOT, OUT_DIR, IMG_DIR,
    TC_CONFIG, DEPTHS_M, ACTIVE_TCS, THERMAL_PARAMS_LAB,
    MATLAB_REFERENCE, TC_PERIODS, TC_COLORS,
    PAIR_MAP, PAIR_LABELS, PAIR_COLORS_MATLAB,
    STATION_COORDS_UTM,
)

import pipeline_05A as pipe

# ══════════════════════════════════════════════════════════════════════════
# CONSTANTES LOCALES
# ══════════════════════════════════════════════════════════════════════════
PAIRS = ["sup_int", "int_inf", "sup_inf"]
_pair_labels_html = {
    "sup_int": "Sup → Int  (z₁–z₂)",
    "int_inf": "Int → Inf  (z₂–z₃)",
    "sup_inf": "Sup → Inf  (z₁–z₃)",
}
_pair_colors = {"sup_int": "#0072BD", "int_inf": "#D95319", "sup_inf": "#EDB120"}
MS_TO_MM_DAY = 1000.0 * 86400.0

# UTM → WGS84
_tf = Transformer.from_crs("EPSG:32719", "EPSG:4326", always_xy=True)
_coords_wgs84 = {}
for _st, _utm in STATION_COORDS_UTM.items():
    _lon, _lat = _tf.transform(_utm["easting"], _utm["northing"])
    _coords_wgs84[_st] = {"lat": _lat, "lon": _lon}


# ══════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════
def _load_flux_ts_csvs():
    """Carga CSVs de series temporales de flujo."""
    BASE_TS = OUT_DIR / "series_temporales"
    all_data = {}
    for tc in ACTIVE_TCS:
        all_data[tc] = {}
        for pair in PAIRS:
            fpath = BASE_TS / f"flujo_temporal_{tc}_{pair}.csv"
            if not fpath.exists():
                continue
            df = pd.read_csv(fpath, parse_dates=["datetime"])
            if "flux_hatch_amplitude_mm_day" not in df.columns:
                continue
            df["flux_ms"] = df["flux_hatch_amplitude_mm_day"] / MS_TO_MM_DAY
            mask = df["flux_ms"].notna() & np.isfinite(df["flux_ms"])
            all_data[tc][pair] = df.loc[mask, ["datetime", "flux_ms",
                                                "flux_hatch_amplitude_mm_day"]].copy()
    return all_data


# ══════════════════════════════════════════════════════════════════════════
# 1. SELECTORES INTERACTIVOS POR TC
# ══════════════════════════════════════════════════════════════════════════
_HTML_SELECTOR = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Selector Ventana Temporal - {tc}</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; background: #fafafa; }}
#chart {{ width: 100%; max-width: 1100px; margin: 0 auto; }}
#stats-table {{ width: 100%; max-width: 1100px; margin: 15px auto; border-collapse: collapse; }}
#stats-table th {{ background: #2c3e50; color: white; padding: 8px 12px; font-size: 13px; }}
#stats-table td {{ padding: 6px 12px; text-align: center; font-size: 12px; border-bottom: 1px solid #ddd; }}
#stats-table tr:nth-child(even) {{ background: #ecf0f1; }}
#stats-table tr:nth-child(odd) {{ background: #ffffff; }}
h2 {{ text-align: center; color: #2c3e50; }}
#range-info {{ text-align: center; color: #555; font-size: 13px; margin: 5px 0 10px; }}
</style>
</head>
<body>
<h2>Flujo Hatch-Amplitude &mdash; {tc}</h2>
<div id="range-info">Ventana: serie completa</div>
<div id="chart"></div>
<table id="stats-table">
<thead><tr>
  <th>Par</th><th>Mediana (m/s)</th><th>Promedio (m/s)</th>
  <th>Q1 (m/s)</th><th>Q3 (m/s)</th><th>IQR (m/s)</th>
  <th>Mediana (mm/d)</th><th>Promedio (mm/d)</th><th>n</th>
</tr></thead>
<tbody id="stats-body"></tbody>
</table>
<script>
var DATA = {data_json};
var PAIRS = {pairs_json};
var PAIR_LABELS = {pair_labels_json};
var PAIR_COLORS = {pair_colors_json};
var MS_TO_MMD = {ms_to_mmd};
var traces = [];
PAIRS.forEach(function(pair) {{
  if (!DATA[pair]) return;
  traces.push({{
    x: DATA[pair].dt, y: DATA[pair].flux_ms,
    mode: 'lines+markers', name: PAIR_LABELS[pair],
    line: {{color: PAIR_COLORS[pair], width: 1.5}},
    marker: {{size: 4}}, legendgroup: pair
  }});
}});
var layout = {{
  height: 420, template: 'plotly_white',
  legend: {{orientation: 'h', yanchor: 'bottom', y: 1.02, xanchor: 'center', x: 0.5}},
  xaxis: {{
    rangeslider: {{visible: true, thickness: 0.1}},
    rangeselector: {{buttons: [
      {{count: 3, label: '3d', step: 'day', stepmode: 'backward'}},
      {{count: 7, label: '1sem', step: 'day', stepmode: 'backward'}},
      {{count: 14, label: '2sem', step: 'day', stepmode: 'backward'}},
      {{step: 'all', label: 'Todo'}}
    ]}}, type: 'date'
  }},
  yaxis: {{title: 'Flujo vertical (m/s)'}},
  margin: {{l: 70, r: 30, t: 40, b: 30}}
}};
Plotly.newPlot('chart', traces, layout, {{responsive: true}});
function percentile(arr, p) {{
  var s = arr.slice().sort(function(a,b){{return a-b;}});
  var idx = (p/100) * (s.length - 1);
  var lo = Math.floor(idx), hi = Math.ceil(idx);
  if (lo === hi) return s[lo];
  return s[lo] + (idx - lo) * (s[hi] - s[lo]);
}}
function updateStats(xMin, xMax) {{
  var tbody = document.getElementById('stats-body');
  tbody.innerHTML = '';
  var info = document.getElementById('range-info');
  if (xMin && xMax) {{
    var d0 = new Date(xMin), d1 = new Date(xMax);
    info.textContent = 'Ventana: ' + d0.toLocaleDateString('es-CL') + ' \\u2013 ' + d1.toLocaleDateString('es-CL');
  }} else {{ info.textContent = 'Ventana: serie completa'; }}
  PAIRS.forEach(function(pair) {{
    if (!DATA[pair]) return;
    var dt = DATA[pair].dt, v = DATA[pair].flux_ms, filtered = [];
    for (var i = 0; i < dt.length; i++) {{
      if ((!xMin || dt[i] >= xMin) && (!xMax || dt[i] <= xMax)) filtered.push(v[i]);
    }}
    if (filtered.length === 0) return;
    var q1 = percentile(filtered, 25), med = percentile(filtered, 50);
    var q3 = percentile(filtered, 75);
    var mean = filtered.reduce(function(a,b){{return a+b;}},0) / filtered.length;
    var iqr = q3 - q1;
    tbody.innerHTML += '<tr>'
      + '<td style="font-weight:bold;color:' + PAIR_COLORS[pair] + '">' + PAIR_LABELS[pair] + '</td>'
      + '<td>' + med.toExponential(3) + '</td><td>' + mean.toExponential(3) + '</td>'
      + '<td>' + q1.toExponential(3) + '</td><td>' + q3.toExponential(3) + '</td>'
      + '<td>' + iqr.toExponential(3) + '</td>'
      + '<td>' + (med * MS_TO_MMD).toFixed(1) + '</td><td>' + (mean * MS_TO_MMD).toFixed(1) + '</td>'
      + '<td>' + filtered.length + '</td></tr>';
  }});
}}
updateStats(null, null);
document.getElementById('chart').on('plotly_relayout', function(ev) {{
  var xMin = ev['xaxis.range[0]'] || (ev['xaxis.range'] && ev['xaxis.range'][0]) || null;
  var xMax = ev['xaxis.range[1]'] || (ev['xaxis.range'] && ev['xaxis.range'][1]) || null;
  if (ev['xaxis.autorange']) {{ xMin = null; xMax = null; }}
  updateStats(xMin, xMax);
}});
</script>
</body>
</html>"""


def gen_selectors(all_data):
    """Genera HTMLs con selector interactivo de ventana temporal por TC."""
    for tc in ACTIVE_TCS:
        if tc not in all_data or not all_data[tc]:
            continue
        tc_data = {}
        for pair in PAIRS:
            if pair not in all_data[tc]:
                continue
            d = all_data[tc][pair]
            tc_data[pair] = {
                "dt": d["datetime"].dt.strftime("%Y-%m-%dT%H:%M:%S").tolist(),
                "flux_ms": d["flux_ms"].round(10).tolist(),
            }
        html = _HTML_SELECTOR.format(
            tc=tc,
            data_json=_json.dumps(tc_data),
            pairs_json=_json.dumps(PAIRS),
            pair_labels_json=_json.dumps(_pair_labels_html),
            pair_colors_json=_json.dumps(_pair_colors),
            ms_to_mmd=MS_TO_MM_DAY,
        )
        out = IMG_DIR / f"selector_ventana_{tc}.html"
        out.write_text(html, encoding="utf-8")
    print(f"  ✔ Selectores interactivos: {len(ACTIVE_TCS)} TCs")


# ══════════════════════════════════════════════════════════════════════════
# 2. PERFIL DE FLUJO POR POSICIÓN EN EL RÍO
# ══════════════════════════════════════════════════════════════════════════
def gen_perfil_rio(flujos_promedio_tc):
    """Perfil longitudinal Plotly — TC5 (aguas arriba) → TC1 (aguas abajo)."""
    tc_order = ["TC5", "TC4", "TC3", "TC2", "TC1"]
    ha_profile = [flujos_promedio_tc.get(tc, {}).get("hatch_mean", np.nan) for tc in tc_order]
    mc_profile = [flujos_promedio_tc.get(tc, {}).get("mc_mean", np.nan) for tc in tc_order]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=tc_order, y=ha_profile, mode="lines+markers",
        name="Hatch-Amplitude", marker=dict(size=14, symbol="circle"),
        line=dict(color="#e74c3c", width=3),
        hovertemplate="%{x}<br>Hatch-Amp: %{y:.0f} mm/d<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=tc_order, y=mc_profile, mode="lines+markers",
        name="McCallum", marker=dict(size=14, symbol="square"),
        line=dict(color="#2c3e50", width=3, dash="dash"),
        hovertemplate="%{x}<br>McCallum: %{y:.0f} mm/d<extra></extra>"))

    for i, tc in enumerate(tc_order):
        tp = THERMAL_PARAMS_LAB[tc]
        fig.add_annotation(
            x=tc, y=ha_profile[i], text=tp["USCS"],
            showarrow=True, arrowhead=2, ax=0, ay=-30,
            font=dict(size=10, color=TC_COLORS.get(tc, "#333")))

    fig.update_layout(
        title="Perfil de Flujo a lo largo del Río Silala (aguas arriba → abajo)",
        xaxis_title="Estación (aguas arriba → abajo)",
        yaxis_title="Flujo promedio (mm/d)",
        template="plotly_white", height=500, width=900,
        legend=dict(orientation="h", y=-0.12, x=0.5, xanchor="center"))

    out_path = IMG_DIR / "perfil_flujo_rio_05A.html"
    pio.write_html(fig, str(out_path), include_plotlyjs=True)
    print(f"  ✔ Perfil del río: {out_path.name}")


# ══════════════════════════════════════════════════════════════════════════
# 3. PANEL SIG INTEGRADO — Folium + Selector Temporal en Popup
# ══════════════════════════════════════════════════════════════════════════

# JS template para tabla IQR dinámica dentro del popup
_JS_TMPL = '''<script>
(function(){
  var FR=__DATA__;
  var pk=Object.keys(FR);
  function pct(a,p){var s=a.slice().sort(function(x,y){return x-y});
    var i=p/100*(s.length-1),lo=Math.floor(i),hi=Math.ceil(i);
    return lo===hi?s[lo]:s[lo]+(i-lo)*(s[hi]-s[lo]);}
  function upd(xMin,xMax){
    var tb=document.getElementById('stats-body');if(!tb)return;
    tb.innerHTML='';
    var ri=document.getElementById('rng-info');
    if(ri){ri.textContent=xMin&&xMax
      ?'Ventana: '+new Date(xMin).toLocaleDateString('es-CL')+' \\u2013 '+new Date(xMax).toLocaleDateString('es-CL')
      :'Ventana: serie completa';}
    var all=[];
    pk.forEach(function(k){
      var dt=FR[k].dt,v=FR[k].flux,f=[];
      for(var i=0;i<dt.length;i++){if((!xMin||dt[i]>=xMin)&&(!xMax||dt[i]<=xMax))f.push(v[i]);}
      if(!f.length)return; all=all.concat(f);
      var q1=pct(f,25),md=pct(f,50),q3=pct(f,75);
      var mn=f.reduce(function(a,b){return a+b},0)/f.length;
      tb.innerHTML+="<tr><td style='color:"+FR[k].color+"'>"+FR[k].label+"</td>"
        +"<td>"+q1.toFixed(0)+"</td><td style='font-weight:600'>"+md.toFixed(0)+"</td>"
        +"<td>"+q3.toFixed(0)+"</td><td>"+mn.toFixed(0)+(mn>0?" ↓":" ↑")
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
  var fc=document.getElementById('flux-chart');
  if(fc)fc.on('plotly_relayout',function(ev){
    var xMin=ev['xaxis.range[0]']||(ev['xaxis.range']&&ev['xaxis.range'][0])||null;
    var xMax=ev['xaxis.range[1]']||(ev['xaxis.range']&&ev['xaxis.range'][1])||null;
    if(ev['xaxis.autorange']){xMin=null;xMax=null;}
    upd(xMin,xMax);
  });
})();</script>'''

_pos_short = {"surface": "sup", "intermediate": "int", "deep": "inf"}
_pos_dash = {"surface": "solid", "intermediate": "dash", "deep": "dot"}
_tc_hex_p = {"TC1": "#1f77b4", "TC2": "#ff7f0e", "TC3": "#e377c2",
             "TC4": "#2ca02c", "TC5": "#d62728"}
_pair_col = {"sup_int": "#0072BD", "int_inf": "#D95319", "sup_inf": "#EDB120"}
_pair_lbl = {"sup_int": "sup→int", "int_inf": "int→inf", "sup_inf": "sup→inf"}


def _build_popup(tc, df_aligned, flux_ts_results, all_flux_results):
    """Popup HTML con selector temporal integrado en gráfico de flujo."""
    utm_c = STATION_COORDS_UTM[tc]
    color = _tc_hex_p.get(tc, "#555")
    tp = THERMAL_PARAMS_LAB[tc]
    tc_map = TC_CONFIG[tc]
    depths_m = DEPTHS_M

    # Profundidades únicas
    ds = sorted(set(depths_m[tc_map[pos]] for pos in ["surface", "intermediate", "deep"]))
    ds_str = " / ".join(f"{d*100:.0f}" for d in ds) + " cm"

    # ── 1) Serie de temperatura ──────────────────────────────────────────
    fig_t = go.Figure()
    tc_start = pd.Timestamp(TC_PERIODS[tc][0])
    tc_end = pd.Timestamp(TC_PERIODS[tc][1])
    mask_tc = (df_aligned["fecha"] >= tc_start) & (df_aligned["fecha"] <= tc_end)
    df_tc = df_aligned[mask_tc]
    for pos in ["surface", "intermediate", "deep"]:
        col = tc_map[pos]
        dcm = depths_m[col] * 100
        d = df_tc.dropna(subset=[col])
        st = max(1, len(d) // 200)
        fig_t.add_trace(go.Scatter(
            x=d.iloc[::st]["fecha"], y=d.iloc[::st][col], mode="lines",
            name=f"{_pos_short[pos]} ({dcm:.0f}cm)",
            line=dict(width=1.5, dash=_pos_dash[pos]),
            hovertemplate="%{x|%d-%b %H:%M}<br>%{y:.1f}°C<extra></extra>"))
    fig_t.update_layout(
        title=dict(text="Temperatura", font=dict(size=12)),
        xaxis=dict(showgrid=False, tickfont=dict(size=8), tickformat="%d-%b"),
        yaxis=dict(title=dict(text="°C", font=dict(size=9)), tickfont=dict(size=8)),
        template="plotly_white", height=170, width=480,
        margin=dict(l=35, r=8, t=28, b=28),
        legend=dict(orientation="h", font=dict(size=8), y=1.15, x=0.5, xanchor="center"))
    ht = fig_t.to_html(include_plotlyjs=False, full_html=False,
                       config={"displayModeBar": False})

    # ── 2) Flujo Hatch-Amplitude con RANGE-SLIDER ───────────────────────
    fig_f = go.Figure()
    raw = {}
    has_f = False
    for pn, dff in flux_ts_results.items():
        if tc not in pn:
            continue
        dv = dff[dff["quality_flag"] == 0]
        if len(dv) == 0 or "flux_hatch_amplitude_mm_day" not in dv.columns:
            continue
        has_f = True
        pt = pn.split("_", 1)[1]
        raw[pt] = {
            "dt": dv["datetime"].dt.strftime("%Y-%m-%dT%H:%M:%S").tolist(),
            "flux": dv["flux_hatch_amplitude_mm_day"].round(2).tolist(),
            "label": _pair_lbl.get(pt, pt),
            "color": _pair_col.get(pt, "#888"),
        }
        sf = max(1, len(dv) // 150)
        fig_f.add_trace(go.Scatter(
            x=dv.iloc[::sf]["datetime"],
            y=dv.iloc[::sf]["flux_hatch_amplitude_mm_day"],
            mode="lines+markers", name=_pair_lbl.get(pt, pt),
            marker=dict(size=3),
            line=dict(width=1.5, color=_pair_col.get(pt, "#888")),
            hovertemplate="%{x|%d-%b %H:%M}<br>%{y:.0f} mm/d<extra></extra>"))

    ref = MATLAB_REFERENCE.get(tc, {})
    if ref and has_f:
        fig_f.add_hrect(y0=ref["min"], y1=ref["max"],
                        fillcolor="gray", opacity=0.12, line_width=0)
        fig_f.add_hline(y=ref["mean"], line_dash="dash", line_color="gray",
                        line_width=1,
                        annotation_text=f"MATLAB {ref['mean']}",
                        annotation_position="top right",
                        annotation_font_size=8)
    fig_f.update_layout(
        title=dict(text="Flujo Hatch-Amplitude (selector interactivo)", font=dict(size=11)),
        xaxis=dict(
            rangeslider=dict(visible=True, thickness=0.12),
            rangeselector=dict(buttons=[
                dict(count=3, label="3d", step="day", stepmode="backward"),
                dict(count=7, label="1sem", step="day", stepmode="backward"),
                dict(count=14, label="2sem", step="day", stepmode="backward"),
                dict(step="all", label="Todo")],
                font=dict(size=8)),
            showgrid=False, tickfont=dict(size=8), tickformat="%d-%b"),
        yaxis=dict(title=dict(text="mm/d", font=dict(size=9)), tickfont=dict(size=8)),
        template="plotly_white", height=230, width=480,
        margin=dict(l=40, r=8, t=35, b=25),
        legend=dict(orientation="h", font=dict(size=7), y=1.18, x=0.5, xanchor="center"))
    hf = fig_f.to_html(include_plotlyjs=False, full_html=False,
                       config={"displayModeBar": False}, div_id="flux-chart")

    # ── 3) Boxplot ───────────────────────────────────────────────────────
    fig_b = go.Figure()
    for pk_key in [p for p in all_flux_results.keys() if tc in p]:
        ps = pk_key.split(": ")[1] if ": " in pk_key else pk_key
        ts_k = f"{tc}_{ps.replace('-', '_')}"
        if ts_k in flux_ts_results:
            dv2 = flux_ts_results[ts_k]
            dv2 = dv2[dv2["quality_flag"] == 0]
            if "flux_hatch_amplitude_mm_day" in dv2.columns:
                vb = dv2["flux_hatch_amplitude_mm_day"].dropna().values
                if len(vb) > 0:
                    fig_b.add_trace(go.Box(
                        y=vb, name=ps, marker_color=color,
                        boxmean=True, opacity=0.8,
                        hovertemplate="%{y:.0f} mm/d<extra></extra>"))
    fig_b.update_layout(
        title=dict(text="Boxplot Hatch-Amp", font=dict(size=11)),
        yaxis=dict(title=dict(text="mm/d", font=dict(size=9)), tickfont=dict(size=8)),
        xaxis=dict(tickfont=dict(size=8)),
        template="plotly_white", height=160, width=480,
        margin=dict(l=40, r=8, t=28, b=28), showlegend=False)
    hb = fig_b.to_html(include_plotlyjs=False, full_html=False,
                       config={"displayModeBar": False})

    # ── Ref MATLAB texto ─────────────────────────────────────────────────
    ref_h = ""
    if ref:
        ref_h = (f'<div style="font-size:9px;color:#666;margin-top:2px;">'
                 f'Ref MATLAB: {ref["min"]}–{ref["max"]} mm/d '
                 f'(prom {ref["mean"]})</div>')

    # ── JS handler dinámico ──────────────────────────────────────────────
    js = _JS_TMPL.replace("__DATA__", _json.dumps(raw))

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
<div class="hdr"><h3>&#128205; {tc}</h3><span class="badge">{tp['USCS']}</span></div>
<div class="info">
  <b>UTM 19S:</b> {utm_c['easting']}E, {utm_c['northing']}N &nbsp;|&nbsp;
  <b>Prof:</b> {ds_str}<br>
  <b>IDIEM:</b> &lambda;={tp['lambda_sediment']:.3f} W/m&middot;K |
  C={tp['C_sediment']/1e6:.3f} MJ/m&sup3;&middot;K |
  &alpha;={tp['alpha_e']:.2e} m&sup2;/s
</div>
<div class="chart-box">{ht}</div>
<div class="chart-box">{hf}</div>
<div id="rng-info">Ventana: serie completa &mdash; mueva el slider o use botones (3d / 1sem / 2sem / Todo)</div>
<div class="chart-box">{hb}</div>
<div class="mc">
  <b>Flujo Hatch-Amp (mm/d) &mdash; IQR ventanas deslizantes:</b>
  <table><thead><tr>
    <th>Par</th><th>Q1</th><th>Mediana</th><th>Q3</th><th>Promedio</th><th>n</th>
  </tr></thead>
  <tbody id="stats-body"></tbody></table>
  {ref_h}
</div>
{js}
</body></html>"""


def gen_panel_sig(df_aligned, flux_ts_results, all_flux_results):
    """Genera panel SIG integrado con Folium."""
    from branca.element import Element

    tc_list = list(STATION_COORDS_UTM.keys())
    clat = np.mean([_coords_wgs84[t]["lat"] for t in tc_list])
    clon = np.mean([_coords_wgs84[t]["lon"] for t in tc_list])

    m = folium.Map(location=[clat, clon], zoom_start=14,
                   tiles=None, control_scale=True)

    # CSS: tooltips transparentes con halo de texto
    m.get_root().header.add_child(Element(
        "<style>"
        ".leaflet-tooltip { background: none !important; border: none !important; "
        "box-shadow: none !important; padding: 0 !important; }"
        ".leaflet-tooltip::before { display: none !important; }"
        "</style>"
    ))

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/"
              "World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Satélite ESRI", max_zoom=19, show=True).add_to(m)
    folium.TileLayer(
        tiles="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
        attr="OpenTopoMap", name="Topográfico", show=False).add_to(m)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/"
              "Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
        attr="Esri Labels", name="Etiquetas", overlay=True).add_to(m)

    _tooltip_dir = {"TC3": "left", "TC4": "right"}
    _halo = ("text-shadow:-2px -2px 0 #fff, 2px -2px 0 #fff, "
             "-2px 2px 0 #fff, 2px 2px 0 #fff, 0 -2px 0 #fff, "
             "0 2px 0 #fff, -2px 0 0 #fff, 2px 0 0 #fff, "
             "-1px -1px 0 #fff, 1px -1px 0 #fff, "
             "-1px 1px 0 #fff, 1px 1px 0 #fff;")
    for st, wgs in _coords_wgs84.items():
        html_pop = _build_popup(st, df_aligned, flux_ts_results, all_flux_results)
        iframe = folium.IFrame(html=html_pop, width=520, height=800)
        popup = folium.Popup(iframe, max_width=530)
        folium.Marker(
            location=[wgs["lat"], wgs["lon"]], popup=popup,
            tooltip=folium.Tooltip(
                f"{st} ({THERMAL_PARAMS_LAB[st]['USCS']})",
                permanent=True,
                direction=_tooltip_dir.get(st, "auto"),
                offset=(0, -5),
                style=(f"font-size:12px;font-weight:bold;color:black;"
                       f"background:transparent;border:none;box-shadow:none;"
                       f"padding:0;{_halo}"),
            ),
            icon=folium.Icon(color="red", icon="thermometer-half", prefix="fa")
        ).add_to(m)

    ordered = ["TC5", "TC4", "TC3", "TC2", "TC1"]
    folium.PolyLine(
        [[_coords_wgs84[s]["lat"], _coords_wgs84[s]["lon"]]
         for s in ordered if s in _coords_wgs84],
        color="cyan", weight=3, opacity=0.7,
        dash_array="10", tooltip="Perfil del río").add_to(m)

    folium.plugins.MeasureControl(position="bottomleft").add_to(m)
    folium.plugins.Fullscreen().add_to(m)
    folium.plugins.MiniMap(toggle_display=True).add_to(m)
    folium.LayerControl().add_to(m)

    map_path = IMG_DIR / "panel_sig_integrado_05A.html"
    m.save(str(map_path))
    print(f"  ✔ Panel SIG integrado: {map_path.name}")


# ══════════════════════════════════════════════════════════════════════════
# 4. PANEL SIG — TENDENCIA CENTRAL MAD
# ══════════════════════════════════════════════════════════════════════════

_MAD_THRESHOLD = 2.5
_SMOOTH_WINDOW = 5

_pair_col_mad = {"sup_int": "#4FC3F7", "int_inf": "#29B6F6", "sup_inf": "#0288D1"}
_pair_lbl_mad = {"sup_int": "sup→int", "int_inf": "int→inf", "sup_inf": "sup→inf"}

_JS_TMPL_MAD = """<script>
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


def _mad_filter_val(values, threshold=_MAD_THRESHOLD):
    """Filtrar outliers con MAD (Median Absolute Deviation)."""
    med = np.median(values)
    mad_val = np.median(np.abs(values - med))
    if mad_val < 1e-10:
        return np.ones(len(values), dtype=bool)
    mod_z = 0.6745 * np.abs(values - med) / mad_val
    return mod_z < threshold


def _apply_mad_filter(flux_ts_results):
    """Aplica filtrado MAD + suavizado mediana móvil a todas las series."""
    filtered = {}
    for pair_name, df_flux in flux_ts_results.items():
        df_valid = df_flux[df_flux["quality_flag"] == 0].copy()
        if len(df_valid) == 0 or "flux_hatch_amplitude_mm_day" not in df_valid.columns:
            continue
        vals = df_valid["flux_hatch_amplitude_mm_day"].values
        mask = _mad_filter_val(vals)
        n_kept = mask.sum()
        if n_kept < max(3, len(vals) * 0.10):
            for fb in [3.5, 5.0]:
                mask = _mad_filter_val(vals, fb)
                if mask.sum() >= 3:
                    break
            else:
                mask = np.ones(len(vals), dtype=bool)
        df_f = df_valid.loc[mask].copy()
        df_f["flux_smooth"] = (
            df_f["flux_hatch_amplitude_mm_day"]
            .rolling(window=_SMOOTH_WINDOW, center=True, min_periods=1)
            .median()
        )
        filtered[pair_name] = df_f
    return filtered


def _build_popup_mad(tc, df_aligned, filtered_series):
    """Popup HTML con datos MAD-filtrados para mapa de tendencia central."""
    from config_05A import TC_PERIODS

    utm_c = STATION_COORDS_UTM[tc]
    color = _tc_hex_p.get(tc, "#555")
    tp = THERMAL_PARAMS_LAB[tc]
    tc_map = TC_CONFIG[tc]
    depths_m = DEPTHS_M
    ds = sorted(set(depths_m[tc_map[pos]] for pos in ["surface", "intermediate", "deep"]))
    ds_str = " / ".join(f"{d*100:.0f}" for d in ds) + " cm"

    # Temperatura
    fig_t = go.Figure()
    tc_start = pd.Timestamp(TC_PERIODS[tc][0])
    tc_end = pd.Timestamp(TC_PERIODS[tc][1])
    mask_tc = (df_aligned["fecha"] >= tc_start) & (df_aligned["fecha"] <= tc_end)
    df_tc = df_aligned[mask_tc]
    for pos in ["surface", "intermediate", "deep"]:
        col = tc_map[pos]
        dcm = depths_m[col] * 100
        d = df_tc.dropna(subset=[col])
        st = max(1, len(d) // 200)
        fig_t.add_trace(go.Scatter(
            x=d.iloc[::st]["fecha"], y=d.iloc[::st][col], mode="lines",
            name=f"{_pos_short[pos]} ({dcm:.0f}cm)",
            line=dict(width=1.5, dash=_pos_dash[pos]),
            hovertemplate="%{x|%d-%b %H:%M}<br>%{y:.1f}°C<extra></extra>"))
    fig_t.update_layout(
        title=dict(text="Temperatura", font=dict(size=12)),
        xaxis=dict(showgrid=False, tickfont=dict(size=8), tickformat="%d-%b"),
        yaxis=dict(title=dict(text="°C", font=dict(size=9)), tickfont=dict(size=8)),
        template="plotly_white", height=170, width=480,
        margin=dict(l=35, r=8, t=28, b=28),
        legend=dict(orientation="h", font=dict(size=8), y=1.15, x=0.5, xanchor="center"))
    ht = fig_t.to_html(include_plotlyjs=False, full_html=False,
                       config={"displayModeBar": False})

    # Flujo MAD con range-slider
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
        pt = pn.split("_", 1)[1]
        raw[pt] = {
            "dt": df_filt["datetime"].dt.strftime("%Y-%m-%dT%H:%M:%S").tolist(),
            "flux": df_filt["flux_smooth"].round(2).tolist(),
            "label": _pair_lbl_mad.get(pt, pt),
            "color": _pair_col_mad.get(pt, "#888"),
        }
        sf = max(1, len(df_filt) // 150)
        fig_f.add_trace(go.Scatter(
            x=df_filt.iloc[::sf]["datetime"],
            y=df_filt.iloc[::sf]["flux_smooth"],
            mode="lines+markers", name=_pair_lbl_mad.get(pt, pt),
            marker=dict(size=3),
            line=dict(width=1.5, color=_pair_col_mad.get(pt, "#888")),
            hovertemplate="%{x|%d-%b %H:%M}<br>%{y:.0f} mm/d<extra></extra>"))
    ref = MATLAB_REFERENCE.get(tc, {})
    if ref and has_f:
        fig_f.add_hrect(y0=ref["min"], y1=ref["max"], fillcolor="gray",
                        opacity=0.12, line_width=0)
        fig_f.add_hline(y=ref["mean"], line_dash="dash", line_color="gray",
                        line_width=1, annotation_text=f'MATLAB {ref["mean"]}',
                        annotation_position="top right", annotation_font_size=8)
    fig_f.update_layout(
        title=dict(text="Flujo Hatch-Amp — Tendencia Central (MAD)",
                   font=dict(size=11)),
        xaxis=dict(rangeslider=dict(visible=True, thickness=0.12),
                   rangeselector=dict(buttons=[
                       dict(count=3, label="3d", step="day", stepmode="backward"),
                       dict(count=7, label="1sem", step="day", stepmode="backward"),
                       dict(count=14, label="2sem", step="day", stepmode="backward"),
                       dict(step="all", label="Todo")], font=dict(size=8)),
                   showgrid=False, tickfont=dict(size=8), tickformat="%d-%b"),
        yaxis=dict(title=dict(text="mm/d", font=dict(size=9)), tickfont=dict(size=8)),
        template="plotly_white", height=230, width=480,
        margin=dict(l=40, r=8, t=35, b=25),
        legend=dict(orientation="h", font=dict(size=7), y=1.18, x=0.5, xanchor="center"))
    hf = fig_f.to_html(include_plotlyjs=False, full_html=False,
                       config={"displayModeBar": False}, div_id="flux-chart")

    # Boxplot MAD
    fig_b = go.Figure()
    _bp_all = []
    for pn_b in sorted(filtered_series.keys()):
        if tc not in pn_b:
            continue
        df_b = filtered_series[pn_b]
        if len(df_b) == 0:
            continue
        pt_b = pn_b.split("_", 1)[1]
        vb = df_b["flux_hatch_amplitude_mm_day"].dropna().values
        if len(vb) > 0:
            _bp_all.extend(vb.tolist())
            fig_b.add_trace(go.Box(
                y=vb, name=_pair_lbl_mad.get(pt_b, pt_b),
                marker_color="#4FC3F7", boxmean=True, opacity=0.8,
                boxpoints=False,
                hovertemplate="%{y:.0f} mm/d<extra></extra>"))
    _xrng = None
    if _bp_all:
        _bpa = np.array(_bp_all)
        _q1b, _q3b = np.percentile(_bpa, 25), np.percentile(_bpa, 75)
        _iqrb = _q3b - _q1b
        _xrng = [max(_bpa.min(), _q1b - 1.5 * _iqrb) - _iqrb * 0.15,
                 min(_bpa.max(), _q3b + 1.5 * _iqrb) + _iqrb * 0.15]
    fig_b.update_layout(
        title=dict(text="Boxplot (tendencia central MAD)", font=dict(size=11)),
        yaxis=dict(title=dict(text="mm/d", font=dict(size=9)),
                   tickfont=dict(size=8), range=_xrng),
        xaxis=dict(tickfont=dict(size=8)),
        template="plotly_white", height=160, width=480,
        margin=dict(l=40, r=8, t=28, b=28), showlegend=False)
    hb = fig_b.to_html(include_plotlyjs=False, full_html=False,
                       config={"displayModeBar": False})

    ref_h = ""
    if ref:
        ref_h = (f'<div style="font-size:9px;color:#666;margin-top:2px;">'
                 f'Ref MATLAB: {ref["min"]}–{ref["max"]} mm/d '
                 f'(prom {ref["mean"]})</div>')
    js = _JS_TMPL_MAD.replace("__DATA__", _json.dumps(raw))

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
<div class="hdr"><h3>&#128205; {tc}</h3><span class="badge">{tp['USCS']}</span></div>
<div class="info">
  <b>UTM 19S:</b> {utm_c['easting']}E, {utm_c['northing']}N &nbsp;|&nbsp;
  <b>Prof:</b> {ds_str}<br>
  <b>IDIEM:</b> &lambda;={tp['lambda_sediment']:.3f} W/m&middot;K |
  C={tp['C_sediment']/1e6:.3f} MJ/m&sup3;&middot;K |
  &alpha;={tp['alpha_e']:.2e} m&sup2;/s
</div>
<div class="chart-box">{ht}</div>
<div class="chart-box">{hf}</div>
<div id="rng-info">Ventana: serie completa &mdash; mueva el slider o use botones</div>
<div class="chart-box">{hb}</div>
<div class="mc">
  <b>Flujo Hatch-Amp (mm/d) &mdash; tendencia central MAD:</b>
  <table><thead><tr>
    <th>Par</th><th>Q1</th><th>Mediana</th><th>Q3</th><th>Promedio</th><th>n</th>
  </tr></thead>
  <tbody id="stats-body"></tbody></table>
  {ref_h}
</div>
{js}
</body></html>"""


def gen_panel_tendencia_central_mad(df_aligned, flux_ts_results):
    """Genera mapa SIG interactivo con datos MAD-filtrados (satélite por defecto)."""
    from branca.element import Element

    filtered_series = _apply_mad_filter(flux_ts_results)

    tc_list = list(STATION_COORDS_UTM.keys())
    clat = np.mean([_coords_wgs84[t]["lat"] for t in tc_list])
    clon = np.mean([_coords_wgs84[t]["lon"] for t in tc_list])

    m2 = folium.Map(location=[clat, clon], zoom_start=14, tiles=None,
                    control_scale=True)

    # CSS: tooltips transparentes con halo de texto
    m2.get_root().header.add_child(Element(
        "<style>"
        ".leaflet-tooltip { background: none !important; border: none !important; "
        "box-shadow: none !important; padding: 0 !important; }"
        ".leaflet-tooltip::before { display: none !important; }"
        "</style>"
    ))

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/"
              "World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri", name="Satélite ESRI", max_zoom=19, show=True).add_to(m2)
    folium.TileLayer(
        tiles="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
        attr="OpenTopoMap", name="Topográfico", show=False).add_to(m2)
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/"
              "Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}",
        attr="Esri Labels", name="Etiquetas", overlay=True).add_to(m2)

    _tooltip_dir = {"TC3": "left", "TC4": "right"}
    _halo = ("text-shadow:-2px -2px 0 #fff, 2px -2px 0 #fff, "
             "-2px 2px 0 #fff, 2px 2px 0 #fff, 0 -2px 0 #fff, "
             "0 2px 0 #fff, -2px 0 0 #fff, 2px 0 0 #fff, "
             "-1px -1px 0 #fff, 1px -1px 0 #fff, "
             "-1px 1px 0 #fff, 1px 1px 0 #fff;")
    for st, wgs in _coords_wgs84.items():
        html_pop = _build_popup_mad(st, df_aligned, filtered_series)
        iframe = folium.IFrame(html=html_pop, width=520, height=800)
        popup = folium.Popup(iframe, max_width=530)
        folium.Marker(
            location=[wgs["lat"], wgs["lon"]], popup=popup,
            tooltip=folium.Tooltip(
                f"{st} ({THERMAL_PARAMS_LAB[st]['USCS']})",
                permanent=True,
                direction=_tooltip_dir.get(st, "auto"),
                offset=(0, -5),
                style=(f"font-size:12px;font-weight:bold;color:black;"
                       f"background:transparent;border:none;box-shadow:none;"
                       f"padding:0;{_halo}"),
            ),
            icon=folium.Icon(color="red", icon="thermometer-half", prefix="fa"),
        ).add_to(m2)

    ordered = ["TC5", "TC4", "TC3", "TC2", "TC1"]
    folium.PolyLine(
        [[_coords_wgs84[s]["lat"], _coords_wgs84[s]["lon"]]
         for s in ordered if s in _coords_wgs84],
        color="cyan", weight=3, opacity=0.7,
        dash_array="10", tooltip="Perfil del río").add_to(m2)

    folium.plugins.MeasureControl(position="bottomleft").add_to(m2)
    folium.plugins.Fullscreen().add_to(m2)
    folium.plugins.MiniMap(toggle_display=True).add_to(m2)
    folium.LayerControl().add_to(m2)

    map_path = IMG_DIR / "panel_sig_tendencia_central_mad.html"
    m2.save(str(map_path))
    print(f"  ✔ Panel SIG tendencia central MAD: {map_path.name}")


# ══════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════
def main():
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    print("═" * 70)
    print(" PANELES 05A — HTML Interactivos ".center(70, "═"))
    print("═" * 70)

    # Ejecutar pipeline para obtener datos en memoria
    print("\n[0/3] Ejecutando pipeline de datos...")
    sensors = pipe.load_sensors()
    df_raw, df_aligned, _ = pipe.prepare_data(sensors)
    harmonic_results = pipe.run_harmonic_analysis(df_aligned)
    all_flux_results, _, df_results, flujos_promedio_tc = pipe.calculate_fluxes(
        df_aligned, harmonic_results)
    flux_ts_results = pipe.compute_flux_timeseries(df_aligned, df_raw)

    # Exportar datos necesarios (para selectores HTML independientes)
    df_iqr = pipe.compute_iqr(flux_ts_results)
    df_ic, _ = pipe.compute_reliability(all_flux_results, harmonic_results)
    df_uncertainty = pipe.compute_uncertainty(all_flux_results, harmonic_results)
    pipe.export_results(df_results, flujos_promedio_tc, df_iqr, df_ic,
                        df_uncertainty, harmonic_results)

    # Generar paneles
    all_data = _load_flux_ts_csvs()

    print("\n[1/4] Selectores interactivos por TC...")
    gen_selectors(all_data)

    print("[2/4] Perfil del río...")
    gen_perfil_rio(flujos_promedio_tc)

    print("[3/4] Panel SIG integrado...")
    gen_panel_sig(df_aligned, flux_ts_results, all_flux_results)

    print("[4/4] Panel SIG tendencia central MAD...")
    gen_panel_tendencia_central_mad(df_aligned, flux_ts_results)

    print(f"\n✔ Todos los paneles HTML exportados a {IMG_DIR.relative_to(PROJECT_ROOT)}/")


if __name__ == "__main__":
    main()
