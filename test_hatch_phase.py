"""
Test directo del método Hatch-Phase para verificar la ecuación
"""
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from vflux_methods import hatch_phase_method

# Parámetros de prueba
omega = 2 * np.pi / 86400  # Frecuencia angular diaria
alpha = 2.0 / 2.5e6  # Difusividad térmica
dz = 0.10  # 10 cm
phi_shallow = 0.0  # Fase sensor superficial
phi_deep = 0.4828  # Fase sensor profundo (nuevo valor generado)

print("=" * 70)
print("TEST: Método Hatch-Phase")
print("=" * 70)
print(f"\nParámetros:")
print(f"  ω = {omega:.6e} rad/s")
print(f"  α = {alpha:.6e} m²/s")
print(f"  Δz = {dz:.2f} m")
print(f"  φ_shallow = {phi_shallow:.4f} rad")
print(f"  φ_deep = {phi_deep:.4f} rad")
print(f"  Δφ = {phi_deep - phi_shallow:.4f} rad")

# Llamar al método
v_ms = hatch_phase_method(
    phase_shallow=phi_shallow,
    phase_deep=phi_deep,
    depth_difference=dz,
    thermal_diffusivity=alpha,
    angular_frequency=omega
)

v_mm_day = v_ms * 86400 * 1000

print(f"\nResultados:")
print(f"  v = {v_ms:.6e} m/s")
print(f"  v = {v_mm_day:.2f} mm/día")
print(f"\nFlujo objetivo (datos sintéticos): 5.00 mm/día")
print(f"Error: {abs(v_mm_day - 5.0):.2f} mm/día")
print("=" * 70)
