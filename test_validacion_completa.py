"""
Test de Validación Completo - Todos los Métodos VFLUX2
=======================================================

Objetivo: Validar corrección de McCallum y estado de todos los métodos

Fecha: 19 noviembre 2025
"""

import numpy as np
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from vflux_methods import (
    hatch_amplitude_method,
    hatch_phase_method,
    mccallum_method,
    keery_method,
    luce_method
)

# Parámetros del caso sintético
TARGET_FLUX = 5.0  # mm/día
DELTA_Z = 0.30  # m
LAMBDA = 2.0  # W/(m·K)
C_S = 2.5e6  # J/(m³·K)
C_W = 4.18e6  # J/(m³·K)
ALPHA = LAMBDA / C_S  # m²/s
OMEGA = 2 * np.pi / 86400  # rad/s

# Convertir flujo objetivo a m/s
v_target_m_s = TARGET_FLUX / 86400 / 1000

print("=" * 70)
print("VALIDACIÓN COMPLETA: Todos los Métodos VFLUX2")
print("=" * 70)
print(f"\n📊 CASO SINTÉTICO: {TARGET_FLUX} mm/día")

# Generar datos sintéticos consistentes con TARGET_FLUX
# Para Hatch-Phase: necesitamos que Δφ_advectivo produzca el flujo target
# Fórmula: v = (Δφ_advectivo * 2λ) / (Cw * Δz)
# Por lo tanto: Δφ_advectivo = (v * Cw * Δz) / (2λ)

v_target_m_s = TARGET_FLUX / (1000 * 86400)  # Convertir mm/día a m/s

# Calcular componentes de fase física
delta_phi_conductivo = np.sqrt((OMEGA * DELTA_Z**2) / (4 * ALPHA))
delta_phi_advectivo = (v_target_m_s * C_W * DELTA_Z) / (2 * LAMBDA)
delta_phi_total = delta_phi_conductivo + delta_phi_advectivo

# Para Hatch-Amplitude: usar formula correcta
Pe = (v_target_m_s * DELTA_Z) / ALPHA
Ar = np.exp(Pe)
A_shallow = 1.0
A_deep = A_shallow / Ar

# Configurar fases (shallow = 0 como referencia)
phase_shallow = 0.0
phase_deep = delta_phi_total

print(f"\n🔬 PARÁMETROS GENERADOS")
print(f"   Pe = {Pe:.6f}, Ar = {Ar:.6f}")
print(f"   A_shallow: {A_shallow:.6f}, A_deep: {A_deep:.6f}")
print(f"   φ_conductivo: {delta_phi_conductivo:.6f} rad")
print(f"   φ_advectivo: {delta_phi_advectivo:.6f} rad")
print(f"   φ_total: {delta_phi_total:.6f} rad")
print(f"   φ_shallow: {phase_shallow:.6f} rad, φ_deep: {phase_deep:.6f} rad")

# ============================================================================
# EJECUTAR TODOS LOS MÉTODOS
# ============================================================================

resultados = {}

# 1. Hatch Amplitude
try:
    v_hatch_amp = hatch_amplitude_method(
        amplitude_shallow=A_shallow,
        amplitude_deep=A_deep,
        depth_difference=DELTA_Z,
        thermal_diffusivity=ALPHA,
        angular_frequency=OMEGA
    )
    resultados['Hatch Amplitude'] = v_hatch_amp * 86400 * 1000
    error_hatch_amp = abs(v_hatch_amp - v_target_m_s) / v_target_m_s * 100
    print(f"\n✓ Hatch Amplitude: {resultados['Hatch Amplitude']:.4f} mm/día (error: {error_hatch_amp:.2f}%)")
except Exception as e:
    print(f"\n❌ Hatch Amplitude: ERROR - {e}")
    resultados['Hatch Amplitude'] = np.nan

# 2. Hatch Phase
try:
    v_hatch_phase = hatch_phase_method(
        phase_shallow=phase_shallow,
        phase_deep=phase_deep,
        depth_difference=DELTA_Z,
        thermal_diffusivity=ALPHA,
        angular_frequency=OMEGA,
        thermal_conductivity=LAMBDA,
        heat_capacity_water=C_W
    )
    resultados['Hatch Phase'] = v_hatch_phase * 86400 * 1000
    error_hatch_phase = abs(v_hatch_phase - v_target_m_s) / v_target_m_s * 100
    print(f"✓ Hatch Phase: {resultados['Hatch Phase']:.4f} mm/día (error: {error_hatch_phase:.2f}%)")
