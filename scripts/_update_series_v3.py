"""
Actualiza la celda 49 (series temporales MAD) del notebook 05A_datos_terreno.ipynb
para usar un gradiente celeste Flow v3 en lugar de colores distintos por TC.

Cambios:
  - _tc_hex → gradiente celeste: claro (TC1, superficial) → oscuro (TC5, profundo)
  - Paleta consistente con boxplot (celda 51)
  - Sin grilla explícita (ya estaba)
  - Ajuste de markeredgecolor para contraste
"""

import json
from pathlib import Path

NB = Path(r"c:\Users\cesar.godoy\Hidrologia-Termocuplas-BH\notebooks\05A_datos_terreno.ipynb")
CELL_IDX = 48  # celda 49 (0-based)

# ── Viejo fragmento (colores multi-hue) ────────────────────────────
OLD_TC_HEX = """_tc_hex = {
    'TC1': '#1f77b4', 'TC2': '#ff7f0e', 'TC3': '#2ca02c',
    'TC4': '#9467bd', 'TC5': '#d62728'
}"""

# ── Nuevo fragmento (gradiente celeste Flow v3) ────────────────────
# Desde celeste claro (TC1 = más superficial) a azul oscuro (TC5 = más profundo)
# Rango más saturado que boxplot para legibilidad en líneas finas
NEW_TC_HEX = """# Gradiente celeste Flow v3: claro (superficial) → oscuro (profundo)
_tc_hex = {
    'TC1': '#4FC3F7',   # celeste claro
    'TC2': '#29B6F6',   # celeste medio
    'TC3': '#0288D1',   # celeste oscuro
    'TC4': '#0277BD',   # azul medio
    'TC5': '#01579B',   # azul profundo
}"""

# ── Viejo: markeredgecolor blanco (poco contraste con celeste claro) ──
OLD_MARKER_EDGE = "markeredgewidth=0.3, markeredgecolor='white'"
NEW_MARKER_EDGE = "markeredgewidth=0.4, markeredgecolor='black'"

with open(NB, encoding="utf-8") as f:
    nb = json.load(f)

cell = nb["cells"][CELL_IDX]
src = "".join(cell["source"])

if "_tc_hex" not in src:
    raise SystemExit(f"❌ Celda {CELL_IDX} no contiene _tc_hex — ¿índice incorrecto?")

# Reemplazos
src = src.replace(OLD_TC_HEX, NEW_TC_HEX)
src = src.replace(OLD_MARKER_EDGE, NEW_MARKER_EDGE)

cell["source"] = src.splitlines(keepends=True)
# Normalizar última línea
if cell["source"] and not cell["source"][-1].endswith("\n"):
    cell["source"][-1] += "\n"

# Limpiar outputs y execution_count
cell["outputs"] = []
cell["execution_count"] = None

with open(NB, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("✅ Celda 49 actualizada:")
print("   → Gradiente celeste Flow v3 (claro→oscuro por profundidad)")
print("   → markeredgecolor negro para contraste")
print("   → Consistente con boxplot (celda 51)")
