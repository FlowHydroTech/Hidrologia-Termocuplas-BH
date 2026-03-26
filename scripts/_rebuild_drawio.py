"""Reescribir hoja 'Pipeline VFLUX2 Python' del drawio.

Versión profesional para cliente: 4 fases (swimlanes),
sin código, numeración limpia, alto nivel.
"""
import pathlib, shutil, textwrap

DRAWIO = pathlib.Path(r"Diagrama/diagrama_proceso.drawio")
shutil.copy2(DRAWIO, DRAWIO.with_suffix(".drawio.bak2"))

# Leer la primera hoja (Cap. 4) y preservarla intacta
raw = DRAWIO.read_text(encoding="utf-8")
# Extraer primer <diagram>...</diagram>
import re
m = re.search(r'(<diagram\s+id="cap4-simplificado".*?</diagram>)', raw, re.DOTALL)
sheet1 = m.group(1) if m else ""

# ── Construir hoja 2 completa ────────────────────────────
# Paleta profesional
AZUL_FASE   = "#1565C0"   # borde fases
AZUL_BG1    = "#E3F2FD"   # Fase 1
VERDE_BG2   = "#E8F5E9"   # Fase 2
AMBAR_BG3   = "#FFF8E1"   # Fase 3
INDIGO_BG4  = "#EDE7F6"   # Fase 4

# Colores cajas
C_AZUL   = "#dae8fc"    ; B_AZUL   = "#6c8ebf"
C_VERDE  = "#d5e8d4"    ; B_VERDE  = "#82b366"
C_AMAR   = "#fff2cc"    ; B_AMAR   = "#d6b656"
C_ROJO   = "#f8cecc"    ; B_ROJO   = "#b85450"
C_LILA   = "#e1d5e7"    ; B_LILA   = "#9673a6"
C_GRIS   = "#f5f5f5"    ; B_GRIS   = "#666666"
C_NARANJA= "#ffe6cc"    ; B_NARANJA= "#d79b00"
C_INDIGO = "#e8eaf6"    ; B_INDIGO = "#3f51b5"
C_LIMA   = "#c8e6c9"    ; B_LIMA   = "#388e3c"
C_CYAN   = "#E1F5FE"    ; B_CYAN   = "#0288D1"

# Estilos base
STYLE_TITLE = "text;html=1;align=center;verticalAlign=middle;whiteSpace=wrap;fontSize=20;fontColor=#1a1a2e;fontFamily=Arial;fontStyle=1;"
STYLE_SUBTITLE = "text;html=1;align=center;verticalAlign=middle;whiteSpace=wrap;fontSize=12;fontColor=#546E7A;fontFamily=Arial;"

def swimlane(bg_color, label_color):
    return (f"swimlane;startSize=40;horizontal=1;fillColor={bg_color};"
            f"strokeColor=#B0BEC5;strokeWidth=1;rounded=1;arcSize=6;"
            f"fontSize=14;fontColor={label_color};fontStyle=1;fontFamily=Arial;"
            f"html=1;whiteSpace=wrap;collapsible=0;swimlaneLine=0;shadow=0;")

def box(fill, stroke, extra=""):
    return (f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill};"
            f"strokeColor={stroke};strokeWidth=2;fontSize=11;"
            f"align=center;verticalAlign=middle;shadow=1;fontFamily=Arial;{extra}")

def box_sm(fill, stroke, extra=""):
    return (f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill};"
            f"strokeColor={stroke};strokeWidth=1;fontSize=10;"
            f"align=center;verticalAlign=middle;shadow=0;fontFamily=Arial;{extra}")

ARROW = ("edgeStyle=orthogonalEdgeStyle;rounded=1;strokeWidth=2;"
         "strokeColor=#37474F;targetPerimeterSpacing=6;sourcePerimeterSpacing=6;")
ARROW_DASH = ARROW + "dashed=1;dashPattern=8 4;"
LBL = "edgeLabel;html=1;fontSize=9;fontColor=#78909C;fontFamily=Arial;align=center;"

# ── Coordenadas clave ─────────────────────────────────────
PW, PH = 1500, 1200    # página
MX = 40                 # margen X
SW = PW - 2*MX         # ancho swimlane = 1420

Y_TITLE = 15
Y_F1 = 80;  H_F1 = 190
Y_F2 = 290; H_F2 = 220
Y_F3 = 530; H_F3 = 190
Y_F4 = 740; H_F4 = 210
Y_FOOTER = 970

# Caja ancho estándar
BW = 270; BH = 100

# Helper
cells = []
cid = [0]

def _id():
    cid[0] += 1
    return f"p{cid[0]}"

