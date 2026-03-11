"""
Tests para el módulo de preprocesamiento.
"""

import unittest
import sys
from pathlib import Path
import numpy as np
import pandas as pd

# Añadir el directorio src al path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from vfluxx.preprocess import build_dataframe, resample_temperatures

class TestPreprocess(unittest.TestCase):
    def test_build_dataframe(self):
        time = np.arange(0, 100, 10)
        temps = np.random.rand(10)
        df = build_dataframe(time, temps)
        self.assertEqual(len(df), 10)
        self.assertIn('time', df.columns)
        self.assertIn('temperature', df.columns)

    def test_resample_temperatures(self):
        time = np.arange(0, 3600, 600)
        temps = np.random.rand(6)
        df = build_dataframe(time, temps)
        df_resampled = resample_temperatures(df, freq='15min')
        self.assertTrue(len(df_resampled) > 0)
        self.assertFalse(df_resampled['temperature'].isna().any())

if __name__ == "__main__":
    unittest.main()
