import unittest
import numpy as np
import pandas as pd
from vfluxx.preprocess import build_dataframe, resample_temperatures
from vfluxx.flux_methods import estimate_flux, compute_flux_sensitivity

class TestFluxMethods(unittest.TestCase):
    def test_estimate_flux(self):
        time = np.arange(0, 3600, 600)
        temps = np.random.rand(6)
        df = build_dataframe(time, temps)
        df_resampled = resample_temperatures(df, freq='15min')
        flux = estimate_flux(df_resampled)
        self.assertIsInstance(flux, float)

    def test_compute_flux_sensitivity(self):
        time = np.arange(0, 3600, 600)
        temps = np.random.rand(6)
        df = build_dataframe(time, temps)
        df_resampled = resample_temperatures(df, freq='15min')
        sensitivity = compute_flux_sensitivity(df_resampled)
        self.assertIsInstance(sensitivity, float)

if __name__ == "__main__":
    unittest.main()
