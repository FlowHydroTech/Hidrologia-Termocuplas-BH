"""Actualizar diagrama_proceso.drawio — hoja 'Pipeline VFLUX2 Python'.

Cambios 25-Mar-2026:
  1. Fecha 18-Mar → 25-Mar-2026
  2. Título: + Filtro MAD + 3 Modos Ejecución
  3. g7 Visualizaciones: +110 px, nuevas celdas MAD
  4. s7_map: satélite defecto + labels TC permanentes
  5. g11 → 3 Modos de Ejecución (Python / Prefect / Docker)
  6. Footer actualizado (11 etapas, MAD, 3 modos)
  7. Desplaza bloques g8-g12 + nota +110 px
"""
import re, pathlib, shutil

DRAWIO = pathlib.Path(r"Diagrama/diagrama_proceso.drawio")
SHIFT = 110

# Backup
shutil.copy2(DRAWIO, DRAWIO.with_suffix(".drawio.bak"))
xml = DRAWIO.read_text(encoding="utf-8")


# ── Helpers ──────────────────────────────────────────────
def shift_y(xml, cell_id, dy):
    pat = rf'(<mxCell\s+id="{re.escape(cell_id)}".*?<mxGeometry\s[^>]*?\by=")(\d+)'
    def repl(m):
        return m.group(1) + str(int(m.group(2)) + dy)
    r = re.sub(pat, repl, xml, count=1, flags=re.DOTALL)
    return r


def shift_h(xml, cell_id, dh):
    pat = rf'(<mxCell\s+id="{re.escape(cell_id)}".*?<mxGeometry\s[^>]*?\bheight=")(\d+)'
    def repl(m):
        return m.group(1) + str(int(m.group(2)) + dh)
    return re.sub(pat, repl, xml, count=1, flags=re.DOTALL)


def set_val(xml, cell_id, new_val):
    pat = rf'(<mxCell\s+id="{re.escape(cell_id)}"\s+value=")[^"]*(")'
    def repl(m):
        return m.group(1) + new_val + m.group(2)
    r, n = re.subn(pat, repl, xml, count=1)
    if n == 0:
        print(f"  WARNING set_val: {cell_id} not found")
    return r


def set_style(xml, cell_id, new_style):
    pat = rf'(<mxCell\s+id="{re.escape(cell_id)}"[^>]*\bstyle=")[^"]*(")'
    def repl(m):
        return m.group(1) + new_style + m.group(2)
    return re.sub(pat, repl, xml, count=1)


# ── 1. Fecha global ─────────────────────────────────────
xml = xml.replace("18-Mar-2026", "25-Mar-2026")
print("[1] Fecha → 25-Mar-2026")

# ── 2. Subtítulo del título ─────────────────────────────
xml = xml.replace(
    "Ecuaci\u00f3n Hatch Eq.6a no-lineal (brentq) | 5 Termocuplas",
    "Hatch Eq.6a (brentq) | 5 TC | Filtro MAD | 3 Modos Ejecuci\u00f3n",
)
print("[2] Título actualizado")

# ── 3. g7 (Visualizaciones) más alto ────────────────────
xml = shift_h(xml, "g7", SHIFT)
print(f"[3] g7 height +{SHIFT}px")

# ── 4. s7_map → Panel SIG + satélite + labels ──────────
xml = set_val(
    xml, "s7_map",
    "&lt;b&gt;Panel SIG Integrado&lt;/b&gt; — Folium + sat\u00e9lite defecto "
    "+ labels TC permanentes + popups T\u00b0/flujo/IQR",
)
print("[4] s7_map actualizado")

