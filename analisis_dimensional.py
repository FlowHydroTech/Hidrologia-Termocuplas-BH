"""
Análisis Dimensional Completo - Método Hatch-Phase
Investigación de la causa del error de magnitud
"""
import numpy as np

print("=" * 80)
print("ANÁLISIS DIMENSIONAL - MÉTODO HATCH-PHASE")
print("=" * 80)

# ============================================================================
# 1. PARÁMETROS FÍSICOS
# ============================================================================
lambda_val = 2.0        # W/(m·K)
Cs = 2.5e6              # J/(m³·K)
Cw = 4.18e6             # J/(m³·K)
alpha = lambda_val / Cs  # m²/s
omega = 2 * np.pi / 86400  # rad/s

delta_z = 0.10  # m
delta_phi = 0.4828  # rad (medido en análisis armónico)

print(f"\nParámetros:")
print(f"  λ = {lambda_val} W/(m·K)")
print(f"  Cs = {Cs:.2e} J/(m³·K)")
print(f"  Cw = {Cw:.2e} J/(m³·K)")
print(f"  α = λ/Cs = {alpha:.6e} m²/s")
print(f"  ω = 2π/86400 = {omega:.6e} rad/s")
print(f"  Δz = {delta_z} m")
print(f"  Δφ (medido) = {delta_phi:.4f} rad")

# ============================================================================
# 2. ECUACIÓN ACTUAL (INCORRECTA)
# ============================================================================
print("\n" + "=" * 80)
print("ECUACIÓN ACTUAL en vflux_methods.py (INCORRECTA)")
print("=" * 80)

v_actual = (4 * alpha * delta_phi) / (omega * delta_z**2)
v_actual_mm_day = v_actual * 86400 * 1000

print(f"\n  v = (4 × α × Δφ) / (ω × Δz²)")
print(f"  v = (4 × {alpha:.2e} × {delta_phi}) / ({omega:.2e} × {delta_z}²)")
print(f"  v = {v_actual:.6e} m/s")
print(f"  v = {v_actual_mm_day:.2f} mm/día")
print(f"\n  ❌ ERROR: Sobrestima el flujo por factor ~{v_actual_mm_day/5:.0f}x")

# ============================================================================
# 3. TEORÍA CORRECTA - Stallman (1965)
# ============================================================================
print("\n" + "=" * 80)
print("TEORÍA CORRECTA - Stallman (1965)")
print("=" * 80)

print("""
Para propagación de onda térmica con advección vertical:

Desfase total = Desfase conductivo + Desfase advectivo

Δφ_total = √((ω×Δz²)/(4α)) + (v×Cw×Δz)/(2λ)
           └─ sin flujo ──┘   └── por flujo ──┘

Despejando v:

v = [Δφ_total - √((ω×Δz²)/(4α))] × (2λ)/(Cw×Δz)
""")

# ============================================================================
# 4. CALCULAR TÉRMINOS
# ============================================================================
print("=" * 80)
print("CÁLCULO CON ECUACIÓN CORRECTA")
print("=" * 80)

# Término conductivo (sin flujo)
phi_conductivo = np.sqrt((omega * delta_z**2) / (4 * alpha))

print(f"\n1. Término conductivo (propagación pura):")
print(f"   Δφ_cond = √((ω×Δz²)/(4α))")
print(f"   Δφ_cond = √(({omega:.2e}×{delta_z}²)/(4×{alpha:.2e}))")
print(f"   Δφ_cond = {phi_conductivo:.4f} rad")

# Desfase por advección
phi_advectivo = delta_phi - phi_conductivo

print(f"\n2. Desfase por advección:")
print(f"   Δφ_adv = Δφ_total - Δφ_cond")
print(f"   Δφ_adv = {delta_phi:.4f} - {phi_conductivo:.4f}")
print(f"   Δφ_adv = {phi_advectivo:.6f} rad")