def add_cell(parent, value, style, x, y, w, h, vertex=True, edge=False, **kw):
    i = _id()
    cells.append((i, parent, value, style, x, y, w, h, vertex, edge, kw))
    return i

def add_edge(parent, source, target, style, label=None, **kw):
    i = _id()
    cells.append((i, parent, "", style, 0, 0, 0, 0, False, True,
                   {"source": source, "target": target, "label": label, **kw}))
    return i

# ── ROOT ──────────────────────────────────────────────────
ROOT_PARENT = "1"

# Título
add_cell(ROOT_PARENT,
    "<b>Pipeline de Procesamiento — Método VFLUX2</b>",
    STYLE_TITLE, 200, Y_TITLE, 1100, 35)
add_cell(ROOT_PARENT,
    ("Estimación de flujo vertical río–acuífero mediante señal térmica"
     "<br>Río Cuncumén / Silala  |  Dic 2025 – Feb 2026  |  5 estaciones termocuplas"
     '<br><font color="#388E3C">Actualizado 25-Mar-2026</font>'),
    STYLE_SUBTITLE, 200, Y_TITLE+35, 1100, 40)

# ═══════════════════════════════════════════════════════════
# FASE 1 — ADQUISICIÓN Y PARÁMETROS
# ═══════════════════════════════════════════════════════════
f1 = add_cell(ROOT_PARENT,
    "<b>FASE 1  —  ADQUISICIÓN Y PARÁMETROS DE ENTRADA</b>",
    swimlane(AZUL_BG1, "#1565C0"), MX, Y_F1, SW, H_F1)

bx = 30; by = 55
b1 = add_cell(f1,
    "<b>1. Instrumentación</b><hr size='1'>"
    "15 sensores iButton (DS1922L / DS1923)<br>"
    "5 estaciones termocupla (TC1–TC5)<br>"
    "3 profundidades por estación",
    box(C_AZUL, B_AZUL), bx, by, BW, BH)

b2 = add_cell(f1,
    "<b>2. Registro de Campo</b><hr size='1'>"
    "Frecuencia: cada 30 minutos<br>"
    "Periodo: 21-Dic-2025 a 25-Feb-2026<br>"
    "Formato: archivos CSV por sensor",
    box(C_AZUL, B_AZUL), bx + BW + 80, by, BW, BH)

b3 = add_cell(f1,
    "<b>3. Parámetros Térmicos</b><hr size='1'>"
    "Conductividad λ (IDIEM)<br>"
    "Capacidad calórica Cs (IDIEM)<br>"
    "Dispersividad β (d50 granulométrico)",
    box(C_ROJO, B_ROJO), bx + 2*(BW + 80), by, BW, BH)

b4 = add_cell(f1,
    "<b>Laboratorio IDIEM</b><br>U. de Chile",
    box_sm("#FFF", B_ROJO, "fontStyle=2;"), bx + 2*(BW + 80) + BW + 30, by + 10, 150, 55)

add_edge(f1, b1, b2, ARROW, "CSV brutos")
add_edge(f1, b4, b3, ARROW_DASH)

# ═══════════════════════════════════════════════════════════
# FASE 2 — PROCESAMIENTO
# ═══════════════════════════════════════════════════════════
f2 = add_cell(ROOT_PARENT,
    "<b>FASE 2  —  PROCESAMIENTO Y CÁLCULO</b>",
    swimlane(VERDE_BG2, "#2E7D32"), MX, Y_F2, SW, H_F2)

by2 = 55
b5 = add_cell(f2,
    "<b>4. Preprocesamiento</b><hr size='1'>"
    "Alineación temporal (30 min)<br>"
    "Control de calidad<br>"
    "Remoción de artefactos",
    box(C_VERDE, B_VERDE), bx, by2, BW, BH)

b6 = add_cell(f2,
    "<b>5. Análisis Armónico</b><hr size='1'>"
    "Ajuste sinusoidal (P = 24 h)<br>"
    "Extracción: amplitud, fase, R²<br>"
    "15 pares de sensores",
    box(C_AMAR, B_AMAR), bx + BW + 60, by2, BW, BH)

b7 = add_cell(f2,
    "<b>6. Estimación de Flujo</b><hr size='1'>"
    "Método Hatch-Amplitude (Eq. 6a)<br>"
    "Validación: McCallum et al.<br>"
    "Incluye dispersividad térmica",
    box(C_LILA, B_LILA), bx + 2*(BW + 60), by2, BW, BH)

b8 = add_cell(f2,
    "<b>7. Series Temporales</b><hr size='1'>"
    "Ventana deslizante 48 h / paso 12 h<br>"
    "Flujo estimado cada 12 h<br>"
    "15 pares × 5 estaciones",
    box(C_LIMA, B_LIMA), bx + 3*(BW + 60), by2, BW, BH)

