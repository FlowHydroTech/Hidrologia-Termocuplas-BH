"""Fix global rcParams grid settings in cell 3 and cell 26."""
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
        # Fix grid.alpha: 0.35 -> 0.55 (cell 3)
        if "'grid.alpha': 0.35" in line:
            new_line = line.replace("'grid.alpha': 0.35", "'grid.alpha': 0.55")
            modified = True
            changes += 1
        # Fix grid.linewidth: 0.4 -> 0.5 (cell 3)
        elif "'grid.linewidth': 0.4" in line:
            new_line = line.replace("'grid.linewidth': 0.4", "'grid.linewidth': 0.5")
            modified = True
            changes += 1
        # Fix grid.color: '#b0b0b0' -> '#999999' (cell 3)
        elif "'grid.color': '#b0b0b0'" in line:
            new_line = line.replace("'grid.color': '#b0b0b0'", "'grid.color': '#999999'")
            modified = True
            changes += 1
        # Fix "grid.alpha": 0.3 -> 0.55 (cell 26 rcParams)
        elif '"grid.alpha": 0.3' in line:
            new_line = line.replace('"grid.alpha": 0.3', '"grid.alpha": 0.55')
            modified = True
            changes += 1
        new_source.append(new_line)
    if modified:
        cell["source"] = new_source

# Also ensure axes.grid is True in cell 3
for cell in nb["cells"]:
    if cell["cell_type"] != "code":
        continue
    src = "".join(cell["source"])
    if "'grid.alpha': 0.55" in src and "'axes.grid'" not in src:
        # Insert axes.grid: True right before grid.alpha
        new_source = []
        for line in cell["source"]:
            if "'grid.alpha': 0.55" in line:
                new_source.append("    'axes.grid': True,\n")
                changes += 1
            new_source.append(line)
        cell["source"] = new_source

print(f"Changed {changes} rcParams lines")

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Notebook saved successfully")
