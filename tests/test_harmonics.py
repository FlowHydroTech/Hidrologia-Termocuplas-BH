"""
Tests para el módulo de análisis armónico.
"""

import pytest
import numpy as np
import pandas as pd
import sys
from pathlib import Path

# Añadir el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from vfluxx.harmonic_analysis import (
    compute_ar_spectrum,
    fit_harmonic_model,
    analyze_sensor_pair
)


def test_compute_ar_spectrum():
    """Test básico de espectro AR con señal sintética."""
    # Crear señal sintética con ciclo de 24 horas
    n_points = 48 * 2  # 2 días a 30 min = 96 puntos
    t = np.linspace(0, 48, n_points)  # horas
    signal = 10 + 3 * np.sin(2 * np.pi * t / 24)  # Ciclo 24h
    
    # compute_ar_spectrum espera DataFrame con columna 'temperature'
    df = pd.DataFrame({'temperature': signal})
    spectrum, freqs = compute_ar_spectrum(df, order=12)
    
    assert len(freqs) > 0
    assert len(spectrum) == len(freqs)
    assert all(s >= 0 for s in spectrum)  # Espectro no negativo


def test_analyze_sensor_pair():
    """Test de análisis de par de sensores."""
    # Crear datos sintéticos con atenuación y desfase
    n_points = 48 * 3  # 3 días
    t = np.linspace(0, 72, n_points)  # horas
    
    # Sensor superficial: mayor amplitud
    temp_shallow = 15 + 4 * np.sin(2 * np.pi * t / 24)
    
    # Sensor profundo: menor amplitud y desfasado
    temp_deep = 15 + 2 * np.sin(2 * np.pi * t / 24 - np.pi/6)
    
    result = analyze_sensor_pair(t, temp_shallow, temp_deep, period_hours=24.0)
    
    # La función retorna claves A_shallow, A_deep directamente
    assert 'A_shallow' in result
    assert 'A_deep' in result
    assert result['A_shallow'] > result['A_deep']


def test_fit_harmonic_model():
    """Test de ajuste de modelo armónico."""
    # Parámetros conocidos
    mean = 10
    amplitude = 5
    period = 24  # Ciclo diario en horas
    phase = np.pi / 4
    
    # Generar datos sintéticos con ruido mínimo
    t = np.linspace(0, 72, 144)  # 72 horas, 30 min intervalo
    temperature = mean + amplitude * np.sin(2 * np.pi * t / period + phase)
    
    # Ajustar modelo
    params = fit_harmonic_model(t, temperature, period_hours=24.0)
    
    # Verificar parámetros
    assert 'amplitude' in params
    assert 'phase' in params
    assert 'offset' in params
    assert 'r_squared' in params
    assert np.isclose(params['offset'], mean, rtol=0.1)
    assert np.isclose(params['amplitude'], amplitude, rtol=0.2)
    assert params['r_squared'] > 0.9  # Debe ser buen ajuste sin ruido


if __name__ == '__main__':
    pytest.main([__file__])
