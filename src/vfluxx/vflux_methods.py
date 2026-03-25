"""
vflux_methods.py - Implementación de los 5 métodos de cálculo de flujo vertical VFLUX2.

Métodos:
    1. McCallum (2012) - Combinado amplitud + fase (recomendado)
    2. Hatch Amplitud (2006) - Basado en atenuación de amplitud
    3. Hatch Fase (2006) - Basado en desfase temporal
    4. Keery (2007) - Amplitud + fase con capacidades caloríficas
    5. Luce (2013) - Empírico simplificado

Referencias:
    - Hatch et al. (2006), Water Resources Research
    - Keery et al. (2007), Ground Water
    - McCallum et al. (2012), Journal of Hydrology
    - Luce et al. (2013), Water Resources Research
    - Gordon et al. (2012) - VFLUX2 MATLAB toolbox
"""

import numpy as np
from scipy.optimize import brentq


def _flux_hatch_amplitude(A_shallow, A_deep, dz, alpha_e, omega, beta=0.0):
    """
    Método Hatch - Amplitud (2006) — Ecuación completa no-lineal.

    Implementa Hatch et al. (2006) Eq. 6a con dispersividad térmica,
    idéntico a VFLUX2 MATLAB (Gordon et al., 2012):

        f(v) = (2·α_eff/Δz)·ln(Ar) + √((√(v⁴+(4ωα_eff)²)+v²)/2) − v = 0

    donde α_eff = α_e + β·|v| (difusividad efectiva con dispersividad)
    y Ar = A_deep / A_shallow (< 1 para atenuación normal).

    Se resuelve con brentq (equivalente a fzero de MATLAB).

    Returns: thermal front velocity v_t [m/s] (NO es seepage flux q).
    Para obtener q: multiplicar por C_total/C_water.
    """
    if A_shallow <= 0 or A_deep <= 0:
        return np.nan
    Ar = A_deep / A_shallow  # MATLAB convention: lower/upper < 1
    if Ar <= 0 or Ar >= 1.0:
        return np.nan

    ln_Ar = np.log(Ar)  # Negative for normal attenuation

    def equation(v):
        alpha_eff = alpha_e + abs(beta * v)
        term1 = (2.0 * alpha_eff / dz) * ln_Ar
        inner = np.sqrt(v**4 + (4.0 * omega * alpha_eff)**2)
        term2 = np.sqrt((inner + v**2) / 2.0)
        return term1 + term2 - v

    # Solve with progressively wider brackets (like MATLAB's fzero)
    for bracket in [(0, 1e-2), (-1e-3, 1e-1), (-1e-2, 1.0)]:
        try:
            v_thermal = brentq(equation, bracket[0], bracket[1], maxiter=200)
            return v_thermal
        except (ValueError, RuntimeError):
            continue

    return np.nan


def _flux_hatch_phase(dz, delta_phi, alpha_e, omega):
    """
    Método Hatch - Fase (2006).

    Basado en la velocidad de propagación de la onda térmica:
    v = omega * dz / delta_phi - 2 * alpha_e * delta_phi / dz

    Simplificado para flujos pequeños (Hatch 2006 Eq. 8):
    v = omega * dz^2 / (2 * alpha_e * delta_phi)  ... no exacta

    Forma VFLUX2 (Gordon 2012):
    v_phase = (2 * Ke / (rho_c)) * [delta_phi/dz + sqrt(omega/(2*alpha_e))]

    Usamos la forma analítica:
    v = (2 * alpha_e / dz) * (delta_phi / dz - sqrt(omega / (2 * alpha_e)))
    No; la correcta:
    v = 2 * alpha_e * (delta_phi / dz^2) - (omega * dz) / (delta_phi)
    
    Forma correcta de Hatch (2006) Ec. 4b:
    v = (2*Ke/(rho_w*cw)) * [delta_phi/dz - sqrt(omega/(2*alpha))]
    ~ = 2*alpha_e * delta_phi/dz - sqrt(2*alpha_e*omega)
    """
    if abs(delta_phi) < 1e-10:
        return np.nan
    # Forma simplificada robusta
    v = 2.0 * alpha_e * (delta_phi / (dz**2)) - np.sqrt(2.0 * alpha_e * omega)
    return -v  # Convención: positivo = towards deeper sensor


