"""
Consolidación del notebook 05A_datos_terreno.ipynb para entrega a cliente.

Cambios:
1. Eliminar celda 34 (0-indexed) — CELDA 18 (AUDITORÍA), redundante con MD cell 33
2. Corregir sección duplicada §17:
   - Cell 47 (§17 Tendencia Central) → §18
   - Cell 49 (§18 Boxplot) → §19
   - Cell 51 (§19 Mapa SIG) → §20
3. Actualizar comentarios en celdas de código (§17→§18, §18→§19, §19→§20)
4. Actualizar índice de secciones (celda 1) para incluir §18-§20
"""

import json
from pathlib import Path

NB_PATH = Path(__file__).resolve().parent.parent / "notebooks" / "05A_datos_terreno.ipynb"

with open(NB_PATH, "r", encoding="utf-8") as f:
    nb = json.load(f)

cells = nb["cells"]
n_before = len(cells)

# ── 1. Eliminar celda de auditoría (cell 34, 0-indexed) ─────────────────
# Verificar que es la celda correcta
audit_cell = cells[34]
assert audit_cell["cell_type"] == "code", f"Cell 34 is {audit_cell['cell_type']}, expected code"
cell_text = "".join(audit_cell["source"])
assert "AUDITORÍA" in cell_text or "AUDITORIA" in cell_text, f"Cell 34 doesn't look like audit cell: {cell_text[:120]}"

del cells[34]
print(f"✔ Eliminada celda de auditoría (era cell 34), ahora {len(cells)} celdas")

# Después de la eliminación, los índices se desplazan -1 para celdas ≥ 34.
# Las celdas que necesitan fix son ahora:
# - vieja cell 47 → nueva cell 46 (MD: §17 Tendencia Central → §18)
# - vieja cell 48 → nueva cell 47 (code: §17 → §18)
# - vieja cell 49 → nueva cell 48 (MD: §18 Boxplot → §19)
# - vieja cell 50 → nueva cell 49 (code: §18 → §19)
# - vieja cell 51 → nueva cell 50 (MD: §19 Mapa SIG → §20)
# - vieja cell 52 → nueva cell 51 (code: §19 → §20)

# ── 2. Corregir sección §17 duplicada → §18 (MD cell, ahora idx 46) ─────
def replace_in_cell(cell, old, new):
    """Replace string in cell source lines."""
    changed = False
    new_source = []
    for line in cell["source"]:
        if old in line:
            line = line.replace(old, new)
            changed = True
        new_source.append(line)
    cell["source"] = new_source
    return changed

# MD cell: §17 Tendencia → §18
c46 = cells[46]
assert c46["cell_type"] == "markdown"
assert any("17." in l and "Tendencia" in l for l in c46["source"]), \
    f"Cell 46 not the expected §17 Tendencia Central"
replace_in_cell(c46, "## 17. Series Temporales", "## 18. Series Temporales")
print("✔ MD §17 (Tendencia Central) → §18")

# Code cell: §17 → §18 in comments
c47 = cells[47]
assert c47["cell_type"] == "code"
replace_in_cell(c47, "§17 SERIES TEMPORALES", "§18 SERIES TEMPORALES")
print("✔ Code §17 → §18")

# MD cell: §18 Boxplot → §19
c48 = cells[48]
assert c48["cell_type"] == "markdown"
assert any("18." in l and "Boxplot" in l for l in c48["source"]), \
    f"Cell 48 not the expected §18 Boxplot"
replace_in_cell(c48, "## 18. Boxplot Vertical", "## 19. Boxplot Vertical")
print("✔ MD §18 (Boxplot) → §19")

# Code cell: §18 → §19
c49 = cells[49]
assert c49["cell_type"] == "code"
replace_in_cell(c49, "§18 BOXPLOT VERTICAL", "§19 BOXPLOT VERTICAL")
print("✔ Code §18 → §19")

# MD cell: §19 Mapa SIG → §20
c50 = cells[50]
assert c50["cell_type"] == "markdown"
assert any("19" in l and "Mapa" in l for l in c50["source"]), \
    f"Cell 50 not the expected §19 Mapa SIG"
# This cell uses "## §19 — Mapa SIG" format
replace_in_cell(c50, "§19", "20.")
print("✔ MD §19 (Mapa SIG) → §20")

# Code cell: §19 → §20
c51 = cells[51]
assert c51["cell_type"] == "code"
replace_in_cell(c51, "§19 MAPA SIG", "§20 MAPA SIG")
print("✔ Code §19 → §20")

# ── 3. Actualizar índice de secciones (celda 1, 0-indexed) ──────────────
idx_cell = cells[1]
assert idx_cell["cell_type"] == "markdown"
assert any("Índice" in l for l in idx_cell["source"])

# Find the line with "| 17 |" and add §18-§20 after it
new_source = []
for line in idx_cell["source"]:
    new_source.append(line)
    if "| 17 |" in line and "Panel SIG" in line:
        new_source.append("| 18 | Series Temporales Tendencia Central | 25 | MAD-filtrado, Flow v3 |\n")
        new_source.append("| 19 | Boxplot Tendencia Central | 26 | MAD sin outliers, Flow v3 |\n")
        new_source.append("| 20 | Mapa SIG Tendencia Central | 27 | Folium + MAD + tabla |\n")

idx_cell["source"] = new_source
print("✔ Índice actualizado con §18-§20")

# ── Guardar ──────────────────────────────────────────────────────────────
with open(NB_PATH, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print(f"\n✔ Notebook consolidado: {n_before} → {len(cells)} celdas")
print(f"  Guardado en: {NB_PATH}")