except Exception as e:
    print(f"❌ Hatch Phase: ERROR - {e}")
    resultados['Hatch Phase'] = np.nan

# 3. McCallum (CORREGIDO)
try:
    v_mccallum = mccallum_method(
        amplitude_shallow=A_shallow,
        amplitude_deep=A_deep,
        phase_shallow=phase_shallow,
        phase_deep=phase_deep,
        depth_difference=DELTA_Z,
        thermal_diffusivity=ALPHA,
        angular_frequency=OMEGA
    )
    resultados['McCallum'] = v_mccallum * 86400 * 1000
    error_mccallum = abs(v_mccallum - v_target_m_s) / v_target_m_s * 100
    print(f"✓ McCallum: {resultados['McCallum']:.4f} mm/día (error: {error_mccallum:.2f}%) 🔄 CORREGIDO")
except Exception as e:
    print(f"❌ McCallum: ERROR - {e}")
    resultados['McCallum'] = np.nan

# 4. Keery
try:
    v_keery = keery_method(
        amplitude_shallow=A_shallow,
        amplitude_deep=A_deep,
        phase_shallow=phase_shallow,
        phase_deep=phase_deep,
        depth_difference=DELTA_Z,
        thermal_diffusivity=ALPHA,
        angular_frequency=OMEGA,
        thermal_conductivity=LAMBDA,
        heat_capacity_water=C_W,
        heat_capacity_sediment=C_S
    )
    resultados['Keery'] = v_keery * 86400 * 1000
    error_keery = abs(v_keery - v_target_m_s) / v_target_m_s * 100
    print(f"✓ Keery: {resultados['Keery']:.4f} mm/día (error: {error_keery:.2f}%)")
except Exception as e:
    print(f"❌ Keery: ERROR - {e}")
    resultados['Keery'] = np.nan

# 5. Luce
try:
    v_luce = luce_method(
        amplitude_shallow=A_shallow,
        amplitude_deep=A_deep,
        depth_difference=DELTA_Z,
        angular_frequency=OMEGA
    )
    resultados['Luce'] = v_luce * 86400 * 1000
    error_luce = abs(v_luce - v_target_m_s) / v_target_m_s * 100
    print(f"✓ Luce: {resultados['Luce']:.4f} mm/día (error: {error_luce:.2f}%)")
except Exception as e:
    print(f"❌ Luce: ERROR - {e}")
    resultados['Luce'] = np.nan

# ============================================================================
# COEFICIENTE DE VARIACIÓN
# ============================================================================

print("\n" + "=" * 70)
print("📊 RESUMEN Y COEFICIENTE DE VARIACIÓN")
print("=" * 70)

valores_validos = [v for v in resultados.values() if not np.isnan(v)]
media = np.mean(valores_validos)
std = np.std(valores_validos, ddof=1)
cv = (std / media) * 100

print(f"\n{'Método':<20} {'Resultado [mm/día]':<20} {'Estado':<20}")
print("-" * 70)
print(f"{'Objetivo':<20} {TARGET_FLUX:<20.2f} {'Referencia':<20}")
for metodo, valor in resultados.items():
    if not np.isnan(valor):
        error = abs(valor - TARGET_FLUX) / TARGET_FLUX * 100
        if error < 5:
            estado = "✓✓ Excelente"
        elif error < 20:
            estado = "✓ Aceptable"
        else:
            estado = "⚠️ Requiere ajuste"
        print(f"{metodo:<20} {valor:<20.4f} {estado:<20}")
    else:
        print(f"{metodo:<20} {'ERROR':<20} {'❌ Falló':<20}")

print(f"\n📈 COEFICIENTE DE VARIACIÓN (CV):")
print(f"   Media: {media:.4f} mm/día")
print(f"   Desviación estándar: {std:.4f} mm/día")
print(f"   CV: {cv:.2f}%")
print(f"   Objetivo: < 20%")

if cv < 20:
    print(f"   ✓✓✓ OBJETIVO ALCANZADO: CV = {cv:.2f}% < 20%")
else:
    print(f"   ❌ REQUIERE MEJORA: CV = {cv:.2f}% > 20%")

print("\n" + "=" * 70)
print("FIN DE LA VALIDACIÓN")
print("=" * 70)
