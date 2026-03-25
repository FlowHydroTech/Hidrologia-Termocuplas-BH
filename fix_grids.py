"""Fix all grid alpha=0.3 lines in the notebook to alpha=0.55."""
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
        if ".grid(" in line and "alpha=0.3" in line:
            new_line = line.replace(
                "alpha=0.3, linewidth=0.4",
                'alpha=0.55, linewidth=0.5, color="#999999"',
            )
            new_source.append(new_line)
            modified = True
            changes += 1
        else:
            new_source.append(line)
    if modified:
        cell["source"] = new_source

print(f"Changed {changes} grid lines")

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Notebook saved successfully")
