
from sklearn.ensemble import IsolationForest
import pandas as pd

def train_model(data: pd.DataFrame, contamination=0.05, random_state=42):
    model = IsolationForest(contamination=contamination, random_state=random_state)
    model.fit(data[["output_kwh"]])
    return model

def predict_anomalies(model, data: pd.DataFrame) -> pd.Series:
    return model.predict(data[["output_kwh"]]) == -1
