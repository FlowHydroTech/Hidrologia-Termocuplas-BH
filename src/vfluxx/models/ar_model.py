import numpy as np
from statsmodels.tsa.ar_model import AutoReg

def fit_ar_model(temps, order=12):
    """
    Fit AR model to temperature data.
    """
    model = AutoReg(temps, lags=order, old_names=False)
    fit = model.fit()
    return fit
