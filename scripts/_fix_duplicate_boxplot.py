"""Eliminar la sección duplicada del boxplot en la celda 51 del notebook."""
import json
from pathlib import Path

NB = Path('notebooks/05A_datos_terreno.ipynb')
nb = json.loads(NB.read_text(encoding='utf-8'))

# Buscar celda con MAPA SIG + _build_popup_mad
target_idx = None
for i, cell in enumerate(nb['cells']):
    src = ''.join(cell.get('source', []))
    if 'MAPA SIG' in src and '_build_popup_mad' in src:
        target_idx = i
        break

if target_idx is None:
    print("ERROR: No se encontró la celda objetivo")
    raise SystemExit(1)

cell = nb['cells'][target_idx]
full = ''.join(cell['source'])

header = "§18 BOXPLOT VERTICAL"
positions = []
start = 0
while True:
    idx = full.find(header, start)
    if idx == -1:
        break
    positions.append(idx)
    start = idx + 1

if len(positions) < 2:
    print(f"Solo {len(positions)} ocurrencia(s) del header — no hay duplicado")
    raise SystemExit(0)

print(f"Encontradas {len(positions)} ocurrencias del header boxplot")
print(f"  Posiciones de carácter: {positions}")

# La segunda ocurrencia es el duplicado.
# Buscar el inicio de la línea con el comentario del segundo §18
dup_line_start = full.rfind('\n', 0, positions[1])

# Buscar donde empieza la sección MAPA SIG (línea de ═══)
mapa_marker = "# MAPA SIG"
mapa_idx = full.find(mapa_marker)
if mapa_idx == -1:
    print("ERROR: No se encontró MAPA SIG")
    raise SystemExit(1)

# Retroceder al inicio de la línea de separadores ═══
eq_start = full.rfind('\n# ═', 0, mapa_idx)
if eq_start == -1:
    eq_start = full.rfind('\n', 0, mapa_idx)

new_full = full[:dup_line_start] + full[eq_start:]

print(f"  Eliminando: chars {dup_line_start} → {eq_start}")
print(f"  Tamaño original: {len(full)}")
print(f"  Tamaño nuevo:    {len(new_full)}")

# También corregir el print message de la primera sección
new_full = new_full.replace(
    "gradiente celeste",
    "celeste uniforme"
)

# Reconstruir source lines
new_lines = new_full.split('\n')
cell['source'] = [line + '\n' for line in new_lines[:-1]]
if new_lines[-1]:
    cell['source'].append(new_lines[-1])

cell['outputs'] = []
cell['execution_count'] = None

NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding='utf-8')
print("✅ Sección duplicada del boxplot eliminada")
