"""
Genera visualizaciones TC1 y TC5 con estilo idéntico a las imágenes MATLAB VFLUX2
para comparación directa.
"""
import sys
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import AutoMinorLocator

sys.path.insert(0, 'c:/Users/Cesar/Hidrologia-Termocuplas-BH/src')
from vfluxx.io_utils import load_all_ibuttons

# ----- Cargar datos -----
sensors = load_all_ibuttons('c:/Users/Cesar/Hidrologia-Termocuplas-BH/data/raw/Datos_Terreno')

# Crear diccionario por sensor_id
sensor_dict = {s['sensor_id']: s['df'] for s in sensors}

# =====================================================
# MAPEO SENSOR → TERMOCUPLA Y PROFUNDIDAD
# =====================================================
tc1_mapping = {
    'surface':      'A400000082BAF041',
    'intermediate': '7D000000828FA841',
    'deep':         '5900000082B86A41',
}

tc5_mapping = {
    'surface':      '3800000082952A41',
    'intermediate': 'B000000082987741',
    'deep':         '2800000082978041',
}

# Profundidades (mbnt)
depths = {'surface': 0.00, 'intermediate': 0.28, 'deep': 0.56}
labels_es = {'surface': 'S. superior', 'intermediate': 'S. intermedio', 'deep': 'S. inferior'}

# Colores EXACTOS de MATLAB (tab10 default)
colors = {'surface': '#1f77b4', 'intermediate': '#ff7f0e', 'deep': '#2ca02c'}

cutoff = pd.Timestamp('2025-12-21')


def plot_thermocouple(mapping, tc_name, save_path):
    """Genera gráfico con estilo idéntico a MATLAB VFLUX2."""
    # Fondo blanco, estilo MATLAB
    plt.rcdefaults()
    fig, ax = plt.subplots(figsize=(14, 5), facecolor='white')
    ax.set_facecolor('white')

    cutoff_end = pd.Timestamp('2026-01-22 12:00:00')

    # Obtener primer datetime para calcular hora de referencia para el eje X
    first_dt = None
    for key in ['surface', 'intermediate', 'deep']:
        sid = mapping[key]
        df = sensor_dict[sid].copy()
        df = df[(df['datetime'] >= cutoff) & (df['datetime'] <= cutoff_end)]
        if first_dt is None or df['datetime'].iloc[0] < first_dt:
            first_dt = df['datetime'].iloc[0]

    for key in ['surface', 'intermediate', 'deep']:
        sid = mapping[key]
        df = sensor_dict[sid].copy()
        df = df[(df['datetime'] >= cutoff) & (df['datetime'] <= cutoff_end)].reset_index(drop=True)
        label = f"{labels_es[key]} ({depths[key]:.2f} mbnt)"
        lw = 1.0 if key == 'surface' else 1.2
        ax.plot(df['datetime'], df['temperature'], color=colors[key],
                linewidth=lw, label=label)

    # Eje Y: "Temperatura [°C]" a la izquierda, mismo estilo que MATLAB
    ax.set_ylabel('Temperatura [°C]', fontsize=12, fontweight='normal')

    # Leyenda arriba, 3 columnas, sin marco — idéntico al MATLAB
    ax.legend(loc='upper center', ncol=3, fontsize=11, frameon=False,
              bbox_to_anchor=(0.5, 1.12))

    # Eje X: formato DD-MM HH:MM, tick cada 2 días, rotado
    # Usar la hora del primer registro como referencia (08:26 para TC1, 10:04 para TC5)
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d-%m %H:%M'))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right', fontsize=9)

    # Ticks Y
    ax.tick_params(axis='y', labelsize=10)
    ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

    # Rango Y: redondear como MATLAB
    all_temps = []
    for key in ['surface', 'intermediate', 'deep']:
        sid = mapping[key]
        df = sensor_dict[sid].copy()
        df = df[(df['datetime'] >= cutoff) & (df['datetime'] <= cutoff_end)]
        all_temps.extend(df['temperature'].values)
    ymin = int(np.floor(min(all_temps)))
    ymax = int(np.ceil(max(all_temps))) + 1
    ax.set_ylim(ymin, ymax)

    # Sin grid — como MATLAB
    ax.grid(False)

    # Box completo (4 spines visibles) — como MATLAB
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(1.0)
        spine.set_color('black')

    # Ticks en ambos lados (MATLAB default)
    ax.tick_params(axis='both', direction='in', top=True, right=True, 
                   left=True, bottom=True)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  ✔ Guardado: {save_path}")

    # Estadísticas
    print(f"\n  Estadísticas {tc_name} (post 21-Dic):")
    for key in ['surface', 'intermediate', 'deep']:
        sid = mapping[key]
        df = sensor_dict[sid].copy()
        df = df[(df['datetime'] >= cutoff) & (df['datetime'] <= cutoff_end)]
        t = df['temperature']
        print(f"    {labels_es[key]:15s} ({sid}): "
              f"[{t.min():.1f}, {t.max():.1f}] °C | "
              f"Media: {t.mean():.1f} °C | "
              f"Semi-amp: {(t.max()-t.min())/2:.1f} °C")


# ----- Generar gráficos -----
print("=" * 60)
print("Generando gráfico TC1...")
plot_thermocouple(
    tc1_mapping, "TC1",
    'c:/Users/Cesar/Hidrologia-Termocuplas-BH/image/temperatura_tc1_python.png'
)

print()
print("Generando gráfico TC5...")
plot_thermocouple(
    tc5_mapping, "TC5",
    'c:/Users/Cesar/Hidrologia-Termocuplas-BH/image/temperatura_tc5_python.png'
)

print()
print("=" * 60)
print("\nMAPEO FINAL DE SENSORES:")
print("\nTC1 (Termocupla 1):")
for key in ['surface', 'intermediate', 'deep']:
    sid = tc1_mapping[key]
    print(f"  {depths[key]:.2f} mbnt ({labels_es[key]:15s}) → {sid}")
print("\nTC5 (Termocupla 5):")
for key in ['surface', 'intermediate', 'deep']:
    sid = tc5_mapping[key]
    print(f"  {depths[key]:.2f} mbnt ({labels_es[key]:15s}) → {sid}")

print("\nPROFUNDIDADES PARA EL NOTEBOOK:")
print("  TC1: dz_sup-int = 0.28 m, dz_int-inf = 0.28 m, dz_sup-inf = 0.56 m")
print("  TC5: dz_sup-int = 0.28 m, dz_int-inf = 0.28 m, dz_sup-inf = 0.56 m")
