import numpy as np
from sklearn.metrics import brier_score_loss, log_loss, mean_absolute_error


def expected_calibration_error(y_true: np.ndarray, p: np.ndarray, bins: int = 10) -> float:
    edges = np.linspace(0, 1, bins + 1)
    ece = 0.0
    for i in range(bins):
        m = (p >= edges[i]) & (p < edges[i + 1])
        if m.sum() == 0:
            continue
        ece += abs(y_true[m].mean() - p[m].mean()) * (m.sum() / len(y_true))
    return float(ece)


def compute_metrics(y_true: np.ndarray, p: np.ndarray, margin_true: np.ndarray, margin_pred: np.ndarray) -> dict:
    return {
        'logloss': float(log_loss(y_true, p, labels=[0, 1])),
        'brier': float(brier_score_loss(y_true, p)),
        'ece': expected_calibration_error(y_true, p),
        'mae_margin': float(mean_absolute_error(margin_true, margin_pred)),
    }
