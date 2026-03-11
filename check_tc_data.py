"""Script temporal para verificar datos de todas las termocuplas"""
import pandas as pd
from pathlib import Path

data_dir = Path('data/Datos Termocuplas 25-02-2026')

print("=" * 80)
print(" VERIFICACIÓN DE DATOS POR TERMOCUPLA ".center(80))
print("=" * 80)
print()

for tc in ['tc1', 'tc2', 'tc3', 'tc4', 'tc5']:
    xlsx_path = data_dir / tc / f'datos_filtrados_{tc}.xlsx'
    if xlsx_path.exists():
        df = pd.read_excel(xlsx_path)
        inicio = df['fecha1'].min()
        fin = df['fecha1'].max()
        dias = (fin - inicio).days
        print(f"{tc.upper()}: {len(df):>5} registros | {str(inicio)[:16]} → {str(fin)[:16]} | {dias} días")
    else:
        print(f"{tc.upper()}: NO EXISTE")

print()
print("=" * 80)
