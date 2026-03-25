"""
Limpieza del notebook 05A_datos_terreno.ipynb:
  1. Backup del original
  2. Elimina celdas obsoletas (Folium antiguo §14)
  3. Renumera secciones de markdown (§15→§14, §16→§15, §17→§16, §18→§17)
  4. Renumera comentarios CELDA en código (secuencial 1–24)
  5. Agrega celda de Índice (TOC) después del header
  6. Limpia outputs y execution_count
  7. Guarda notebook limpio
"""

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NB_PATH = ROOT / "notebooks" / "05A_datos_terreno.ipynb"
BACKUP_PATH = ROOT / "notebooks" / "05A_datos_terreno_BACKUP.ipynb"

# 0-based indices of cells to REMOVE (old Folium §14)
REMOVE_INDICES = {39, 40}

# Section renumbering map for markdown headers
SECTION_REMAP = {15: 14, 16: 15, 17: 16, 18: 17}

# TOC to insert after the header cell (index 0)
TOC_SOURCE = [
    "---\n",
    "## Índice de Secciones\n",
    "\n",
    "| § | Sección | Celdas | Contenido |\n",
    "|:-:|:--------|:------:|:----------|\n",
    "| 1 | Carga de Datos y Configuración | 1 | Imports, carga de Excel TC1–TC5 |\n",
    "| 2 | Configuración Maestra | 2 | TC_CONFIG, parámetros IDIEM, profundidades |\n",
    "| 3 | Preparación de Datos | 3 | Alineación temporal, remuestreo 30 min |\n",
    "| 4 | Series de Temperatura | 4 | Figuras combinadas e individuales por TC |\n",
    "| 5 | Análisis Armónico | 5–6 | Ajuste sinusoidal, R², visualización |\n",
    "| 6 | Cálculo de Flujo | 7 | Hatch-Amplitude + McCallum, 15 pares |\n",
    "| 7 | Tabla de Resultados | 8 | Comparación HA vs MC, Python vs MATLAB |\n",
    "| 8 | Visualizaciones | 9–11 | Boxplot, barras, IC 95 % (forest-plot) |\n",
    "| 9 | Series Temporales de Flujo | 12–15 | Ventanas deslizantes 48 h / 12 h, selectores |\n",
    "| 10 | Métricas de Confiabilidad | 16 | Índice IC (0–1) por par |\n",
    "| 11 | Propagación de Incertidumbre | 17–18 | Props IDIEM, IC 95 % |\n",
    "| 12 | Exportación de Resultados | 19 | Excel multi-hoja + CSVs |\n",
    "| 13 | Resumen Ejecutivo | 20 | Síntesis final |\n",
    "| 14 | Perfil de Flujo | 21 | Plotly interactivo aguas arriba → abajo |\n",
    "| 15 | Boxplot Publicación | 22 | Estilo informe, 300 DPI |\n",
    "| 16 | Series Temporales Publicación | 23 | Panel 5×1 estilo informe |\n",
    "| 17 | Panel SIG Integrado | 24 | Folium + selector temporal + tabla IQR dinámica |\n",
    "\n",
    "> **Ejecución directa:** Los scripts `scripts/pipeline_05A.py`, "
    "`scripts/figuras_05A.py` y `scripts/paneles_05A.py` "
    "permiten ejecutar el análisis completo sin abrir el notebook.\n",
]

TOC_CELL = {
    "cell_type": "markdown",
    "id": "toc-05A-clean",
    "metadata": {},
    "source": TOC_SOURCE,
}


def fix_section_number(line):
    """Reemplaza ## 15. → ## 14., etc."""
    m = re.match(r'^(#{1,3}\s+)(\d+)(\.)', line)
    if m:
        old_num = int(m.group(2))
        if old_num in SECTION_REMAP:
            new_num = SECTION_REMAP[old_num]
            line = f"{m.group(1)}{new_num}{m.group(3)}" + line[m.end():]
    # Also fix "(sección N)" text references
    for old, new in SECTION_REMAP.items():
        line = line.replace(f"sección {old}", f"sección {new}")
        line = line.replace(f"§{old}", f"§{new}")
    return line


def fix_celda_comment(line, new_num):
    """Reemplaza '# CELDA 11b:' → '# CELDA 13:' etc."""
    # Pattern: '# CELDA <word>:' or '# CELDA <word> ('
    m = re.match(r'^(# CELDA )\S+(:.*)$', line)
    if m:
        desc = m.group(2)
        # Special case for AUDITORÍA — preserve label
        if 'AUDITORÍA' in line:
            return f"# CELDA {new_num} (AUDITORÍA){desc}\n"
        return f"# CELDA {new_num}{desc}\n"
    return line


def main():
    # Backup
    shutil.copy2(NB_PATH, BACKUP_PATH)
    print(f"✔ Backup: {BACKUP_PATH.name}")

    with open(NB_PATH, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    cells = nb['cells']
    n_before = len(cells)

    # 1. Remove obsolete cells
    new_cells = [c for i, c in enumerate(cells) if i not in REMOVE_INDICES]

    # 2. Fix section numbers in markdown cells
    for cell in new_cells:
        if cell['cell_type'] == 'markdown':
            cell['source'] = [fix_section_number(line) for line in cell['source']]

    # 3. Renumber CELDA comments in code cells
    celda_counter = 0
    for cell in new_cells:
        if cell['cell_type'] == 'code':
            celda_counter += 1
            src_text = ''.join(cell['source'])
            if '# CELDA ' in src_text:
                cell['source'] = [
                    fix_celda_comment(line, celda_counter) for line in cell['source']
                ]
            # For cells without CELDA comment - no change needed
            # (they already have descriptive headers)

    # 4. Insert TOC after header (index 0)
    new_cells.insert(1, TOC_CELL)

    # 5. Clear outputs and execution counts
    for cell in new_cells:
        if cell['cell_type'] == 'code':
            cell['outputs'] = []
            cell['execution_count'] = None

    nb['cells'] = new_cells

    # Save
    with open(NB_PATH, 'w', encoding='utf-8') as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)

    n_after = len(new_cells)
    n_code = sum(1 for c in new_cells if c['cell_type'] == 'code')
    n_md = sum(1 for c in new_cells if c['cell_type'] == 'markdown')

    print(f"✔ Notebook limpio: {n_before} → {n_after} celdas")
    print(f"  Eliminadas: 2 celdas (Folium antiguo §14)")
    print(f"  Agregada: 1 celda TOC (Índice de Secciones)")
    print(f"  Secciones renumeradas: §15→§14, §16→§15, §17→§16, §18→§17")
    print(f"  CELDA renumeradas: 1–{celda_counter}")
    print(f"  Total: {n_code} código + {n_md} markdown = {n_after} celdas")
    print(f"  Outputs limpiados")
    print(f"  Archivo: {NB_PATH}")


if __name__ == '__main__':
    main()
