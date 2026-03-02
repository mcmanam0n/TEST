import pandas as pd
from sklearn.linear_model import LogisticRegression


def train_win_model(X: pd.DataFrame, y: pd.Series, c: float = 1.0) -> LogisticRegression:
    model = LogisticRegression(C=c, solver='liblinear', max_iter=200)
    model.fit(X, y)
    return model
