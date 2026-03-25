"""Busca en el notebook la celda que genera Tabla 5."""
import json

with open("notebooks/05A_datos_terreno.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)

keywords = [
    "tabla_5", "Tabla 5", "tabla_resumen", "resumen_flujo",
    "caudal_vertical", "Caudal", "infiltracion_rio",
    "281", "2246", "1555", "3.3E-03", "3,3E-03",
]

for i, cell in enumerate(nb["cells"]):
    src = "".join(cell["source"])
    ct = cell["cell_type"]
    found = [k for k in keywords if k.lower() in src.lower()]
    has_minmax = "min" in src.lower() and "max" in src.lower() and "promedio" in src.lower()
    if found or has_minmax:
        preview = src[:400].replace("\n", " | ")
        print(f"Cell {i}: type={ct}  found={found}  minmax={has_minmax}")
        print(f"  {preview}")
        print()

    # Also check outputs for these values
    if ct == "code":
        for out in cell.get("outputs", []):
            text = ""
            if out.get("output_type") == "stream":
                text = "".join(out.get("text", []))
            elif out.get("output_type") == "execute_result":
                text = "".join(out.get("data", {}).get("text/plain", []))
            for k in ["281", "2246", "1555", "311"]:
                if k in text:
                    t_preview = text[:300].replace("\n", " | ")
                    print(f"Cell {i} OUTPUT contains '{k}': {t_preview}")
                    print()
                    break
