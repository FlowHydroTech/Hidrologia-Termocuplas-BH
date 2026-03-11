"""
Tests para los métodos de cálculo de flujo VFLUX2.
"""

import unittest
import sys
from pathlib import Path
import numpy as np

# Añadir el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from vfluxx.vflux_methods import calculate_vflux_all_methods


class TestVfluxMethods(unittest.TestCase):
    """Tests para los 5 métodos VFLUX2."""
    
    def setUp(self):
        """Configurar parámetros térmicos estándar."""
        self.lambda_s = 1.8  # W/m·K
        self.C_s = 2.8e6     # J/m³·K
        self.C_w = 4.18e6    # J/m³·K
        self.omega = 2 * np.pi / 86400  # rad/s
    
    def test_calculate_all_methods_returns_dict(self):
        """Verificar que la función retorna un diccionario con resultados."""
        results = calculate_vflux_all_methods(
            amplitude_shallow=3.0,
            amplitude_deep=1.5,
            phase_shallow=0.5,
            phase_deep=1.8,
            depth_difference=0.28,
            thermal_conductivity=self.lambda_s,
            heat_capacity_sediment=self.C_s,
            heat_capacity_water=self.C_w,
            angular_frequency=self.omega
        )
        self.assertIsInstance(results, dict)
        self.assertIn('flux_mm_day', results)
        self.assertIn('flux_m_s', results)
    
    def test_all_five_methods_present(self):
        """Verificar que los 5 métodos están presentes en los resultados."""
        results = calculate_vflux_all_methods(
            amplitude_shallow=3.0,
            amplitude_deep=1.5,
            phase_shallow=0.5,
            phase_deep=1.8,
            depth_difference=0.28,
            thermal_conductivity=self.lambda_s,
            heat_capacity_sediment=self.C_s,
            heat_capacity_water=self.C_w,
            angular_frequency=self.omega
        )
        expected_methods = ['hatch_amplitude', 'hatch_phase', 'keery', 'mccallum', 'luce']
        for method in expected_methods:
            self.assertIn(method, results['flux_mm_day'])
    
    def test_positive_amplitude_ratio_gives_positive_flux(self):
        """Con A_shallow > A_deep, Hatch-Amplitude debe dar flujo positivo."""
        results = calculate_vflux_all_methods(
            amplitude_shallow=3.0,
            amplitude_deep=1.0,
            phase_shallow=0.5,
            phase_deep=1.5,
            depth_difference=0.28,
            thermal_conductivity=self.lambda_s,
            heat_capacity_sediment=self.C_s,
            heat_capacity_water=self.C_w,
            angular_frequency=self.omega
        )
        # Hatch-Amplitude debe ser positivo cuando Ar > 1
        self.assertGreater(results['flux_mm_day']['hatch_amplitude'], 0)
    
    def test_invalid_amplitude_returns_nan(self):
        """Amplitudes negativas o cero deben retornar NaN."""
        results = calculate_vflux_all_methods(
            amplitude_shallow=0,
            amplitude_deep=1.5,
            phase_shallow=0.5,
            phase_deep=1.8,
            depth_difference=0.28,
            thermal_conductivity=self.lambda_s,
            heat_capacity_sediment=self.C_s,
            heat_capacity_water=self.C_w,
            angular_frequency=self.omega
        )
        self.assertTrue(np.isnan(results['flux_mm_day']['hatch_amplitude']))


if __name__ == "__main__":
    unittest.main()
