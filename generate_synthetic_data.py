import pandas as pd
import numpy as np
from pathlib import Path

# Generar datos sintéticos por 3 días cada 15 minutos
rng = pd.date_range("2025-01-01", periods=3*24*4, freq="15min")

def generar_serie(base_temp, amplitud, desfase_minutos):
    t = np.arange(len(rng))
    omega = 2 * np.pi / (24*4)  # ciclo diario
    desfase = desfase_minutos / 60 / 24 * 2 * np.pi
    return base_temp + amplitud * np.sin(omega * t + desfase)

# Series térmicas sintéticas
temp1 = generar_serie(20, 3, desfase_minutos=0)
temp2 = generar_serie(19, 2, desfase_minutos=2)
temp3 = generar_serie(18, 1.2, desfase_minutos=4)

df = pd.DataFrame({
    "fecha1": rng,
    "temp1": temp1,
    "fecha2": rng + pd.Timedelta(minutes=2),
    "temp2": temp2,
    "fecha3": rng + pd.Timedelta(minutes=4),
    "temp3": temp3
})

# Crear directorio si no existe
output_dir = Path("data/raw")
output_dir.mkdir(parents=True, exist_ok=True)

# Guardar
output_file = output_dir / "termocuplas_sinteticas.xlsx"
df.to_excel(output_file, index=False)

print(f"✅ Archivo '{output_file}' generado correctamente.")
print(f"   Registros: {len(df)}")
print(f"   Periodo: {rng[0]} a {rng[-1]}")