def _flux_keery(A_shallow, A_deep, delta_phi, dz, alpha_e, omega):
    """
    Método Keery (2007).
    
    Combina amplitud y fase de manera independiente y luego promedia.
    Keery usa las mismas ecuaciones base pero con notación diferente
    y considera las capacidades caloríficas explícitamente.
    
    v_keery = alpha_e / dz * [ln(Ar) + delta_phi]
    """
    if A_shallow <= 0 or A_deep <= 0:
        return np.nan
    
    Ar = A_shallow / A_deep
    if Ar <= 0:
        return np.nan
    
    # Keery: combinación de ln(Ar) y delta_phi
    ln_Ar = np.log(Ar)
    v = (alpha_e / dz) * (ln_Ar + delta_phi)
    return v


def _flux_mccallum(A_shallow, A_deep, delta_phi, dz, alpha_e, omega, C_water, C_sediment):
    """
    Método McCallum (2012) - Combinado.
    
    Resuelve simultáneamente amplitud y fase para obtener v y Ke:
    
    v = (C_water / C_sediment) * (2*Ke/dz) * 
        sqrt(delta_phi^2 + ln(Ar)^2) / (2*delta_phi)
    
    Donde Ke se obtiene de:
    Ke = (omega * dz^2 * delta_phi) / (2 * (delta_phi^2 + ln(Ar)^2))
    
    Forma simplificada (McCallum 2012 Eq. 10):
    gamma = sqrt(delta_phi^2 + ln(Ar)^2)
    v = 2*Ke*C_water / (C_sediment * dz) * gamma
    """
    if A_shallow <= 0 or A_deep <= 0:
        return np.nan
    
    Ar = A_shallow / A_deep
    if Ar <= 0:
        return np.nan
    
    ln_Ar = np.log(Ar)
    
    if abs(delta_phi) < 1e-10 and abs(ln_Ar) < 1e-10:
        return 0.0
    
    gamma = np.sqrt(delta_phi**2 + ln_Ar**2)
    
    # Difusividad térmica efectiva del McCallum
    if gamma > 0:
        Ke = (omega * dz**2 * delta_phi) / (2.0 * gamma**2)
    else:
        Ke = alpha_e
    
    # Flujo vertical
    if delta_phi > 1e-10:
        v = (2.0 * Ke / dz) * (C_water / C_sediment) * gamma / (2.0 * delta_phi)
        v *= ln_Ar  # Signo del flujo
    else:
        # Si no hay desfase significativo, usar solo amplitud
        v = (2.0 * alpha_e / dz) * ln_Ar
    
    return v


def _flux_luce(A_shallow, A_deep, delta_phi, dz, alpha_e, omega):
    """
    Método Luce (2013) - Aproximación empírica simplificada.
    
    Luce usa una relación empírica entre el ratio de amplitud
    y el flujo vertical, calibrada con datos de campo.
    
    v_luce ≈ sqrt(8 * alpha_e * omega) * [1 - Ar] / Ar
    
    Válido para flujos moderados donde Ar no es extremo.
    """
    if A_shallow <= 0 or A_deep <= 0:
        return np.nan
    
    Ar = A_shallow / A_deep
    if Ar <= 0 or Ar > 100:
        return np.nan
    
    v = np.sqrt(8.0 * alpha_e * omega) * (1.0 - 1.0/Ar)
    return v


