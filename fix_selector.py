"""Rewrite cell 29 (interactive selector) with real-time JS stats update."""
import json

path = "notebooks/05A_datos_terreno.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

NEW_CODE = r'''# ==========================================================================
# CELDA 11c: Selector interactivo de ventana temporal — HTML + JS
# ==========================================================================
# Genera archivos HTML autocontenidos con Plotly.js donde la tabla de
# estadísticos se actualiza AL INSTANTE cuando el usuario mueve el
# range-slider o pulsa los botones de rango.
# ==========================================================================
import json as _json
from IPython.display import display, HTML as IHTML

# ---------- Cargar datos (reutiliza all_data de celda anterior) ----------
try:
    _ = all_data
except NameError:
    BASE_TS = project_root / "resultados_python" / "terreno_2026_hatch" / "series_temporales"
    PAIRS = ["sup_int", "int_inf", "sup_inf"]
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
            df["flux_ms"] = df["flux_hatch_amplitude_mm_day"] / 1000.0 / 86400.0
            mask = df["flux_ms"].notna() & np.isfinite(df["flux_ms"])
            all_data[tc][pair] = df.loc[mask, ["datetime", "flux_ms",
                                                "flux_hatch_amplitude_mm_day"]].copy()

MS_TO_MM_DAY = 1000.0 * 86400.0

PAIRS = ["sup_int", "int_inf", "sup_inf"]
pair_labels = {
    "sup_int": "Sup \u2192 Int  (z\u2081\u2013z\u2082)",
    "int_inf": "Int \u2192 Inf  (z\u2082\u2013z\u2083)",
    "sup_inf": "Sup \u2192 Inf  (z\u2081\u2013z\u2083)",
}
pair_colors = {"sup_int": "#0072BD", "int_inf": "#D95319", "sup_inf": "#EDB120"}

html_template = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Selector Ventana Temporal - {tc}</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; background: #fafafa; }}
#chart {{ width: 100%%; max-width: 1100px; margin: 0 auto; }}
#stats-table {{ width: 100%%; max-width: 1100px; margin: 15px auto; border-collapse: collapse; }}
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

// Build traces
var traces = [];
PAIRS.forEach(function(pair) {{
  if (!DATA[pair]) return;
  traces.push({{
    x: DATA[pair].dt, y: DATA[pair].flux_ms,
    mode: 'lines+markers', name: PAIR_LABELS[pair],
    line: {{color: PAIR_COLORS[pair], width: 1.5}},
    marker: {{size: 4}},
    legendgroup: pair
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
    ]}},
    type: 'date'
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
    info.textContent = 'Ventana: ' + d0.toLocaleDateString('es-CL') + ' \u2013 ' + d1.toLocaleDateString('es-CL');
  }} else {{
    info.textContent = 'Ventana: serie completa';
  }}

  PAIRS.forEach(function(pair) {{
    if (!DATA[pair]) return;
    var dt = DATA[pair].dt, v = DATA[pair].flux_ms;
    var filtered = [];
    for (var i = 0; i < dt.length; i++) {{
      if ((!xMin || dt[i] >= xMin) && (!xMax || dt[i] <= xMax)) {{
        filtered.push(v[i]);
      }}
    }}
    if (filtered.length === 0) return;
    var q1 = percentile(filtered, 25);
    var med = percentile(filtered, 50);
    var q3 = percentile(filtered, 75);
    var mean = filtered.reduce(function(a,b){{return a+b;}},0) / filtered.length;
    var iqr = q3 - q1;
    var row = '<tr>' +
      '<td style="font-weight:bold;color:' + PAIR_COLORS[pair] + '">' + PAIR_LABELS[pair] + '</td>' +
      '<td>' + med.toExponential(3) + '</td>' +
      '<td>' + mean.toExponential(3) + '</td>' +
      '<td>' + q1.toExponential(3) + '</td>' +
      '<td>' + q3.toExponential(3) + '</td>' +
      '<td>' + iqr.toExponential(3) + '</td>' +
      '<td>' + (med * MS_TO_MMD).toFixed(1) + '</td>' +
      '<td>' + (mean * MS_TO_MMD).toFixed(1) + '</td>' +
      '<td>' + filtered.length + '</td></tr>';
    tbody.innerHTML += row;
  }});
}}

// Initial stats (full series)
updateStats(null, null);

// Update on range change
document.getElementById('chart').on('plotly_relayout', function(ev) {{
  var xMin = ev['xaxis.range[0]'] || (ev['xaxis.range'] && ev['xaxis.range'][0]) || null;
  var xMax = ev['xaxis.range[1]'] || (ev['xaxis.range'] && ev['xaxis.range'][1]) || null;
  if (ev['xaxis.autorange']) {{ xMin = null; xMax = null; }}
  updateStats(xMin, xMax);
}});
</script>
</body>
</html>"""

out_dir_html = project_root / "image" / "terreno_2026"
out_dir_html.mkdir(parents=True, exist_ok=True)

for tc in ACTIVE_TCS:
    if tc not in all_data or not all_data[tc]:
        continue

    # Prepare JSON data for embedding
    tc_data = {}
    for pair in PAIRS:
        if pair not in all_data[tc]:
            continue
        d = all_data[tc][pair]
        tc_data[pair] = {
            "dt": d["datetime"].dt.strftime("%Y-%m-%dT%H:%M:%S").tolist(),
            "flux_ms": d["flux_ms"].round(10).tolist(),
        }

    html_content = html_template.format(
        tc=tc,
        data_json=_json.dumps(tc_data),
        pairs_json=_json.dumps(PAIRS),
        pair_labels_json=_json.dumps(pair_labels),
        pair_colors_json=_json.dumps(pair_colors),
        ms_to_mmd=MS_TO_MM_DAY,
    )

    out_html = out_dir_html / f"selector_ventana_{tc}.html"
    out_html.write_text(html_content, encoding="utf-8")
    print(f"\u2714 {tc}: selector interactivo \u2192 {out_html.relative_to(project_root)}")

    # Mostrar resumen en notebook
    n_pairs = len(tc_data)
    n_pts = sum(len(v["flux_ms"]) for v in tc_data.values())
    display(IHTML(
        f'<div style="padding:8px;background:#eef;border-radius:6px;margin:4px 0">'
        f'<b>{tc}</b> \u2014 {n_pairs} pares, {n_pts} puntos. '
        f'<a href="{out_html.relative_to(project_root)}" target="_blank">'
        f'Abrir selector interactivo</a></div>'
    ))

print("\n\u2714 Selectores interactivos generados para todas las TCs")
print("  \u2192 Abra los archivos HTML en el navegador.")
print("  \u2192 Mueva el range-slider inferior para ajustar la ventana temporal.")
print("  \u2192 La tabla de estad\u00edsticos se actualiza autom\u00e1ticamente.")
print("  \u2192 Unidades: m/s (investigaci\u00f3n) y mm/d (comparaci\u00f3n MATLAB).")
'''

# Find and replace cell 29 (the one with "CELDA 11c")
found = False
for cell in nb["cells"]:
    if cell["cell_type"] != "code":
        continue
    src = "".join(cell["source"])
    if "CELDA 11c" in src:
        # Convert the new code to source lines
        lines = NEW_CODE.split("\n")
        source = []
        for i, line in enumerate(lines):
            if i < len(lines) - 1:
                source.append(line + "\n")
            else:
                source.append(line)  # last line without \n
        cell["source"] = source
        found = True
        print("Found and replaced cell 29 (CELDA 11c)")
        break

if not found:
    print("ERROR: Could not find CELDA 11c cell!")

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Notebook saved successfully")
