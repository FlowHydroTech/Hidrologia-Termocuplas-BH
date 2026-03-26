import xml.etree.ElementTree as ET

t = ET.parse("Diagrama/diagrama_proceso.drawio")
diagrams = t.findall("diagram")
print(f"Hojas: {len(diagrams)}")
for d in diagrams:
    name = d.get("name")
    cells = d.findall(".//mxCell")
    vertices = [c for c in cells if c.get("vertex") == "1"]
    edges = [c for c in cells if c.get("edge") == "1"]
    print(f"\n  '{name}':")
    print(f"    Celdas: {len(cells)} ({len(vertices)} vértices, {len(edges)} aristas)")
    
    if "Pipeline" in name:
        # Check for swimlanes (FASE)
        for c in vertices:
            val = c.get("value", "")
            style = c.get("style", "")
            if "swimlane" in style:
                # Decode HTML entities for display
                clean = val.replace("&lt;", "<").replace("&gt;", ">")
                clean = clean.replace("<b>", "").replace("</b>", "")
                print(f"    SWIMLANE: {clean[:60]}")
            elif "FASE" in val or "Fase" in val or "fase" in val:
                print(f"    → {val[:60]}")
        
        # Check numbering (1-10)
        import re
        numbers_found = set()
        for c in vertices:
            val = c.get("value", "")
            m = re.search(r"(\d+)\.\s", val)
            if m:
                numbers_found.add(int(m.group(1)))
        print(f"    Numeración: {sorted(numbers_found)}")
        
        # Check for duplicate numbers
        from collections import Counter
        all_nums = []
        for c in vertices:
            val = c.get("value", "")
            for m2 in re.finditer(r"(\d+)\.\s", val):
                all_nums.append(int(m2.group(1)))
        dupes = {k: v for k, v in Counter(all_nums).items() if v > 1}
        if dupes:
            print(f"    ⚠️  DUPLICADOS: {dupes}")
        else:
            print(f"    ✓ Sin numeración duplicada")
