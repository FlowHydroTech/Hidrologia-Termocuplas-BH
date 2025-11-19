"""
Extractor mejorado para el paper de Suárez 2023.
Busca patrones específicos relacionados con métodos de flujo vertical.
"""
from pathlib import Path
import re

pdf_path = Path('doc/1. Suárez 2023 - WIREs Water - Silala - Investigating river aquifer interactions using heat a.PDF')

# Leer PDF como binario y buscar patrones ASCII
data = pdf_path.read_bytes()

# Intentar decodificar con varios encodings
texts = []
for encoding in ['latin-1', 'utf-8', 'cp1252']:
    try:
        text = data.decode(encoding, errors='ignore')
        texts.append(text)
        break
    except:
        continue

if not texts:
    text = ''.join(chr(b) if 32 <= b <= 126 else ' ' for b in data)
else:
    text = texts[0]

# Buscar secciones relevantes
patterns = {
    'title': r'(?i)(investigating|river|aquifer|interactions|heat|tracer|silala)',
    'authors': r'(?i)(suárez|su.rez)',
    'methods': r'(?i)(hatch|keery|mccallum|luce|stallman|vflux)',
    'equations': r'(v\s*=|q\s*=|Δ|delta|phi|\\phi)',
    'thermal': r'(?i)(thermal|temperature|conductivity|diffusivity|heat)',
    'vertical_flux': r'(?i)(vertical\s+flux|groundwater\s+flux|darcy)',
}

print("="*80)
print("ANÁLISIS DEL PAPER: Suárez 2023")
print("="*80)

for category, pattern in patterns.items():
    matches = list(re.finditer(pattern, text, flags=re.IGNORECASE))
    print(f"\n{category.upper()}: {len(matches)} coincidencias")
    
    # Mostrar contexto de las primeras 5 coincidencias
    for i, match in enumerate(matches[:5]):
        start = max(0, match.start() - 100)
        end = min(len(text), match.end() + 100)
        context = text[start:end]
        # Limpiar caracteres no imprimibles
        context = ''.join(c if 32 <= ord(c) <= 126 else ' ' for c in context)
        context = ' '.join(context.split())  # Normalizar espacios
        print(f"  [{i+1}] ...{context}...")

# Buscar números de página y estructura
print("\n" + "="*80)
print("ESTRUCTURA DEL DOCUMENTO")
print("="*80)

# Buscar stream objects (contenido de páginas)
stream_pattern = r'stream\s+'
streams = list(re.finditer(stream_pattern, text, flags=re.IGNORECASE))
print(f"Número estimado de páginas/streams: {len(streams)}")

# Buscar referencias bibliográficas
refs_pattern = r'(?i)(references|bibliography|cited)'
refs = list(re.finditer(refs_pattern, text))
if refs:
    print(f"\nSección de referencias encontrada en {len(refs)} ubicaciones")

# Guardar extracto relevante
output_path = Path('doc/extracted/suarez_2023_analysis.txt')
output_path.parent.mkdir(exist_ok=True)

with output_path.open('w', encoding='utf-8') as f:
    f.write("ANÁLISIS DEL PAPER: Suárez 2023\n")
    f.write("="*80 + "\n\n")
    
    for category, pattern in patterns.items():
        matches = list(re.finditer(pattern, text, flags=re.IGNORECASE))
        f.write(f"\n{category.upper()}: {len(matches)} coincidencias\n")
        f.write("-"*80 + "\n")
        
        for i, match in enumerate(matches[:10]):
            start = max(0, match.start() - 150)
            end = min(len(text), match.end() + 150)
            context = text[start:end]
            context = ''.join(c if 32 <= ord(c) <= 126 else ' ' for c in context)
            context = ' '.join(context.split())
            f.write(f"\n[{i+1}] ...{context}...\n")

print(f"\nAnálisis guardado en: {output_path}")
