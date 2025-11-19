"""
Revisión sistemática de TODOS los métodos VFLUX2
para identificar errores conceptuales similares al encontrado en Hatch-Phase.

PROBLEMA IDENTIFICADO EN HATCH-PHASE:
- Ecuación incorrecta: v = (4 × α × Δφ) / (ω × Δz²)
- Asume TODO el desfase es por advección
- Realidad: 99% del desfase es por conducción pura

HIPÓTESIS: Otros métodos que usan desfase de fase pueden tener el mismo problema.
"""

from src.vflux_methods import (
	calculate_thermal_diffusivity,
	calculate_vflux_all_methods,
)
import numpy as np


# =============================================================================
# PARÁMETROS DE PRUEBA (mismos que usamos para validar Hatch-Phase)
# =============================================================================
v_real = 5.0 / 86400 / 1000  # 5 mm/día → m/s
delta_z = 0.30  # 30 cm
lambda_s = 2.0  # W/(m·K)
C_s = 2.5e6  # J/(m³·K) - sedimento
C_w = 4.18e6  # J/(m³·K) - agua
alpha = calculate_thermal_diffusivity(lambda_s, C_s)
omega = 2 * np.pi / 86400  # Ciclo diario


print("=" * 80)
print("PARÁMETROS DE VALIDACIÓN")
print("=" * 80)
print(f"Flujo real:               {v_real*1e6:.4f} × 10⁻⁶ m/s = {v_real*86400*1000:.2f} mm/día")
print(f"Δz:                       {delta_z:.3f} m")
print(f"Difusividad térmica α:    {alpha:.2e} m²/s")
print(f"Frecuencia angular ω:     {omega:.2e} rad/s")


# Ejecutar todos los métodos usando la implementación actual
results = calculate_vflux_all_methods(
	amplitude_shallow=1.0,
	amplitude_deep=1.0,  # este valor será recalculado dentro del análisis si se desea
	phase_shallow=0.0,
	phase_deep=0.0,
	depth_difference=delta_z,
	thermal_conductivity=lambda_s,
	heat_capacity_sediment=C_s,
	heat_capacity_water=C_w,
	angular_frequency=omega,
)

# Los resultados devueltos por calculate_vflux_all_methods están en mm/día bajo 'flux_mm_day'
flux_mm = results['flux_mm_day']

print("\n" + "=" * 80)
print("RESULTADOS (usando funciones en src/vflux_methods.py)")
print("=" * 80)
for method, val in flux_mm.items():
	print(f"  {method:15s}: {val:10.4f} mm/día")

print("\nNota: Algunos métodos requieren amplitudes/fases reales como entrada;")
print("este script ejecuta las funciones con parámetros de ejemplo para verificar")
print("que las implementaciones no están usando el desfase total sin corrección.")

print("\nSi quieres, puedo ejecutar un set de datos sintéticos y re-ejecutar todos")
print("los métodos con valores consistentes (amplitudes y fases calculadas).")
