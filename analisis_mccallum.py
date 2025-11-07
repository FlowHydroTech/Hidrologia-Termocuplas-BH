"""
Análisis detallado del método McCallum (2012)
para entender por qué funciona correctamente.
"""

import numpy as np

# Parámetros
v_real = 5.0 / 86400 / 1000
delta_z = 0.30
lambda_s = 2.0
C_s = 2.5e6
C_w = 4.18e6
alpha = lambda_s / C_s
omega = 2 * np.pi / 86400

# Desfases y amplitudes
delta_phi_conductivo = np.sqrt((omega * delta_z**2) / (4 * alpha))
delta_phi_advectivo = (v_real * C_w * delta_z) / (2 * lambda_s)
delta_phi_total = delta_phi_conductivo + delta_phi_advectivo

Ar = np.exp((v_real * delta_z) / alpha)
delta_A = np.log(Ar)

print("="*80)
print("ANÁLISIS DETALLADO: McCallum (2012)")
print("="*80)

print("\n📐 ECUACIÓN DE McCALLUM:")
print("v = (α/Δz) × [ΔA + √(ΔA² + ωΔz²/(4α) - Δφ²)]")

print("\n🔍 ANÁLISIS TÉRMINO POR TÉRMINO:")
print(f"\nΔA = ln(Ar) = {delta_A:.10f}")
print(f"ΔA² = {delta_A**2:.10f}")

term_omega = (omega * delta_z**2) / (4 * alpha)
print(f"\nωΔz²/(4α) = {term_omega:.10f}")

print(f"\nΔφ = {delta_phi_total:.10f} rad")
print(f"Δφ² = {delta_phi_total**2:.10f}")

inside_sqrt = delta_A**2 + term_omega - delta_phi_total**2
print(f"\nDentro de √: ΔA² + ωΔz²/(4α) - Δφ²")
print(f"           = {delta_A**2:.10f} + {term_omega:.10f} - {delta_phi_total**2:.10f}")
print(f"           = {inside_sqrt:.10f}")

print("\n⚠️ OBSERVACIÓN CRÍTICA:")
if inside_sqrt < 0:
    print("   ¡El término dentro de √ es NEGATIVO!")
    print("   Esto significa que la ecuación tiene un problema matemático.")
    print(f"   √({inside_sqrt:.10f}) no está definido en los reales.")
    
    print("\n   El código implementado hace:")
    print("   if term2_inside < 0:")
    print("       return hatch_amplitude_method(...)")
    print("\n   ¡Por eso McCallum 'funciona' - está usando HATCH-AMPLITUDE como fallback!")
    
elif abs(inside_sqrt) < 1e-10:
    print("   El término dentro de √ es PRÁCTICAMENTE CERO!")
    print("   Esto significa: √(~0) ≈ 0")
    print("\n   Por tanto:")
    print("   v = (α/Δz) × [ΔA + 0]")
    print("   v = (α/Δz) × ΔA")
    print("\n   ¡Esto es EXACTAMENTE la ecuación de Hatch-Amplitude!")
    print("   McCallum se reduce a Hatch-Amplitude cuando Δφ² ≈ ΔA² + ωΔz²/(4α)")
    
else:
    sqrt_term = np.sqrt(inside_sqrt)
    print(f"   √(...) = {sqrt_term:.10f}")
    v_calc = (alpha / delta_z) * (delta_A + sqrt_term)
    print(f"\n   v = (α/Δz) × [{delta_A:.10f} + {sqrt_term:.10f}]")
    print(f"   v = {v_calc * 86400 * 1000:.4f} mm/día")

print("\n" + "="*80)
print("INTERPRETACIÓN FÍSICA")
print("="*80)

print("\n🧮 Relación entre términos:")
print(f"   ΔA² = {delta_A**2:.10f}")
print(f"   ωΔz²/(4α) = {term_omega:.10f}")
print(f"   SUMA = {delta_A**2 + term_omega:.10f}")
print(f"   ")
print(f"   Δφ² = {delta_phi_total**2:.10f}")