add_edge(f2, b5, b6, ARROW, "Series alineadas")
add_edge(f2, b6, b7, ARROW, "Amplitud y fase")
add_edge(f2, b7, b8, ARROW, "Flujos por par")

# Flecha entre fases (F1 → F2)
f1_f2_src = b2
f1_f2_tgt = b5
# Se crea a nivel root para cruzar swimlanes
add_edge(ROOT_PARENT, f1_f2_src, f1_f2_tgt, ARROW + "exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;")
# Parámetros → Flujo
add_edge(ROOT_PARENT, b3, b7, ARROW_DASH + "exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;", "Parámetros térmicos")

# ═══════════════════════════════════════════════════════════
# FASE 3 — ANÁLISIS Y VALIDACIÓN
# ═══════════════════════════════════════════════════════════
f3 = add_cell(ROOT_PARENT,
    "<b>FASE 3  —  ANÁLISIS ESTADÍSTICO Y VALIDACIÓN</b>",
    swimlane(AMBAR_BG3, "#F57F17"), MX, Y_F3, SW, H_F3)

by3 = 55
b9 = add_cell(f3,
    "<b>8. Métricas de Calidad</b><hr size='1'>"
    "Índice de Confiabilidad (IC)<br>"
    "Propagación de incertidumbre<br>"
    "Tabla IQR por estación",
    box(C_GRIS, B_GRIS), bx, by3, BW, BH)

b10 = add_cell(f3,
    "<b>9. Filtro Estadístico (MAD)</b><hr size='1'>"
    "Desviación Absoluta Mediana (2.5σ)<br>"
    "Suavizado mediana móvil (w = 5)<br>"
    "Tendencia central por estación",
    box(C_CYAN, B_CYAN), bx + BW + 80, by3, BW, BH)

b11 = add_cell(f3,
    "<b>10. Validación Cruzada</b><hr size='1'>"
    "Comparación Python vs MATLAB VFLUX2<br>"
    "Δ%: ±2% (TC2) a ±20% (TC1,TC5)<br>"
    "Incertidumbre promedio: ±17.3%",
    box(C_NARANJA, B_NARANJA), bx + 2*(BW + 80), by3, BW, BH)

# Resultado destacado
b_res = add_cell(f3,
    "<b>Resultado: 443 mm/día ↓</b> (infiltración río → acuífero)<br>"
    "Rango: 220 – 678 mm/día según estación",
    box_sm("#E8F5E9", "#388E3C", "fontSize=11;fontStyle=0;"),
    bx + 3*(BW + 80), by3 + 10, 200, 80)

add_edge(f3, b9, b10, ARROW)
add_edge(f3, b10, b11, ARROW)
add_edge(f3, b11, b_res, ARROW_DASH)

# Flechas F2 → F3
add_edge(ROOT_PARENT, b7, b9,
    ARROW + "exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;",
    "Flujos estimados")
add_edge(ROOT_PARENT, b8, b10,
    ARROW_DASH + "exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;",
    "Series temporales")

# ═══════════════════════════════════════════════════════════
# FASE 4 — PRODUCTOS DE SALIDA
# ═══════════════════════════════════════════════════════════
f4 = add_cell(ROOT_PARENT,
    "<b>FASE 4  —  PRODUCTOS DE SALIDA</b>",
    swimlane(INDIGO_BG4, "#4527A0"), MX, Y_F4, SW, H_F4)

by4 = 55
b12 = add_cell(f4,
    "<b>Informes y Tablas</b><hr size='1'>"
    "Excel consolidado (7 hojas)<br>"
    "Tablas CSV por estación<br>"
    "Resumen ejecutivo",
    box(C_INDIGO, B_INDIGO), bx, by4, 220, BH)

b13 = add_cell(f4,
    "<b>Figuras y Gráficos</b><hr size='1'>"
    "Series de temperatura (5 TC)<br>"
    "Barras IQR, boxplot, forest-plot<br>"
    "Tendencia central MAD-filtrada",
    box(C_NARANJA, B_NARANJA), bx + 250, by4, 220, BH)

b14 = add_cell(f4,
    "<b>Paneles Interactivos</b><hr size='1'>"
    "Mapa SIG (satélite + labels TC)<br>"
    "Panel tendencia central MAD<br>"
    "Selectores temporales por TC",
    box(C_LIMA, B_LIMA), bx + 500, by4, 220, BH)

