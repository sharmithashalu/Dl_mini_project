"""
GASGUARD X - Sensor Fault & Anomaly Detection Model
Trains an Isolation Forest anomaly detector on normal sensor array data,
and provides evaluation functions for calculating Sensor Trust Scores (0-100%).
"""

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

def train_anomaly_model():
    os.makedirs("models", exist_ok=True)
    data_path = "data/gas_signatures.csv"
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"{data_path} not found.")

    df = pd.read_csv(data_path)
    # Filter for normal conditions to establish baseline distribution
    normal_df = df[df["gas_type"] == "Normal Air"]
    feature_cols = ["sensor_s1", "sensor_s2", "sensor_s3", "sensor_s4", "sensor_s5"]

    X_normal = normal_df[feature_cols].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_normal)

    print("Fitting Isolation Forest for Sensor Anomaly Detection...")
    iso_forest = IsolationForest(
        n_estimators=100,
        contamination=0.03,
        random_state=42
    )
    iso_forest.fit(X_scaled)

    # Establish baseline means and standard deviations for z-score checking
    baselines = {
        col: {
            "mean": float(normal_df[col].mean()),
            "std": float(normal_df[col].std())
        }
        for col in feature_cols
    }

    model_payload = {
        "model": iso_forest,
        "scaler": scaler,
        "feature_names": feature_cols,
        "baselines": baselines
    }

    joblib.dump(model_payload, "models/anomaly_model.pkl")
    print("Saved models/anomaly_model.pkl successfully.")
    return model_payload

if __name__ == "__main__":
    train_anomaly_model()
