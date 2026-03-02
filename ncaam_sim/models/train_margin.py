import pandas as pd
from sklearn.linear_model import Ridge


def train_margin_model(X: pd.DataFrame, y: pd.Series, alpha: float = 2.0) -> Ridge:
    model = Ridge(alpha=alpha)
    model.fit(X, y)
    return model