def calculate_vflux_all_methods(
    amplitude_shallow,
    amplitude_deep,
    phase_shallow,
    phase_deep,
    depth_difference,
    thermal_conductivity,
    heat_capacity_sediment,
    heat_capacity_water,
    angular_frequency,
    beta=0.0,
    quiet=False,
):
    """
    Calcula el flujo vertical usando los 5 métodos de VFLUX2.

    Parameters
    ----------
    amplitude_shallow : float
        Amplitud del armónico diario del sensor superficial (°C).
    amplitude_deep : float
        Amplitud del armónico diario del sensor profundo (°C).
    phase_shallow : float
        Fase del armónico del sensor superficial (rad).
    phase_deep : float
        Fase del armónico del sensor profundo (rad).
    depth_difference : float
        Diferencia de profundidad entre sensores (m).
    thermal_conductivity : float
        Conductividad térmica del sedimento (W/m·K).
    heat_capacity_sediment : float
        Capacidad calorífica volumétrica del sedimento (J/m³·K).
    heat_capacity_water : float
        Capacidad calorífica volumétrica del agua (J/m³·K).
    angular_frequency : float
        Frecuencia angular del ciclo (rad/s). Para diario: 2π/86400.
    beta : float
        Dispersividad térmica (m). Default 0.0.

    Returns
    -------
    dict con:
        'flux_m_s': dict - Flujos en m/s para cada método (seepage flux q)
        'flux_mm_day': dict - Flujos en mm/día para cada método
        'parameters': dict - Parámetros intermedios de cálculo
    """
    dz = depth_difference
    omega = angular_frequency
    Ke = thermal_conductivity
    Cs = heat_capacity_sediment
    Cw = heat_capacity_water

    # Difusividad térmica efectiva
    alpha_e = Ke / Cs

    # Heat capacity ratio: convierte v_thermal → seepage flux q
    # q = v_t * (C_total / C_water)
    # C_total ≈ C_sediment (medido por IDIEM como muestra bulk saturada)
    heat_capacity_ratio = Cs / Cw

    # Desfase
    delta_phi = phase_deep - phase_shallow
    if delta_phi < 0:
        delta_phi += 2 * np.pi

    A_s = amplitude_shallow
    A_d = amplitude_deep

    # --- Hatch Amplitude: ecuación completa + conversión v_t → q ---
    v_thermal_ha = _flux_hatch_amplitude(A_s, A_d, dz, alpha_e, omega, beta=beta)
    if v_thermal_ha is not None and not np.isnan(v_thermal_ha):
        q_ha = v_thermal_ha * heat_capacity_ratio
    else:
        q_ha = np.nan

    # Calcular cada método
    results_ms = {}
    results_ms['hatch_amplitude'] = q_ha
    results_ms['hatch_phase'] = _flux_hatch_phase(dz, delta_phi, alpha_e, omega)
    results_ms['keery'] = _flux_keery(A_s, A_d, delta_phi, dz, alpha_e, omega)
    results_ms['mccallum'] = _flux_mccallum(A_s, A_d, delta_phi, dz, alpha_e, omega, Cw, Cs)
    results_ms['luce'] = _flux_luce(A_s, A_d, delta_phi, dz, alpha_e, omega)

    # Convertir a mm/día
    MS_TO_MM_DAY = 86400.0 * 1000.0
    results_mm_day = {}
    for method, val in results_ms.items():
        if val is not None and not np.isnan(val):
            results_mm_day[method] = val * MS_TO_MM_DAY
        else:
            results_mm_day[method] = np.nan

    # Mostrar resumen
    if not quiet:
        print(f"  {'Método':<20} {'m/s':>12} {'mm/día':>12}")
        print(f"  {'-'*44}")
        for method in ['hatch_amplitude', 'mccallum']:
            v_ms = results_ms.get(method, np.nan)
            v_mm = results_mm_day.get(method, np.nan)
            if not np.isnan(v_mm):
                print(f"  {method:<20} {v_ms:>12.2e} {v_mm:>12.2f}")
            else:
                print(f"  {method:<20} {'NaN':>12} {'NaN':>12}")

    return {
        'flux_m_s': results_ms,
        'flux_mm_day': results_mm_day,
        'parameters': {
            'alpha_e': alpha_e,
            'delta_phi': delta_phi,
            'A_shallow': A_s,
            'A_deep': A_d,
            'dz': dz,
            'omega': omega,
            'Ke': Ke,
            'Cs': Cs,
            'Cw': Cw,
            'beta': beta,
            'heat_capacity_ratio': heat_capacity_ratio,
            'v_thermal_ha': v_thermal_ha,
        }
    }
