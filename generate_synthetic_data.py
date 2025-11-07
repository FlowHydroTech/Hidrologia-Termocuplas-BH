import pandas as pd
import numpy as np
from pathlib import Path

# =============================
# PARÁMETROS DE SIMULACIÓN
# =============================

# Flujo vertical objetivo para generar datos sintéticos realistas
TARGET_FLUX = 5.0  # mm/día (infiltración típica río-acuífero)

# Parámetros térmicos del sedimento (arena saturada)
LAMBDA = 2.0  # Conductividad térmica [W/m·K]
C_SEDIMENT = 2.5e6  # Capacidad calorífica sedimento [J/m³·K]
C_WATER = 4.18e6  # Capacidad calorífica agua [J/m³·K]
OMEGA = 2 * np.pi / 86400  # Frecuencia angular ciclo diario [rad/s]

# Profundidades de sensores [m]
z1, z2, z3 = 0.10, 0.20, 0.30

# =============================
# CÁLCULO DE DESFASES TEMPORALES FÍSICOS
# =============================

# Convertir flujo a m/s
v = TARGET_FLUX * 1e-3 / 86400  # mm/día → m/s

# Difusividad térmica [m²/s]
alpha = LAMBDA / C_SEDIMENT

def calcular_desfase_mccallum(z_shallow, z_deep, flux_ms):
    """
    Calcula el desfase de fase usando la ecuación de McCallum (2012) invertida.
    
    Esta es la forma más robusta ya que luego se puede recuperar el flujo
    usando exactamente la misma ecuación.
    
    McCallum (2012):
    Δφ² + ΔA² = (ω * Δz²) / (4 * α) + (v² * C_water² * ω * Δz²) / (4 * LAMBDA²)
    
    Para simplificar, asumiendo que conocemos ΔA, despejamos Δφ:
    Δφ = sqrt[(ω * Δz²)/(4 * α) * (1 + v² * C_water²/(4 * LAMBDA² / (ω * Δz²))) - ΔA²]
    
    Aproximación para flujos pequeños:
    Δφ ≈ sqrt[(ω * Δz²)/(4 * α)] + (v * C_water * Δz) / (2 * LAMBDA)
    """
    dz = z_deep - z_shallow
    
    # Término puramente conductivo
    term_conductive = np.sqrt((OMEGA * dz**2) / (4 * alpha))
    
    # Término advectivo (influencia del flujo)
    term_advective = (flux_ms * C_WATER * dz) / (2 * LAMBDA)
    
    # Desfase total (aproximación lineal)
    delta_phi = term_conductive + term_advective
    
    # Convertir a segundos
    time_lag_seconds = (delta_phi / OMEGA)
    
    return time_lag_seconds, delta_phi

# Calcular desfases entre sensores
lag_12_sec, phi_12 = calcular_desfase_mccallum(z1, z2, v)
lag_23_sec, phi_23 = calcular_desfase_mccallum(z2, z3, v)
lag_13_sec, phi_13 = calcular_desfase_mccallum(z1, z3, v)

print("=" * 80)
print("GENERACIÓN DE DATOS SINTÉTICOS - VFLUX2")
print("=" * 80)
print(f"\nFlujo vertical objetivo: {TARGET_FLUX:.2f} mm/día")
print(f"Velocidad de Darcy: {v*86400*1000:.6f} mm/día = {v:.2e} m/s")
print(f"\nDesfases temporales calculados:")
print(f"  Sensor 1→2 ({z1*100:.0f}-{z2*100:.0f} cm): {lag_12_sec/60:.2f} min ({phi_12:.4f} rad)")
print(f"  Sensor 2→3 ({z2*100:.0f}-{z3*100:.0f} cm): {lag_23_sec/60:.2f} min ({phi_23:.4f} rad)")
print(f"  Sensor 1→3 ({z1*100:.0f}-{z3*100:.0f} cm): {lag_13_sec/60:.2f} min ({phi_13:.4f} rad)")
print("=" * 80)

# =============================
# GENERAR SERIES TEMPORALES
# =============================

# Generar datos sintéticos por 3 días cada 15 minutos
rng = pd.date_range("2025-01-01", periods=3*24*4, freq="15min")

def generar_serie_termica(base_temp, amplitud, time_index, phase_rad):
    """
    Genera serie temporal sinusoidal con temperatura base, amplitud y desfase en radianes.
    
    T(t) = T_base + A * sin(ω*t + φ)
    
    donde:
      - T_base: temperatura promedio [°C]
      - A: amplitud de oscilación [°C]
      - ω: frecuencia angular [rad/s]
      - φ: desfase inicial [rad]
    """
    t_seconds = (time_index - time_index[0]).total_seconds().values
    temp = base_temp + amplitud * np.sin(OMEGA * t_seconds + phase_rad)
    return temp

# Generar series con desfases físicamente realistas
# El sensor superficial marca la referencia (fase = 0)
# Los sensores profundos tienen retraso de fase positivo (señal llega después)

temp1 = generar_serie_termica(base_temp=20.0, amplitud=3.0, time_index=rng, phase_rad=0.0)
temp2 = generar_serie_termica(base_temp=19.0, amplitud=2.0, time_index=rng, phase_rad=phi_12)
temp3 = generar_serie_termica(base_temp=18.0, amplitud=1.2, time_index=rng, phase_rad=phi_13)


# =============================
# CREAR DATAFRAME Y GUARDAR
# =============================

df = pd.DataFrame({
    "fecha1": rng,
    "temp1": temp1,
    "fecha2": rng,  # Todas las fechas sincronizadas
    "temp2": temp2,
    "fecha3": rng,  # El desfase está en la SEÑAL, no en las fechas
    "temp3": temp3
})

# Crear directorio si no existe
output_dir = Path("data/raw")
output_dir.mkdir(parents=True, exist_ok=True)

# Guardar
output_file = output_dir / "termocuplas_sinteticas.xlsx"
df.to_excel(output_file, index=False)

print(f"\n✅ Archivo '{output_file}' generado correctamente.")
print(f"   Registros: {len(df)}")
print(f"   Periodo: {rng[0]} a {rng[-1]}")
print(f"\n📊 Estadísticas de las series generadas:")
print(f"   Sensor 1 (10 cm): {temp1.mean():.2f}°C ± {temp1.std():.2f}°C (rango: {temp1.min():.2f}-{temp1.max():.2f}°C)")
print(f"   Sensor 2 (20 cm): {temp2.mean():.2f}°C ± {temp2.std():.2f}°C (rango: {temp2.min():.2f}-{temp2.max():.2f}°C)")
print(f"   Sensor 3 (30 cm): {temp3.mean():.2f}°C ± {temp3.std():.2f}°C (rango: {temp3.min():.2f}-{temp3.max():.2f}°C)")
print("\n" + "=" * 80)
print("Datos listos para análisis con VFLUX2 Python 🚀")
print("=" * 80)