# Recuperar flujo
if phi_advectivo > 0:
    v_correcto = phi_advectivo / delta_z * (2 * lambda_val) / Cw
    v_correcto_mm_day = v_correcto * 86400 * 1000
    
    print(f"\n3. Flujo vertical:")
    print(f"   v = (Δφ_adv/Δz) × (2λ/Cw)")
    print(f"   v = ({phi_advectivo:.6f}/{delta_z}) × (2×{lambda_val}/{Cw:.2e})")
    print(f"   v = {v_correcto:.6e} m/s")
    print(f"   v = {v_correcto_mm_day:.4f} mm/día")
else:
    print(f"\n   ⚠️  Δφ_adv es NEGATIVO ({phi_advectivo:.6f})")
    print(f"      Esto indica flujo ascendente o error en parámetros")
    v_correcto_mm_day = 0

# ============================================================================
# 5. VERIFICACIÓN CON DATOS SINTÉTICOS
# ============================================================================
print("\n" + "=" * 80)
print("VERIFICACIÓN: Comparar con Flujo Objetivo")
print("=" * 80)

TARGET_FLUX = 5.0  # mm/día (usado en generate_synthetic_data.py)
v_objetivo = TARGET_FLUX * 1e-3 / 86400  # m/s

# Recalcular el desfase que debería generar ese flujo
term_cond_generacion = np.sqrt((omega * delta_z**2) / (4 * alpha))
term_adv_generacion = (v_objetivo * Cw * delta_z) / (2 * lambda_val)
delta_phi_esperado = term_cond_generacion + term_adv_generacion

print(f"\nFlujo objetivo: {TARGET_FLUX} mm/día")
print(f"\nDesfase esperado para ese flujo:")
print(f"  Δφ_cond = {term_cond_generacion:.4f} rad")
print(f"  Δφ_adv  = {term_adv_generacion:.6f} rad")
print(f"  Δφ_total = {delta_phi_esperado:.4f} rad")

print(f"\nDesfase medido en datos:")
print(f"  Δφ_medido = {delta_phi:.4f} rad")

if abs(delta_phi - delta_phi_esperado) < 0.001:
    print(f"\n  ✓ Coincide perfectamente!")
else:
    print(f"\n  Diferencia: {abs(delta_phi - delta_phi_esperado):.6f} rad")

# ============================================================================
# 6. RESUMEN COMPARATIVO
# ============================================================================
print("\n" + "=" * 80)
print("RESUMEN COMPARATIVO")
print("=" * 80)

print(f"\n{'Método':<30} {'Flujo (mm/día)':<15} {'Error'}")
print("-" * 80)
print(f"{'Objetivo (datos sintéticos)':<30} {TARGET_FLUX:>14.2f}")
print(f"{'Ecuación ACTUAL (incorrecta)':<30} {v_actual_mm_day:>14.2f}  ❌ {abs(v_actual_mm_day-TARGET_FLUX)/TARGET_FLUX*100:>6.0f}%")

if phi_advectivo > 0:
    error_correcto = abs(v_correcto_mm_day - TARGET_FLUX) / TARGET_FLUX * 100
    if error_correcto < 1:
        simbolo = "✅"
    else:
        simbolo = "⚠️"
    print(f"{'Ecuación CORREGIDA':<30} {v_correcto_mm_day:>14.4f}  {simbolo} {error_correcto:>6.2f}%")

# ============================================================================
# 7. CONCLUSIÓN
# ============================================================================
print("\n" + "=" * 80)
print("CONCLUSIÓN")
print("=" * 80)

print("""
🔍 CAUSA DEL ERROR IDENTIFICADA:

La ecuación implementada:
  v = (4 × α × Δφ) / (ω × Δz²)

NO incluye el término de desfase conductivo. Esta ecuación asume que TODO
el desfase de fase medido es causado por advección, cuando en realidad
gran parte del desfase es causado por la conducción térmica pura.

Ecuación CORRECTA:
  v = [Δφ - √((ω×Δz²)/(4α))] × (2λ)/(Cw×Δz)
       └── restar desfase conductivo ───┘

ACCIÓN REQUERIDA:
  1. Corregir hatch_phase_method() en vflux_methods.py
  2. Revisar también McCallum, Keery y Luce (mismo problema probable)
  3. Re-ejecutar análisis con ecuaciones corregidas
""")

print("=" * 80)