print("\n💡 INSIGHT:")
print("   Para flujos pequeños (como 5 mm/día):")
print("   - ΔA es muy pequeño (~0.02)")
print("   - Δφ está dominado por el término conductivo")
print("   - El término ωΔz²/(4α) = Δφ_conductivo²")
print("   ")
print(f"   Verificación: Δφ_conductivo² = {delta_phi_conductivo**2:.10f}")
print(f"   vs ωΔz²/(4α) = {term_omega:.10f}")
print(f"   Diferencia: {abs(delta_phi_conductivo**2 - term_omega):.2e}")

print("\n⚠️ ENTONCES:")
print("   ΔA² + ωΔz²/(4α) ≈ ΔA² + Δφ_conductivo²")
print("   ")
print("   Δφ² = (Δφ_conductivo + Δφ_advectivo)²")
print("       = Δφ_conductivo² + 2×Δφ_conductivo×Δφ_advectivo + Δφ_advectivo²")
print("   ")
print("   Para flujos pequeños: Δφ_advectivo << Δφ_conductivo")
print(f"   ({delta_phi_advectivo:.6f} << {delta_phi_conductivo:.6f})")
print("   ")
print("   Por tanto:")
print("   Δφ² ≈ Δφ_conductivo² + término_cruzado")
print("   ")
print("   Y el término dentro de √:")
print("   ΔA² + Δφ_conductivo² - (Δφ_conductivo² + término_cruzado)")
print("   ≈ ΔA² - término_cruzado")
print("   ")
print("   Como ΔA² es del mismo orden que término_cruzado para flujos pequeños,")
print("   ¡el resultado es casi cero!")

print("\n" + "="*80)
print("CONCLUSIÓN")
print("="*80)
print("\n✅ McCallum (2012) PARECE correcta porque:")
print("   1. Para flujos pequeños, el término √(...) → 0")
print("   2. La ecuación se reduce a Hatch-Amplitude")
print("   3. Hatch-Amplitude está correcta")
print("   ")
print("⚠️ PERO necesitamos verificar:")
print("   1. ¿Funciona para flujos grandes?")
print("   2. ¿La ecuación original del paper es esta?")
print("   3. ¿O la implementación tiene un error que se cancela?")

# Probar con flujo más grande
print("\n" + "="*80)
print("PRUEBA CON FLUJO MAYOR (50 mm/día)")
print("="*80)

v_real_2 = 50.0 / 86400 / 1000
delta_phi_conductivo_2 = np.sqrt((omega * delta_z**2) / (4 * alpha))
delta_phi_advectivo_2 = (v_real_2 * C_w * delta_z) / (2 * lambda_s)
delta_phi_total_2 = delta_phi_conductivo_2 + delta_phi_advectivo_2

Ar_2 = np.exp((v_real_2 * delta_z) / alpha)
delta_A_2 = np.log(Ar_2)

inside_sqrt_2 = delta_A_2**2 + term_omega - delta_phi_total_2**2
print(f"\nΔA² = {delta_A_2**2:.10f}")
print(f"ωΔz²/(4α) = {term_omega:.10f}")
print(f"Δφ² = {delta_phi_total_2**2:.10f}")
print(f"Dentro de √ = {inside_sqrt_2:.10f}")

if inside_sqrt_2 < 0:
    print("\n❌ Término negativo - McCallum usa Hatch-Amplitude como fallback")
    v_calc_2 = (alpha / delta_z) * delta_A_2
else:
    sqrt_term_2 = np.sqrt(inside_sqrt_2)
    v_calc_2 = (alpha / delta_z) * (delta_A_2 + sqrt_term_2)
    
print(f"\nv calculado: {v_calc_2 * 86400 * 1000:.2f} mm/día")
print(f"v real:      {v_real_2 * 86400 * 1000:.2f} mm/día")
print(f"Error:       {abs(v_calc_2 - v_real_2)/v_real_2*100:.2f}%")
