"""Investigar outliers del sensor 5900."""
import sys
import pandas as pd
sys.path.insert(0, 'c:/Users/Cesar/Hidrologia-Termocuplas-BH/src')
from vfluxx.io_utils import load_all_ibuttons

sensors = load_all_ibuttons('c:/Users/Cesar/Hidrologia-Termocuplas-BH/data/raw/Datos_Terreno')
sensor_dict = {s['sensor_id']: s['df'] for s in sensors}

cutoff = pd.Timestamp('2025-12-21')

# --- Sensor 5900 ---
df = sensor_dict['5900000082B86A41'].copy()
df = df[df['datetime'] >= cutoff].reset_index(drop=True)

print(f"Sensor 5900 post 21-Dic: {len(df)} registros")
high20 = df[df['temperature'] > 20]
high22 = df[df['temperature'] > 22]
high25 = df[df['temperature'] > 25]
print(f"  > 20°C: {len(high20)} registros ({100*len(high20)/len(df):.1f}%)")
print(f"  > 22°C: {len(high22)} registros ({100*len(high22)/len(df):.1f}%)")
print(f"  > 25°C: {len(high25)} registros ({100*len(high25)/len(df):.1f}%)")
print()

if len(high25) > 0:
    print("Registros con T > 25°C:")
    print(high25.to_string(index=False))
    print()

# Percentiles
print("Percentiles:")
for p in [1, 5, 25, 50, 75, 95, 99]:
    val = df['temperature'].quantile(p/100)
    print(f"  P{p}: {val:.2f}°C")

print()
# Comparar con 7D00
df7d = sensor_dict['7D000000828FA841'].copy()
df7d = df7d[df7d['datetime'] >= cutoff]
print(f"Sensor 7D00 post 21-Dic: {len(df7d)} registros")
print("Percentiles 7D00:")
for p in [1, 5, 25, 50, 75, 95, 99]:
    val = df7d['temperature'].quantile(p/100)
    print(f"  P{p}: {val:.2f}°C")

# Comparar con A400
dfa4 = sensor_dict['A400000082BAF041'].copy()
dfa4 = dfa4[dfa4['datetime'] >= cutoff]
print(f"\nSensor A400 post 21-Dic: {len(dfa4)} registros")
print("Percentiles A400:")
for p in [1, 5, 25, 50, 75, 95, 99]:
    val = dfa4['temperature'].quantile(p/100)
    print(f"  P{p}: {val:.2f}°C")
