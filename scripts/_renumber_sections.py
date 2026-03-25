"""Renumera secciones del notebook 05A para entrega al cliente.
Ejecutar UNA VEZ cuando el notebook esté guardado en disco."""
import json, re, pathlib

NB = pathlib.Path(r"c:\Users\cesar.godoy\Hidrologia-Termocuplas-BH\notebooks\05A_datos_terreno.ipynb")
nb = json.loads(NB.read_text(encoding="utf-8"))

# --- Mapa de renumeración: viejo → nuevo ---
RENAME = {
    7: 6,  8: 7,  9: 8, 10: 9,  11: 10,
    12: 11, 13: 12, 14: 13, 15: 14, 16: 15,
}
# Primera §17 → §16, segunda §17 se queda como §17
first_17_done = False

for cell in nb["cells"]:
    if cell["cell_type"] != "markdown":
        continue
    src = cell["source"]
    new_src = []
    for line in src:
        # Patron: "## 7. Tabla" o "## §19 —"
        m = re.match(r"(##\s+)(\d+)\.\s", line)
        if m:
            old_num = int(m.group(2))
            if old_num in RENAME:
                line = line.replace(f"{m.group(1)}{old_num}.", f"{m.group(1)}{RENAME[old_num]}.", 1)
            elif old_num == 17 and not first_17_done:
                line = line.replace("## 17.", "## 16.", 1)
                first_17_done = True
            # §17 segunda, §18, §19: permanecen igual
        new_src.append(line)
    cell["source"] = new_src

# --- También renumerar "# §19" en celdas de código (comentario) ---
# No es necesario, §19 permanece como §19

# --- Actualizar tabla de índice ---
for cell in nb["cells"]:
    if cell["cell_type"] != "markdown":
        continue
    joined = "".join(cell["source"])
    if "Índice de Secciones" in joined:
        new_index = [
            "---\n",
            "## Índice de Secciones\n",
            "\n",
            "| § | Sección | Contenido |\n",
            "|:-:|:--------|:----------|\n",
            "| 1 | Carga de Datos y Configuración | Imports, carga de Excel TC1–TC5 |\n",
            "| 2 | Configuración Maestra | TC_CONFIG, parámetros IDIEM, profundidades |\n",
            "| 3 | Preparación de Datos | Alineación temporal, remuestreo 30 min |\n",
            "| 4 | Series de Temperatura | Figuras combinadas e individuales por TC |\n",
            "| 5 | Análisis Armónico | Ajuste sinusoidal, R², visualización |\n",
            "| 6 | Cálculo de Flujo y Tabla de Resultados | Hatch-Amplitude + McCallum, 15 pares |\n",
            "| 7 | Visualizaciones | Boxplot, barras, IC 95 % (forest-plot) |\n",
            "| 8 | Series Temporales de Flujo | Ventanas deslizantes 48 h / 12 h, selectores |\n",
            "| 9 | Métricas de Confiabilidad | Índice IC (0–1) por par |\n",
            "| 10 | Propagación de Incertidumbre | Props IDIEM, IC 95 % |\n",
            "| 11 | Exportación de Resultados | Excel multi-hoja + CSVs |\n",
            "| 12 | Resumen Ejecutivo | Síntesis final |\n",
            "| 13 | Perfil de Flujo | Plotly interactivo aguas arriba → abajo |\n",
            "| 14 | Boxplot Publicación | Estilo informe, 300 DPI |\n",
            "| 15 | Series Temporales Publicación | Panel 5×1 estilo informe |\n",
            "| 16 | Panel SIG Integrado | Folium + selector temporal + tabla IQR dinámica |\n",
            "| 17 | Series Temporales — Tendencia Central | Filtrado MAD, suavizado mediana móvil |\n",
            "| 18 | Boxplot Vertical — Tendencia Central | Datos MAD, sin outliers |\n",
            "| 19 | Mapa SIG — Tendencia Central MAD | Folium satélite + popup interactivo |\n",
            "\n",
            "> **Ejecución directa:** Los scripts `scripts/pipeline_05A.py`, `scripts/figuras_05A.py` y `scripts/paneles_05A.py` permiten ejecutar el análisis completo sin abrir el notebook.\n",
        ]
        cell["source"] = new_index
        break

# --- Renombrar §7 a §6 con título más apropiado ---
for cell in nb["cells"]:
    if cell["cell_type"] != "markdown":
        continue
    joined = "".join(cell["source"])
    if "6. Tabla de Resultados" in joined:
        cell["source"] = [
            line.replace(
                "## 6. Tabla de Resultados — Hatch-Amplitude vs McCallum",
                "## 6. Cálculo de Flujo y Tabla de Resultados — Hatch-Amplitude vs McCallum",
            )
            for line in cell["source"]
        ]
        break

NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print("OK — notebook renumerado: §1-§19 consecutivas, índice actualizado.")
