import json, re
nb = json.load(open('notebooks/05A_datos_terreno.ipynb', 'r', encoding='utf-8'))

print(f"Total cells: {len(nb['cells'])}")
print(f"\n=== MARKDOWN SECTIONS ===")
for i, c in enumerate(nb['cells']):
    if c['cell_type'] == 'markdown':
        for line in c['source']:
            if re.match(r'^#{1,3} ', line):
                print(f"  Cell {i+1}: {line.strip()[:85]}")
                break

print(f"\n=== CODE CELDAS ===")
for i, c in enumerate(nb['cells']):
    if c['cell_type'] == 'code':
        src = ''.join(c['source'])
        m = re.search(r'# CELDA (\S+.*?)(?:\n|$)', src)
        if m:
            print(f"  Cell {i+1}: CELDA {m.group(1)[:60]}")
        else:
            print(f"  Cell {i+1}: (no CELDA)")
