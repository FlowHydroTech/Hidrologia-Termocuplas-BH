"""Fix marker sizes in cells 24 and 26, and also ensure cell 3 grid rcParams are correct."""
import json

path = "notebooks/05A_datos_terreno.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

changes = 0
for cell in nb["cells"]:
    if cell["cell_type"] != "code":
        continue
    new_source = []
    modified = False
    for line in cell["source"]:
        new_line = line
        # Cell 24 combined: markersize=3 -> 5
        if "markersize=3," in line and "tc_hex_ts" in line and "alpha=0.8" in line:
            new_line = line.replace("markersize=3,", "markersize=5,")
            modified = True
            changes += 1
        # Cell 24 individual: markersize=4 -> 6
        elif "markersize=4," in line and "tc_hex_ts" in line and "alpha=0.8" in line:
            new_line = line.replace("markersize=4,", "markersize=6,")
            modified = True
            changes += 1
        # Cell 26 individual: markersize=2.8 -> 4.5
        elif "markersize=2.8," in line:
            new_line = line.replace("markersize=2.8,", "markersize=4.5,")
            modified = True
            changes += 1
        # Cell 26 combined: markersize=2 -> 3.5
        elif "markersize=2, alpha=0.9" in line:
            new_line = line.replace("markersize=2,", "markersize=3.5,")
            modified = True
            changes += 1
        new_source.append(new_line)
    if modified:
        cell["source"] = new_source

print(f"Changed {changes} marker size lines")

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Notebook saved successfully")
