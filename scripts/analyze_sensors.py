"""Análisis de mapeo sensor → profundidad → termocupla."""
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, 'c:/Users/Cesar/Hidrologia-Termocuplas-BH/src')
from vfluxx.io_utils import load_all_ibuttons

sensors = load_all_ibuttons('c:/Users/Cesar/Hidrologia-Termocuplas-BH/data/raw/Datos_Terreno')

cutoff = pd.Timestamp('2025-12-21')

groupA = []  # inicio Dec 18
groupB = []  # inicio Dec 20

for s in sensors:
    sid = s['sensor_id']
    df = s['df']
    mask = df['datetime'] >= cutoff
    df_post = df[mask].copy()
    temps = df_post['temperature']
    tmin = temps.min()
    tmax = temps.max()
    tmean = temps.mean()
    amp = (tmax - tmin) / 2
    t0 = df['datetime'].iloc[0]
    t0_post = df_post['datetime'].iloc[0]

    info = {
        'id': sid, 'part': s['part_number'],
        't0': t0, 't0_post': t0_post,
        'tmin': tmin, 'tmax': tmax, 'tmean': tmean, 'amp': amp, 'n': len(df_post),
    }

    if t0.date() == pd.Timestamp('2025-12-18').date():
        groupA.append(info)
    else:
        groupB.append(info)

# Ordenar por amplitud descendente
groupA.sort(key=lambda x: x['amp'], reverse=True)
groupB.sort(key=lambda x: x['amp'], reverse=True)

depths_labels = ['0.00 m (superficie)', '0.28 m (intermedio)', '0.56 m (inferior)']

print("=== ANALISIS POST-DESPLIEGUE (desde 21-Dic) ===\n")

print("GRUPO A (inicio 18-Dic):")
for i, s in enumerate(groupA):
    label = depths_labels[i]
    print(f"  {label:25s} -> {s['id']} ({s['part']})")
    print(f"    Inicio: {s['t0']} | 1er post: {s['t0_post']}")
    print(f"    T post: [{s['tmin']:.2f}, {s['tmax']:.2f}] | Media: {s['tmean']:.2f} | Semi-amp: {s['amp']:.2f}")

print()

print("GRUPO B (inicio 20-Dic):")
for i, s in enumerate(groupB):
    label = depths_labels[i]
    print(f"  {label:25s} -> {s['id']} ({s['part']})")
    print(f"    Inicio: {s['t0']} | 1er post: {s['t0_post']}")
    print(f"    T post: [{s['tmin']:.2f}, {s['tmax']:.2f}] | Media: {s['tmean']:.2f} | Semi-amp: {s['amp']:.2f}")

print()
print(f"Grupo A superficie: amp={groupA[0]['amp']:.2f} | rango=[{groupA[0]['tmin']:.1f}, {groupA[0]['tmax']:.1f}]")
print(f"Grupo B superficie: amp={groupB[0]['amp']:.2f} | rango=[{groupB[0]['tmin']:.1f}, {groupB[0]['tmax']:.1f}]")
print()
print("TC1 imagen: superficie rango ~13-24 (amp~5.5)")
print("TC5 imagen: superficie rango ~14-23 (amp~4.5)")
print()
if groupA[0]['amp'] > groupB[0]['amp']:
    print("=> Grupo A = TC1, Grupo B = TC5")
else:
    print("=> Grupo A = TC5, Grupo B = TC1")
