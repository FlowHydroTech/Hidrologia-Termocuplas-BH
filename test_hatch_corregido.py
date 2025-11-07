"""Test de la ecuacion Hatch-Phase corregida"""
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))
from vflux_methods import hatch_phase_method

# Parametros
alpha = 8e-7  # m2/s
omega = 2 * np.pi / 86400  # rad/s
delta_z = 0.10  # m
phi_shallow = 0.0
phi_deep = 0.4828  # rad
lambda_val = 2.0  # W/(m*K)
Cw = 4.18e6  # J/(m3*K)

print("=" * 70)
print("TEST: Metodo Hatch-Phase CORREGIDO")
print("=" * 70)

v_ms = hatch_phase_method(
    phase_shallow=phi_shallow,
    phase_deep=phi_deep,
    depth_difference=delta_z,
    thermal_diffusivity=alpha,
    angular_frequency=omega,
    thermal_conductivity=lambda_val,
    heat_capacity_water=Cw
)

v_mm_day = v_ms * 86400 * 1000

print(f"\nResultados:")
print(f"  v = {v_ms:.6e} m/s")
print(f"  v = {v_mm_day:.4f} mm/dia")
print(f"\nFlujo objetivo: 5.00 mm/dia")
print(f"Error: {abs(v_mm_day - 5.0):.2f} mm/dia ({abs(v_mm_day - 5.0)/5*100:.1f}%)")

if abs(v_mm_day - 5.0) < 0.5:
    print(f"\n ✓ EXITO: La ecuacion corregida funciona correctamente!")
else:
    print(f"\n ✗ ERROR: Todavia hay problemas")

print("=" * 70)
