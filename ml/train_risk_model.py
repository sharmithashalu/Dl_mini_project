"""
GASGUARD X - Machine Learning Risk Prediction Engine
Trains a model (Random Forest / XGBoost) to predict overall industrial gas-leak risk
using multi-modal telemetry and saves model artifacts for real-time inference and XAI.
"""

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

try:
    from xgboost import XGBRegressor
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

def train_risk_model():
    os.makedirs("models", exist_ok=True)
    data_path = "data/sensor_data.csv"
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"{data_path} not found. Run generate_synthetic_data.py first.")

    df = pd.read_csv(data_path)
    feature_cols = [
        "gas_concentration",
        "pressure",
        "temperature",
        "flow",
        "vibration",
        "equipment_health",
        "sensor_trust"
    ]

    X = df[feature_cols].values
    y = df["risk_score"].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    print("Training Risk Prediction Model...")
    if HAS_XGB:
        print("Using XGBoost Regressor...")
        model = XGBRegressor(n_estimators=120, max_depth=6, learning_rate=0.08, random_state=42)
    else:
        print("Using Random Forest Regressor...")
        model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)

    model.fit(X_train_scaled, y_train)
    y_pred = model.predict(X_test_scaled)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)
    print(f"Risk Model RMSE: {rmse:.2f}, R2 Score: {r2:.4f}")

    # Feature importances
    importances = model.feature_importances_ if hasattr(model, "feature_importances_") else [1/len(feature_cols)] * len(feature_cols)

    model_payload = {
        "model": model,
        "scaler": scaler,
        "feature_names": feature_cols,
        "feature_importances": dict(zip(feature_cols, [float(x) for x in importances])),
        "rmse": float(rmse),
        "r2": float(r2),
        "model_type": "XGBoost" if HAS_XGB else "RandomForest"
    }

    joblib.dump(model_payload, "models/risk_model.pkl")
    print("Saved models/risk_model.pkl successfully.")
    return model_payload

if __name__ == "__main__":
    train_risk_model()
