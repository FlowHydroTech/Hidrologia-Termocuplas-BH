import re
from pathlib import Path
try:
    from pypdf import PdfReader
except Exception:
    try:
        from PyPDF2 import PdfReader
    except Exception:
        raise

DOC_DIR = Path(__file__).resolve().parent.parent / 'doc'
OUT_DIR = DOC_DIR / 'extracted'
OUT_DIR.mkdir(parents=True, exist_ok=True)

files = [
    'Caso-de-Estudio-PD0054-674-C-IT-0001_P.pdf',
    '1. Suárez 2023 - WIREs Water - Silala - Investigating river aquifer interactions using heat a.PDF'
]

# Patterns to look for (equations / keywords)
patterns = [
    r"v\s*=", r"Δφ|Delta ?phi|delta_phi|phi", r"ΔA|Delta ?A|delta_A|ln\(",
    r"α|alpha|difusiv|diffusiv|thermal diffusivity", r"ω|omega|frequency",
    r"sqrt\(|√|\\sqrt", r"ln\(|exp\(|e\^",
    r"Keery|McCallum|Luce|Hatch|Stallman|Pe"
]

report_lines = []

for fname in files:
    path = DOC_DIR / fname
    if not path.exists():
        report_lines.append(f"[ERROR] No existe: {path}")
        continue

    reader = PdfReader(str(path))
    text_parts = []
    for page in reader.pages:
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        text_parts.append(text)

    full_text = "\n".join(text_parts)
    out_txt = OUT_DIR / (path.stem + '.txt')
    out_txt.write_text(full_text, encoding='utf-8')
    report_lines.append(f"[OK] Extrajo texto: {path.name} -> {out_txt.relative_to(Path.cwd())}")

    # buscar ecuaciones / patrones
    found = set()
    for pat in patterns:
        if re.search(pat, full_text, flags=re.IGNORECASE):
            found.add(pat)

    # Extraer líneas con posibles ecuaciones (heurística)
    eq_lines = []
    for line in full_text.splitlines():
        if any(tok in line for tok in ['=', 'Δ', 'Delta', 'sqrt', '√', 'ln(', 'ω', 'alpha', 'α']):
            eq_lines.append(line.strip())
    # Limitar a primeras 80 líneas
    eq_lines = eq_lines[:80]

    report_lines.append(f"  Patrones detectados: {', '.join(sorted(found))}")
    report_lines.append("  Muestras de líneas con ecuaciones / símbolos (máx 80):")
    for l in eq_lines[:80]:
        # acortar líneas largas
        if len(l) > 400:
            l = l[:400] + ' ...'
        report_lines.append('    ' + l)
    report_lines.append("\n")

report_path = OUT_DIR / 'extraction_report.txt'
report_path.write_text('\n'.join(report_lines), encoding='utf-8')
print('Extracción completada. Reporte:', report_path)
print('Archivos generados en:', OUT_DIR)
