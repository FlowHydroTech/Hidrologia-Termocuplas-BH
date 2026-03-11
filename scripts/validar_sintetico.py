"""
validar_sintetico.py - Validación de métodos VFLUX2 con datos sintéticos controlados.

Este script genera datos sintéticos con un flujo conocido y verifica
si los métodos VFLUX2 recuperan el valor correcto.

Ecuaciones físicas (Stallman 1965, Hatch 2006):
- Atenuación: A(z) = A₀ * exp(-z / d)
- Fase: φ(z) = φ₀ + z * sqrt(ω / 2α + v² / 4α²)
- Flujo: v = (2α/dz) * [ln(Ar) + some_function(Δφ)]

Donde d = sqrt(2α/ω) es la profundidad de penetración térmica.
"""

import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from vfluxx.vflux_methods import calculate_vflux_all_methods


def generate_synthetic_signal(
    v_target_mm_day: float,
    dz: float = 0.10,  # m
    A_surface: float = 3.0,  # °C
    T_mean: float = 15.0,  # °C
    thermal_conductivity: float = 1.80,  # W/m·K
    heat_capacity_sediment: float = 2.8e6,  # J/m³·K
    heat_capacity_water: float = 4.18e6,  # J/m³·K
    period_hours: float = 24.0
):
    """
    Genera parámetros armónicos sintéticos para un flujo conocido.
    
    Retorna las amplitudes y fases esperadas según la teoría.
    """
    # Convertir flujo objetivo a m/s
    v_ms = v_target_mm_day / 86400.0 / 1000.0  # mm/day -> m/s
    
    # Parámetros térmicos
    alpha_e = thermal_conductivity / heat_capacity_sediment  # m²/s
    omega = 2 * np.pi / (period_hours * 3600)  # rad/s
    
    # Profundidad de penetración térmica (sin advección)
    d_thermal = np.sqrt(2 * alpha_e / omega)
    
    # Ecuaciones de Hatch (2006) para la solución advectiva
    # gamma = v / (2 * alpha_e)
    gamma = v_ms / (2 * alpha_e)
    
    # Parámetro de onda
    # k = sqrt(omega / (2*alpha)) * sqrt(sqrt(1 + (v*alpha/omega)^2))
    # Simplificación para v pequeño: k ≈ sqrt(omega / (2*alpha))
    k_base = np.sqrt(omega / (2 * alpha_e))
    
    # Según Hatch (2006) Ec. 3:
    # delta_z = d * (k + gamma/k)
    # Aquí usamos la aproximación para flujo pequeño
    
    # Atenuación teórica
    # Para flujo pequeño: Ar = exp(-dz * k)
    # Para flujo general: Ar = exp(-dz * sqrt(gamma^2 + k^2))
    factor = np.sqrt(gamma**2 + k_base**2)
    A_deep = A_surface * np.exp(-dz * factor)
    
    # Desfase teórico
    # delta_phi = dz * (k + gamma) para flujo descendente
    # Simplificado: delta_phi ≈ dz * k para flujo pequeño
    delta_phi = dz * (k_base + gamma)
    
    # Fase
    phi_surface = 0.0
    phi_deep = phi_surface + delta_phi
    
    return {
        'A_shallow': A_surface,
        'A_deep': A_deep,
        'phi_shallow': phi_surface,
        'phi_deep': phi_deep,
        'delta_phi': delta_phi,
        'v_target_m_s': v_ms,
        'v_target_mm_day': v_target_mm_day,
        'alpha_e': alpha_e,
        'omega': omega,
        'd_thermal': d_thermal,
        'dz': dz,
        'Ke': thermal_conductivity,
        'Cs': heat_capacity_sediment,
        'Cw': heat_capacity_water,
    }


def run_validation():
    """Ejecuta la validación con múltiples flujos conocidos."""
    
    print("="*70)
    print("VALIDACIÓN DE MÉTODOS VFLUX2 CON DATOS SINTÉTICOS")
    print("="*70)
    print()
    
    # Parámetros típicos (Río Silala)
    Ke = 1.80       # W/m·K
    Cs = 2.8e6      # J/m³·K
    Cw = 4.18e6     # J/m³·K
    omega = 2 * np.pi / 86400.0  # rad/s (ciclo diario)
    dz = 0.10       # m (separación típica)
    
    alpha_e = Ke / Cs
    d_thermal = np.sqrt(2 * alpha_e / omega)
    
    print("Parámetros térmicos:")
    print(f"  - αₑ (difusividad térmica): {alpha_e:.3e} m²/s")
    print(f"  - d (penetración térmica): {d_thermal*100:.2f} cm")
    print(f"  - ω (frecuencia angular): {omega:.3e} rad/s")
    print(f"  - dz (separación sensores): {dz*100:.0f} cm")
    print()
    
    # Flujos a probar (mm/día)
    test_fluxes = [0.0, 10.0, 50.0, 100.0, 200.0]
    
    print(f"{'Flujo objetivo':>15} | {'McCallum':>12} | {'Hatch-A':>12} | {'Hatch-φ':>12} | {'Keery':>12} | {'Luce':>12}")
    print(f"{'(mm/día)':>15} | {'(mm/día)':>12} | {'(mm/día)':>12} | {'(mm/día)':>12} | {'(mm/día)':>12} | {'(mm/día)':>12}")
    print("-"*90)
    
    errors_by_method = {m: [] for m in ['mccallum', 'hatch_amplitude', 'hatch_phase', 'keery', 'luce']}
    
    for v_target in test_fluxes:
        params = generate_synthetic_signal(
            v_target_mm_day=v_target,
            dz=dz,
            thermal_conductivity=Ke,
            heat_capacity_sediment=Cs,
            heat_capacity_water=Cw
        )
        
        # Calcular con VFLUX2
        print()  # Para el output interno de calculate_vflux_all_methods
        result = calculate_vflux_all_methods(
            amplitude_shallow=params['A_shallow'],
            amplitude_deep=params['A_deep'],
            phase_shallow=params['phi_shallow'],
            phase_deep=params['phi_deep'],
            depth_difference=dz,
            thermal_conductivity=Ke,
            heat_capacity_sediment=Cs,
            heat_capacity_water=Cw,
            angular_frequency=omega
        )
        
        flux_mm = result['flux_mm_day']
        
        row = f"{v_target:>15.1f} |"
        for method in ['mccallum', 'hatch_amplitude', 'hatch_phase', 'keery', 'luce']:
            v_calc = flux_mm.get(method, np.nan)
            if not np.isnan(v_calc):
                row += f" {v_calc:>12.2f} |"
                if v_target > 0:
                    error_pct = abs(v_calc - v_target) / v_target * 100
                    errors_by_method[method].append(error_pct)
            else:
                row += f" {'NaN':>12} |"
        print(row)
    
    print()
    print("="*70)
    print("RESUMEN DE ERRORES (%)")
    print("="*70)
    
    for method, errors in errors_by_method.items():
        if errors:
            avg_error = np.mean(errors)
            print(f"  {method:<20}: Error promedio = {avg_error:.1f}%")
        else:
            print(f"  {method:<20}: Sin datos válidos")
    
    print()
    print("NOTA: Errores altos indican posibles problemas con:")
    print("  1. Ecuaciones de generación sintética vs ecuaciones del método")
    print("  2. Unidades o factores de escala")
    print("  3. Aproximaciones en las fórmulas")


if __name__ == "__main__":
    run_validation()
