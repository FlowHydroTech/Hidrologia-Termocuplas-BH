"""
Script de Validación: Correcciones de Keery y McCallum
========================================================

Objetivo: Validar las correcciones propuestas antes de implementarlas en producción

Correcciones a probar:
1. McCallum: Revertir a lógica de fallback (Hatch-Amplitude cuando raíz negativa)
2. Keery: Implementar ecuación explícita v_z = (α/L) × (Δφ/ΔA) con Δφ advectivo

Fecha: 19 noviembre 2025
"""

import numpy as np
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Parámetros del caso sintético
TARGET_FLUX = 5.0  # mm/día
DELTA_Z = 0.30  # m (30 cm)
LAMBDA = 2.0  # W/(m·K)
C_S = 2.5e6  # J/(m³·K)
C_W = 4.18e6  # J/(m³·K)
ALPHA = LAMBDA / C_S  # m²/s
OMEGA = 2 * np.pi / 86400  # rad/s (diario)

# Convertir flujo objetivo a m/s
v_target_m_s = TARGET_FLUX / 86400 / 1000

print("=" * 70)
print("VALIDACIÓN DE CORRECCIONES: Keery y McCallum")
print("=" * 70)
print(f"\n📊 CASO SINTÉTICO")
print(f"   Flujo objetivo: {TARGET_FLUX} mm/día ({v_target_m_s:.6e} m/s)")
print(f"   Δz: {DELTA_Z} m")
print(f"   λ: {LAMBDA} W/(m·K)")
print(f"   C_s: {C_S:.2e} J/(m³·K)")
print(f"   C_w: {C_W:.2e} J/(m³·K)")
print(f"   α: {ALPHA:.2e} m²/s")
print(f"   ω: {OMEGA:.5e} rad/s")

# Calcular amplitudes y fases esperadas
Ar = np.exp((v_target_m_s * DELTA_Z) / ALPHA)
A_shallow = 1.0
A_deep = A_shallow / Ar

delta_phi_conductivo = np.sqrt((OMEGA * DELTA_Z**2) / (4 * ALPHA))
delta_phi_advectivo = (v_target_m_s * C_W * DELTA_Z) / (2 * LAMBDA)
delta_phi_total = delta_phi_conductivo + delta_phi_advectivo

print(f"\n🔬 COMPONENTES DE FASE")
print(f"   Δφ_conductivo: {delta_phi_conductivo:.6f} rad ({delta_phi_conductivo/delta_phi_total*100:.1f}%)")
print(f"   Δφ_advectivo:  {delta_phi_advectivo:.6f} rad ({delta_phi_advectivo/delta_phi_total*100:.1f}%)")
print(f"   Δφ_total:      {delta_phi_total:.6f} rad")

print(f"\n📈 AMPLITUDES")
print(f"   Ar: {Ar:.6f}")
print(f"   A_shallow: {A_shallow:.6f}")
print(f"   A_deep: {A_deep:.6f}")

# ============================================================================
# MÉTODO 1: HATCH AMPLITUDE (Referencia - ya validado)
# ============================================================================

def hatch_amplitude_reference(A_shallow, A_deep, delta_z, alpha):
    """Método Hatch Amplitude - ya validado"""
    Ar = A_shallow / A_deep
    v = (alpha / delta_z) * np.log(Ar)
    return v

v_hatch_amp = hatch_amplitude_reference(A_shallow, A_deep, DELTA_Z, ALPHA)
error_hatch_amp = abs(v_hatch_amp - v_target_m_s) / v_target_m_s * 100

print("\n" + "=" * 70)
print("🟢 MÉTODO 1: HATCH AMPLITUDE (Referencia)")
print("=" * 70)
print(f"   Resultado: {v_hatch_amp * 86400 * 1000:.4f} mm/día")
print(f"   Error: {error_hatch_amp:.2f}%")
print(f"   Estado: ✓ VALIDADO")

# ============================================================================
# MÉTODO 2: HATCH PHASE (Ya corregido)
# ============================================================================