# ── 5. Insertar celdas MAD antes de s7_export ──────────
MAD_CELLS = (
    '                <mxCell id="s7_mad1" '
    'value="&lt;b&gt;Tendencia Central MAD&lt;/b&gt; (threshold 2.5) '
    '\u2014 Series 5\u00d71 panel + boxplot agrupado | suavizado mediana w=5" '
    'style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E1F5FE;'
    'strokeColor=#0288D1;fontSize=10;" parent="1" vertex="1">\n'
    '                    <mxGeometry x="55" y="865" width="590" '
    'height="35" as="geometry"/>\n'
    '                </mxCell>\n'
    '                <mxCell id="s7_mad2" '
    'value="&lt;b&gt;Panel SIG Tendencia Central MAD&lt;/b&gt; '
    '\u2014 Mapa Folium MAD-filtrado + mediana m\u00f3vil por TC" '
    'style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E1F5FE;'
    'strokeColor=#0288D1;fontSize=10;" parent="1" vertex="1">\n'
    '                    <mxGeometry x="55" y="905" width="590" '
    'height="35" as="geometry"/>\n'
    '                </mxCell>\n'
)
xml = xml.replace(
    '                <mxCell id="s7_export"',
    MAD_CELLS + '                <mxCell id="s7_export"',
    1,
)
print("[5] Celdas MAD insertadas")

# ── 6. Desplazar s7_export y actualizar texto ───────────
xml = shift_y(xml, "s7_export", SHIFT)
xml = set_val(
    xml, "s7_export",
    "\u2192 PNG 150 dpi + 7 HTML interactivos "
    "\u2192 data/processed/resultados_20260325/",
)
print("[6] s7_export desplazado y actualizado")

# ── 7. Desplazar bloques inferiores ─────────────────────
ids_shift = [
    "g8", "g8_title", "s8a", "s8b", "s8c", "s8d",
    "g9", "g9_title", "s9a", "s9b", "s9c", "s9d",
    "g10", "g10_title", "s10a", "s10b", "s10c",
    "g11", "g11_title", "s11a", "s11b", "s11c",
    "g12", "g12_title", "s12a", "s12b", "s12c",
    "note1",
]
for sid in ids_shift:
    xml = shift_y(xml, sid, SHIFT)
print(f"[7] {len(ids_shift)} elementos desplazados +{SHIFT}px")

# ── 8. g11 → 3 Modos de Ejecución ──────────────────────
xml = set_val(xml, "g11_title",
              "&lt;b&gt;3 MODOS DE EJECUCI\u00d3N&lt;/b&gt;")
xml = set_val(xml, "s11a",
              "&lt;b&gt;A) Python Puro&lt;/b&gt;&lt;br&gt;"
              "python scripts/run_pipeline.py")
xml = set_val(xml, "s11b",
              "&lt;b&gt;B) Prefect Orquestado&lt;/b&gt;&lt;br&gt;"
              "prefect server start + prefect_pipeline.py")
xml = set_val(xml, "s11c",
              "&lt;b&gt;C) Docker Compose&lt;/b&gt;&lt;br&gt;"
              "docker compose up (3 servicios)")
xml = set_style(xml, "s11a",
    "rounded=1;whiteSpace=wrap;html=1;fillColor=#E8F5E9;"
    "strokeColor=#388E3C;fontSize=10;")
xml = set_style(xml, "s11b",
    "rounded=1;whiteSpace=wrap;html=1;fillColor=#E3F2FD;"
    "strokeColor=#1976D2;fontSize=10;")
xml = set_style(xml, "s11c",
    "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFF3E0;"
    "strokeColor=#E65100;fontSize=10;")
print("[8] g11 → 3 modos ejecución")

# ── 9. Footer ───────────────────────────────────────────
xml = set_val(
    xml, "note1",
    "&lt;i&gt;Pipeline VFLUX2 (Gordon et al., 2012) \u2014 "
    "Paquete vfluxx Python | Hatch Eq.6a + McCallum"
    "&lt;br&gt;11 etapas (scripts/stages/) | Filtro MAD (2.5) "
    "+ suavizado mediana | 3 modos ejecuci\u00f3n"
    "&lt;br&gt;Proyecto R\u00edo Silala 2025-2026 | "
    "Actualizado 25-Mar-2026&lt;/i&gt;",
)
print("[9] Footer actualizado")

# ── 10. Altura de página ────────────────────────────────
xml = xml.replace('pageHeight="1400"', 'pageHeight="1600"')
print("[10] pageHeight → 1600")

# ── Escribir ────────────────────────────────────────────
DRAWIO.write_text(xml, encoding="utf-8")
print(f"\n\u2705 Diagrama actualizado \u2192 {DRAWIO}")
print(f"   Backup \u2192 {DRAWIO.with_suffix('.drawio.bak')}")
