"""
Análisis detallado del método McCallum (2012)
para entender por qué funciona correctamente.
"""

from src.vflux_methods import (
    calculate_thermal_diffusivity,
    mccallum_method,
    hatch_amplitude_method,
)
import numpy as np


# Parámetros
v_real = 5.0 / 86400 / 1000
delta_z = 0.30
lambda_s = 2.0
C_s = 2.5e6
C_w = 4.18e6
alpha = calculate_thermal_diffusivity(lambda_s, C_s)
omega = 2 * np.pi / 86400

# Amplitudes y fases sintéticas (consistentes con v_real)
delta_phi_conductivo = np.sqrt((omega * delta_z**2) / (4 * alpha))
delta_phi_advectivo = (v_real * C_w * delta_z) / (2 * lambda_s)
delta_phi_total = delta_phi_conductivo + delta_phi_advectivo

Ar = np.exp((v_real * delta_z) / alpha)
A_shallow = 1.0
A_deep = A_shallow / Ar

print("=" * 80)
print("ANÁLISIS DETALLADO (usando implementación en src.vflux_methods)")
print("=" * 80)

print(f"Δφ_conductivo = {delta_phi_conductivo:.6f} rad")
print(f"Δφ_advectivo  = {delta_phi_advectivo:.6f} rad")
print(f"Δφ_total      = {delta_phi_total:.6f} rad")

# Llamar a la función mccallum_method (usa la versión corregida en src)
v_mcc = mccallum_method(
    amplitude_shallow=A_shallow,
    amplitude_deep=A_deep,
    phase_shallow=0.0,
    phase_deep=delta_phi_total,
    depth_difference=delta_z,
    thermal_diffusivity=alpha,
    angular_frequency=omega,
)

v_hatch = hatch_amplitude_method(
    amplitude_shallow=A_shallow,
    amplitude_deep=A_deep,
    depth_difference=delta_z,
    thermal_diffusivity=alpha,
    angular_frequency=omega,
)

print(f"\nResultado McCallum (implementación): {v_mcc*86400*1000:.4f} mm/día")
print(f"Resultado Hatch-Amplitude:           {v_hatch*86400*1000:.4f} mm/día")

if abs(v_mcc - v_hatch) < 1e-12:
    print("\nObservación: McCallum devolvió el mismo valor que Hatch-Amplitude (fallback o reducción).")
else:
    print("\nObservación: McCallum difiere de Hatch-Amplitude — revisar términos internos.")

print("\nSi quieres, puedo imprimir los términos internos (ΔA, término dentro de √) usando")
print("la descomposición advectiva/conductiva para verificar exactamente por qué se toma el fallback.")
