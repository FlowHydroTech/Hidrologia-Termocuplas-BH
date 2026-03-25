"""Update cell 28 markdown and add annotations answering user questions."""
import json

path = "notebooks/05A_datos_terreno.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

# 1. Update cell 28 markdown (section 9.3)
new_md_28 = [
    "### 9.3  Selector Interactivo de Ventana Temporal\n",
    "\n",
    "Herramienta interactiva (HTML + Plotly.js) para seleccionar un subperiodo de la serie de flujos\n",
    "y obtener estadísticos descriptivos (mediana, promedio, Q1, Q3, IQR) **actualizados en tiempo real**.\n",
    "\n",
    "**Uso:**\n",
    "- Se genera un archivo HTML por cada termocupla (TC1–TC5).\n",
    "- Abra el archivo en el navegador.\n",
    "- Mueva el **range slider** inferior o pulse los botones de rango (3d, 1sem, 2sem, Todo).\n",
    "- La tabla de estadísticos **se recalcula automáticamente** al cambiar la ventana.\n",
    "- Muestra unidades en **m/s** (investigación) y **mm/d** (comparación directa con MATLAB VFLUX2).\n",
    "\n",
    "Esto replica el flujo de trabajo de VFLUX2/MATLAB donde el especialista seleccionaba\n",
    "manualmente la ventana de datos estables para reportar el flujo representativo.\n",
    "\n",
    "---\n",
    "\n",
    "**Nota sobre el cálculo del \"Total\" (promedio de 3 pares):**\n",
    "\n",
    "Cada termocupla tiene 3 sensores a distintas profundidades (sup, int, inf), lo que\n",
    "genera 3 pares: sup→int, int→inf, sup→inf. Cada par produce una estimación **independiente**\n",
    "del flujo vertical mediante análisis armónico de amplitud (Hatch et al., 2006).\n",
    "El \"Total\" reportado como promedio de los 3 pares es la práctica estándar en VFLUX2\n",
    "(Gordon et al., 2012) y permite aprovechar toda la información disponible. El par sup→inf\n",
    "no es redundante: usa un Δz diferente y captura señales térmicas distintas.\n",
    "\n",
    "**Nota sobre diferencias Python vs MATLAB:**\n",
    "\n",
    "Las diferencias menores (Δ < 15%) entre Python y MATLAB se deben principalmente a:\n",
    "1. **Ventana temporal**: MATLAB usó una ventana seleccionada manualmente por el especialista;\n",
    "   Python procesa la serie completa. Use el selector interactivo para replicar la ventana\n",
    "   de MATLAB y verificar convergencia.\n",
    "2. **Interpolación**: Diferencias menores en el remuestreo temporal (1h).\n",
    "3. El especialista confirmó: *\"la diferencia es pequeña, así que están OK\"*.\n",
]

for cell in nb["cells"]:
    if cell["cell_type"] != "markdown":
        continue
    src = "".join(cell["source"])
    if "9.3  Selector Interactivo" in src:
        cell["source"] = new_md_28
        print("Updated cell 28 (section 9.3 markdown)")
        break

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Notebook saved successfully")