b15 = add_cell(f4,
    "<b>3 Modos de Ejecución</b><hr size='1'>"
    "<font color='#388E3C'>A) Python Puro</font><br>"
    "<font color='#1565C0'>B) Prefect Orquestado</font><br>"
    "<font color='#E65100'>C) Docker Compose</font>",
    box("#FFF", "#546E7A", "strokeWidth=2;"), bx + 750, by4, 220, BH)

# Notebook
b16 = add_cell(f4,
    "<b>Notebook Reproducible</b><br>05A_datos_terreno.ipynb + Tests (9/9)",
    box_sm("#E3F2FD", "#1976D2"), bx + 1000, by4 + 15, 190, 55)

add_edge(f4, b12, b13, ARROW)
add_edge(f4, b13, b14, ARROW)
add_edge(f4, b14, b15, ARROW)
add_edge(f4, b15, b16, ARROW_DASH)

# Flechas F3 → F4
add_edge(ROOT_PARENT, b9, b12,
    ARROW + "exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;")
add_edge(ROOT_PARENT, b10, b14,
    ARROW_DASH + "exitX=0.5;exitY=1;exitDx=0;exitDy=0;entryX=0.5;entryY=0;entryDx=0;entryDy=0;")

# Footer
add_cell(ROOT_PARENT,
    ("<i>Metodología basada en VFLUX2 (Gordon et al., 2012) — Hatch et al. (2006) Eq. 6a"
     " + McCallum et al. (2012)"
     "<br>Propiedades térmicas: Laboratorio IDIEM, U. de Chile"
     "  |  11 etapas automatizadas  |  Filtro MAD  |  3 modos de ejecución"
     "<br>Proyecto Río Cuncumén / Silala 2025-2026  |  Actualizado 25-Mar-2026</i>"),
    "text;html=1;align=center;verticalAlign=middle;whiteSpace=wrap;fontSize=10;fontColor=#90A4AE;fontFamily=Arial;",
    200, Y_FOOTER, 1100, 50)

# ── Serializar XML ────────────────────────────────────────
def esc(s):
    return (s.replace("&", "&amp;").replace('"', "&quot;")
             .replace("<", "&lt;").replace(">", "&gt;")
             .replace("'", "&apos;"))

lines = []
lines.append('    <diagram id="vflux2-pipeline" name="Pipeline VFLUX2 Python">')
lines.append(f'        <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" '
             f'tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
             f'pageWidth="{PW}" pageHeight="{PH}" math="0" shadow="0">')
lines.append('            <root>')
lines.append('                <mxCell id="0"/>')
lines.append('                <mxCell id="1" parent="0"/>')

for (cid_val, parent, value, style, x, y, w, h, vertex, edge, kw) in cells:
    # Escape value for XML attribute (but value already uses HTML entities via < > etc.)
    # Actually our values use literal <b> etc. — need to escape for XML attribute
    val_esc = esc(value) if value else ""
    style_esc = style  # styles don't need escaping
    
    if edge:
        src = kw.get("source", "")
        tgt = kw.get("target", "")
        lbl = kw.get("label")
        lines.append(f'                <mxCell id="{cid_val}" value="" '
                     f'style="{style_esc}" parent="{parent}" '
                     f'source="{src}" target="{tgt}" edge="1">')
        lines.append(f'                    <mxGeometry relative="1" as="geometry"/>')
        lines.append(f'                </mxCell>')
        if lbl:
            lbl_id = cid_val + "_lbl"
            lbl_esc = esc(lbl)
            lines.append(f'                <mxCell id="{lbl_id}" value="{lbl_esc}" '
                         f'style="{LBL}" parent="{cid_val}" vertex="1" connectable="0">')
            lines.append(f'                    <mxGeometry relative="1" as="geometry"/>')
            lines.append(f'                </mxCell>')
    elif vertex:
        lines.append(f'                <mxCell id="{cid_val}" value="{val_esc}" '
                     f'style="{style_esc}" parent="{parent}" vertex="1">')
        lines.append(f'                    <mxGeometry x="{x}" y="{y}" '
                     f'width="{w}" height="{h}" as="geometry"/>')
        lines.append(f'                </mxCell>')

lines.append('            </root>')
lines.append('        </mxGraphModel>')
lines.append('    </diagram>')

sheet2 = "\n".join(lines)

# ── Escribir archivo final ────────────────────────────────
output = f"""<mxfile host="65bd71144e">
    {sheet1}
{sheet2}
</mxfile>"""

DRAWIO.write_text(output, encoding="utf-8")
print("✅ Diagrama reescrito — versión profesional cliente")
print(f"   {len(cells)} elementos  |  4 fases (swimlanes)")
print(f"   Página {PW}×{PH}  |  Backup → .drawio.bak2")
