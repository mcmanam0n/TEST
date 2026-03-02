import numpy as np
from sklearn.isotonic import IsotonicRegression


def fit_calibrator(probs: np.ndarray, y: np.ndarray) -> IsotonicRegression:
    calib = IsotonicRegression(out_of_bounds='clip')
    calib.fit(probs, y)
    return calib
