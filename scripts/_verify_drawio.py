import xml.etree.ElementTree as ET
t = ET.parse('Diagrama/diagrama_proceso.drawio')
ds = [d.get('name') for d in t.findall('diagram')]
print("Hojas:", ds)
for d in t.findall('diagram'):
    if d.get('id') == 'vflux2-pipeline':
        cells = d.findall('.//mxCell')
        print(f"Celdas pipeline: {len(cells)}")
        for c in cells:
            cid = c.get('id', '')
            if 'mad' in cid or 'title' in cid.lower() or cid == 'note1' or cid.startswith('s11') or cid == 's7_map':
                val = c.get('value', '')[:80]
                print(f"  {cid}: {val}")
