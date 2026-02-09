import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from statsmodels.tsa.ar_model import AutoReg
import matplotlib.pyplot as plt


def compute_ar_spectrum(sensor_series, order=12):
    """
    Compute AR(12) spectrum from temperature series.

    Parameters
    ----------
    sensor_series : pandas.DataFrame
        Resampled temperature data.
    order : int
        AR model order (default 12).

    Returns
    -------
    spectrum : np.ndarray
        Amplitude spectrum.
    freqs : np.ndarray
        Frequency values.
    """
    temps = sensor_series['temperature'].values
    nobs = len(temps)
    if nobs < 2:
        # Serie demasiado corta, omitir modelo AR y retornar espectro vacío
        return np.array([]), np.array([])
    ar_order = min(order, nobs - 1)
    if ar_order < 1:
        return np.array([]), np.array([])
    model = AutoReg(temps, lags=ar_order, old_names=False)
    fit = model.fit()
    ar_params = fit.params
    freqs = np.fft.rfftfreq(nobs, d=1)
    spectrum = np.abs(np.fft.rfft(temps))
    return spectrum, freqs


def clean_zero_freqs(freqs):
    """
    Remove zero frequencies from array.
    """
    return freqs[freqs > 0]


# ================================================================
# ANÁLISIS ARMÓNICO - Ajuste Sinusoidal (VFLUX2 style)
# ================================================================

def _sinusoidal(t, A, phi, offset, period):
    """Modelo sinusoidal: T(t) = A * sin(2π/P * t + φ) + offset"""
    return A * np.sin(2 * np.pi / period * t + phi) + offset


def fit_harmonic_model(time_hours, temperature, period_hours=24.0):
    """
    Ajusta un modelo armónico (sinusoidal) a una serie de temperatura
    para extraer amplitud y fase del componente diario.

    Parameters
    ----------
    time_hours : np.ndarray
        Vector de tiempo en horas desde el inicio.
    temperature : np.ndarray
        Serie de temperatura (°C).
    period_hours : float
        Período del armónico (default 24 horas = ciclo diario).

    Returns
    -------
    dict con:
        'amplitude': float - Amplitud del armónico (°C)
        'phase': float - Fase del armónico (rad)
        'offset': float - Temperatura media (°C)
        'period': float - Período usado (horas)
        'r_squared': float - Coeficiente de determinación R²
        'fitted': np.ndarray - Serie ajustada
    """
    time_hours = np.asarray(time_hours, dtype=float)
    temperature = np.asarray(temperature, dtype=float)

    # Estimaciones iniciales
    A0 = (np.nanmax(temperature) - np.nanmin(temperature)) / 2.0
    offset0 = np.nanmean(temperature)

    # Método FFT para estimar fase inicial
    n = len(temperature)
    temp_detrend = temperature - offset0
    fft_vals = np.fft.rfft(temp_detrend)
    freqs = np.fft.rfftfreq(n, d=(time_hours[1] - time_hours[0]) if n > 1 else 1.0)

    # Buscar componente más cercano a 1/period_hours
    target_freq = 1.0 / period_hours
    idx = np.argmin(np.abs(freqs - target_freq))
    if idx > 0:
        phi0 = np.angle(fft_vals[idx])
        A0_fft = 2.0 * np.abs(fft_vals[idx]) / n
        if A0_fft > 0:
            A0 = A0_fft
    else:
        phi0 = 0.0

    # Ajuste por mínimos cuadrados
    def model(t, A, phi, offset):
        return A * np.sin(2 * np.pi / period_hours * t + phi) + offset

    try:
        popt, pcov = curve_fit(
            model, time_hours, temperature,
            p0=[A0, phi0, offset0],
            maxfev=10000
        )
        A_fit, phi_fit, offset_fit = popt
    except Exception:
        # Fallback si curve_fit falla
        A_fit = A0
        phi_fit = phi0
        offset_fit = offset0

    # Asegurar amplitud positiva
    if A_fit < 0:
        A_fit = -A_fit
        phi_fit = phi_fit + np.pi

    # Normalizar fase a [0, 2π)
    phi_fit = phi_fit % (2 * np.pi)

    # R²
    fitted = model(time_hours, A_fit, phi_fit, offset_fit)
    ss_res = np.sum((temperature - fitted) ** 2)
    ss_tot = np.sum((temperature - np.mean(temperature)) ** 2)
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    return {
        'amplitude': float(A_fit),
        'phase': float(phi_fit),
        'offset': float(offset_fit),
        'period': period_hours,
        'r_squared': float(r_squared),
        'fitted': fitted
    }


def analyze_sensor_pair(time_hours, temp_shallow, temp_deep, period_hours=24.0):
    """
    Analiza un par de sensores a diferentes profundidades para obtener
    los parámetros armónicos necesarios para VFLUX2.

    Parameters
    ----------
    time_hours : np.ndarray
        Vector de tiempo en horas.
    temp_shallow : np.ndarray
        Temperatura del sensor más superficial (°C).
    temp_deep : np.ndarray
        Temperatura del sensor más profundo (°C).
    period_hours : float
        Período del armónico (default 24 horas).

    Returns
    -------
    dict con:
        'A_shallow': float - Amplitud sensor superficial (°C)
        'A_deep': float - Amplitud sensor profundo (°C)
        'phi_shallow': float - Fase sensor superficial (rad)
        'phi_deep': float - Fase sensor profundo (rad)
        'delta_A': float - ln(A_shallow/A_deep)
        'delta_phi': float - Desfase (phi_deep - phi_shallow) (rad)
        'amplitude_ratio': float - A_deep / A_shallow
        'r2_shallow': float - R² ajuste superficial
        'r2_deep': float - R² ajuste profundo
    """
    time_hours = np.asarray(time_hours, dtype=float)
    temp_shallow = np.asarray(temp_shallow, dtype=float)
    temp_deep = np.asarray(temp_deep, dtype=float)

    # Ajustar armónico a cada sensor
    fit_shallow = fit_harmonic_model(time_hours, temp_shallow, period_hours)
    fit_deep = fit_harmonic_model(time_hours, temp_deep, period_hours)

    A_s = fit_shallow['amplitude']
    A_d = fit_deep['amplitude']
    phi_s = fit_shallow['phase']
    phi_d = fit_deep['phase']

    # Razón de amplitud y desfase
    if A_s > 0 and A_d > 0:
        delta_A = np.log(A_s / A_d)
        amplitude_ratio = A_d / A_s
    else:
        delta_A = np.nan
        amplitude_ratio = np.nan

    # Desfase: la onda se propaga hacia abajo, esperamos phi_deep > phi_shallow
    delta_phi = phi_d - phi_s
    # Normalizar a [0, 2π) para que el desfase sea positivo
    if delta_phi < 0:
        delta_phi += 2 * np.pi

    return {
        'A_shallow': A_s,
        'A_deep': A_d,
        'phi_shallow': phi_s,
        'phi_deep': phi_d,
        'delta_A': delta_A,
        'delta_phi': delta_phi,
        'amplitude_ratio': amplitude_ratio,
        'r2_shallow': fit_shallow['r_squared'],
        'r2_deep': fit_deep['r_squared'],
        'fit_shallow': fit_shallow,
        'fit_deep': fit_deep,
    }
