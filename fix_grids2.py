"""Fix remaining weak grid lines in the notebook."""
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
        # Fix ax1.grid alpha=0.25
        if "ax1.grid(" in line and "alpha=0.25" in line:
            new_line = line.replace("alpha=0.25", "alpha=0.5")
            if 'color=' not in new_line and 'color="' not in new_line:
                new_line = new_line.rstrip("\n").rstrip(")") + ', color="#999999")\n'
            modified = True
            changes += 1
        # Fix ax2.grid alpha=0.2
        elif "ax2.grid(" in line and "alpha=0.2" in line:
            new_line = line.replace("alpha=0.2", "alpha=0.5")
            if 'color=' not in new_line and 'color="' not in new_line:
                new_line = new_line.rstrip("\n").rstrip(")") + ', color="#999999")\n'
            modified = True
            changes += 1
        new_source.append(new_line)
    if modified:
        cell["source"] = new_source

print(f"Changed {changes} grid lines")

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Notebook saved successfully")