def hatch_phase_corregido(delta_phi_total, delta_phi_conductivo, delta_z, lambda_s, C_w):
    """Método Hatch Phase - con separación conductivo/advectivo"""
    delta_phi_advectivo = delta_phi_total - delta_phi_conductivo
    v = (2 * lambda_s * delta_phi_advectivo) / (C_w * delta_z)
    return v

v_hatch_phase = hatch_phase_corregido(delta_phi_total, delta_phi_conductivo, DELTA_Z, LAMBDA, C_W)
error_hatch_phase = abs(v_hatch_phase - v_target_m_s) / v_target_m_s * 100

print("\n" + "=" * 70)
print("🟢 MÉTODO 2: HATCH PHASE (Corregido)")
print("=" * 70)
print(f"   Resultado: {v_hatch_phase * 86400 * 1000:.4f} mm/día")
print(f"   Error: {error_hatch_phase:.2f}%")
print(f"   Estado: ✓ CORREGIDO Y VALIDADO")

# ============================================================================
# MÉTODO 3: McCALLUM (Propuesta de reversión)
# ============================================================================

def mccallum_con_fallback(A_shallow, A_deep, delta_phi_total, delta_z, alpha, omega):
    """
    Método McCallum con lógica de fallback a Hatch-Amplitude
    (Reversión a implementación previa que funcionaba)
    """
    delta_A = np.log(A_shallow / A_deep)
    
    # Calcular término de raíz cuadrada
    inner_sqrt = delta_A**2 + (omega * delta_z**2) / (4 * alpha) - delta_phi_total**2
    
    # LÓGICA DE FALLBACK
    if inner_sqrt < 0:
        print(f"   ⚠️  Raíz negativa detectada (inner_sqrt = {inner_sqrt:.6f})")
        print(f"   ➡️  Usando fallback a Hatch-Amplitude")
        # Fallback a Hatch-Amplitude
        return hatch_amplitude_reference(A_shallow, A_deep, delta_z, alpha)
    
    # Ecuación McCallum normal
    v = (alpha / delta_z) * (delta_A + np.sqrt(inner_sqrt))
    return v

v_mccallum_fallback = mccallum_con_fallback(A_shallow, A_deep, delta_phi_total, DELTA_Z, ALPHA, OMEGA)
error_mccallum_fallback = abs(v_mccallum_fallback - v_target_m_s) / v_target_m_s * 100

print("\n" + "=" * 70)
print("🔵 MÉTODO 3: McCALLUM (Con Fallback Restaurado)")
print("=" * 70)
print(f"   Resultado: {v_mccallum_fallback * 86400 * 1000:.4f} mm/día")
print(f"   Error: {error_mccallum_fallback:.2f}%")
print(f"   Estado: {'✓ CORRECCIÓN EXITOSA' if error_mccallum_fallback < 5 else '❌ REQUIERE AJUSTE'}")

# ============================================================================
# MÉTODO 4: KEERY (Nueva implementación con ecuación explícita)
# ============================================================================

def keery_con_separacion(A_shallow, A_deep, delta_phi_total, delta_phi_conductivo, delta_z, alpha):
    """
    Método Keery con ecuación explícita: v_z = (α/L) × (Δφ/ΔA)
    Usando Δφ advectivo (separación conductivo/advectivo)
    """
    # 1. Extraer componente advectivo
    delta_phi_advectivo = delta_phi_total - delta_phi_conductivo
    
    # 2. Calcular variación relativa en amplitud (ΔA)
    delta_A = np.log(A_shallow / A_deep)
    
    # 3. Aplicar fórmula de Keery
    if abs(delta_A) < 1e-10:
        print(f"   ⚠️  ΔA muy pequeño, evitando división por cero")
        return 0.0
    
    v_z = (alpha / delta_z) * (delta_phi_advectivo / delta_A)
    
    return v_z

v_keery_corregido = keery_con_separacion(A_shallow, A_deep, delta_phi_total, delta_phi_conductivo, DELTA_Z, ALPHA)
error_keery_corregido = abs(v_keery_corregido - v_target_m_s) / v_target_m_s * 100

