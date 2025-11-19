import re
from pathlib import Path

DOC_DIR = Path(__file__).resolve().parent.parent / 'doc'
OUT_DIR = DOC_DIR / 'extracted'
OUT_DIR.mkdir(parents=True, exist_ok=True)

files = [
    'Caso-de-Estudio-PD0054-674-C-IT-0001_P.pdf',
    '1. Suárez 2023 - WIREs Water - Silala - Investigating river aquifer interactions using heat a.PDF'
]

patterns = [
    r"Keery",
    r"McCallum",
    r"Luce",
    r"Hatch",
    r"Delta\s*phi|Δφ|delta_phi|Δφ",
    r"Delta\s*A|ΔA|delta_A",
    r"alpha|α|difusiv",
    r"omega|ω|frequency",
    r"sqrt|\\sqrt|√",
    r"ln\(|exp\(|e\^",
    r"v\s*=",
]

report = []
for fname in files:
    p = DOC_DIR / fname
    if not p.exists():
        report.append(f"[MISSING] {p}")
        continue
    data = p.read_bytes()
    try:
        text = data.decode('latin-1')
    except Exception:
        text = ''.join(chr(b) for b in data)
    report.append(f"\n== File: {fname} ==\n")
    for pat in patterns:
        matches = list(re.finditer(pat, text, flags=re.IGNORECASE))
        report.append(f"Pattern: {pat} -> {len(matches)} matches")
        for m in matches[:10]:
            start = max(0, m.start()-80)
            end = min(len(text), m.end()+80)
            snippet = text[start:end]
            # sanitize non-printables
            snippet = ''.join(ch if 32 <= ord(ch) <= 126 else ' ' for ch in snippet)
            report.append('  ...' + snippet.replace('\n',' ') + '...')
    # Also dump any lines that contain = or sqrt or Δ
    snippets = []
    for match in re.finditer(r"[=√\\]", text):
        i = match.start()
        start = max(0, i-120)
        end = min(len(text), i+120)
        s = text[start:end]
        s = ''.join(ch if 32 <= ord(ch) <= 126 else ' ' for ch in s)
        snippets.append(s)
        if len(snippets) >= 30:
            break
    report.append('\nSample equation-like snippets (up to 30):')
    for s in snippets:
        report.append('  ' + s.replace('\n',' '))

out = OUT_DIR / 'binary_grep_report.txt'
out.write_text('\n'.join(report), encoding='utf-8')
print('Reporte escrito en', out)