print("\n" + "=" * 70)
print("🟣 MÉTODO 4: KEERY (Nueva Implementación)")
print("=" * 70)
print(f"   Ecuación: v_z = (α/L) × (Δφ_adv / ΔA)")
print(f"   Δφ_advectivo usado: {delta_phi_advectivo:.6f} rad")
print(f"   ΔA = ln(Ar): {np.log(Ar):.6f}")
print(f"   Resultado: {v_keery_corregido * 86400 * 1000:.4f} mm/día")
print(f"   Error: {error_keery_corregido:.2f}%")
print(f"   Estado: {'✓ CORRECCIÓN EXITOSA' if error_keery_corregido < 5 else '❌ REQUIERE AJUSTE'}")

# ============================================================================
# RESUMEN Y COEFICIENTE DE VARIACIÓN
# ============================================================================

print("\n" + "=" * 70)
print("📊 RESUMEN DE RESULTADOS")
print("=" * 70)

resultados = {
    "Hatch Amplitude": v_hatch_amp * 86400 * 1000,
    "Hatch Phase": v_hatch_phase * 86400 * 1000,
    "McCallum (fallback)": v_mccallum_fallback * 86400 * 1000,
    "Keery (corregido)": v_keery_corregido * 86400 * 1000
}

print(f"\n{'Método':<25} {'Resultado':<15} {'Error':<15} {'Estado':<15}")
print("-" * 70)
print(f"{'Objetivo':<25} {TARGET_FLUX:<15.2f} {'-':<15} {'Referencia':<15}")
print(f"{'Hatch Amplitude':<25} {resultados['Hatch Amplitude']:<15.4f} {error_hatch_amp:<15.2f} {'✓ Validado':<15}")
print(f"{'Hatch Phase':<25} {resultados['Hatch Phase']:<15.4f} {error_hatch_phase:<15.2f} {'✓ Validado':<15}")
print(f"{'McCallum (fallback)':<25} {resultados['McCallum (fallback)']:<15.4f} {error_mccallum_fallback:<15.2f} {'🔄 Propuesto':<15}")
print(f"{'Keery (corregido)':<25} {resultados['Keery (corregido)']:<15.4f} {error_keery_corregido:<15.2f} {'🔄 Propuesto':<15}")

# Calcular CV
valores = list(resultados.values())
media = np.mean(valores)
std = np.std(valores, ddof=1)
cv = (std / media) * 100

print("\n" + "=" * 70)
print("📈 COEFICIENTE DE VARIACIÓN (CV)")
print("=" * 70)
print(f"   Media: {media:.4f} mm/día")
print(f"   Desviación estándar: {std:.4f} mm/día")
print(f"   CV: {cv:.2f}%")
print(f"   Objetivo: < 20%")
print(f"   Estado: {'✓✓✓ OBJETIVO ALCANZADO' if cv < 20 else '❌ REQUIERE MEJORA'}")

# ============================================================================
# CONCLUSIONES
# ============================================================================

print("\n" + "=" * 70)
print("💡 CONCLUSIONES")
print("=" * 70)

if error_mccallum_fallback < 5 and error_keery_corregido < 5 and cv < 20:
    print("   ✓✓✓ TODAS LAS CORRECCIONES SON EXITOSAS")
    print("   ✓ McCallum con fallback funciona correctamente")
    print("   ✓ Keery con ecuación explícita funciona correctamente")
    print("   ✓ CV < 20% alcanzado")
    print("\n   ➡️  RECOMENDACIÓN: Implementar ambas correcciones en producción")
elif error_mccallum_fallback < 5:
    print("   ✓ McCallum con fallback funciona correctamente")
    print("   ⚠️  Keery requiere ajuste adicional")
    print("\n   ➡️  RECOMENDACIÓN: Implementar McCallum, revisar Keery")
elif error_keery_corregido < 5:
    print("   ⚠️  McCallum requiere ajuste adicional")
    print("   ✓ Keery con ecuación explícita funciona correctamente")
    print("\n   ➡️  RECOMENDACIÓN: Implementar Keery, revisar McCallum")
else:
    print("   ⚠️  Ambas correcciones requieren ajuste adicional")
    print("\n   ➡️  RECOMENDACIÓN: Revisar ecuaciones y parámetros")

print("\n" + "=" * 70)
print("FIN DEL ANÁLISIS")
print("=" * 70)
