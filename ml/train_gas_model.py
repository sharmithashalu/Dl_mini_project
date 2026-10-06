"""
GASGUARD X - Machine Learning Gas Classifier
Trains an E-Nose classification model (Random Forest / XGBoost) to predict gas type
and an auxiliary regressor to estimate gas concentration (PPM).
"""

import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, classification_report, mean_squared_error

try:
    from xgboost import XGBClassifier, XGBRegressor
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

def train_gas_models():
    os.makedirs("models", exist_ok=True)
    data_path = "data/gas_signatures.csv"
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"{data_path} not found. Run generate_synthetic_data.py first.")

    df = pd.read_csv(data_path)
    feature_cols = ["sensor_s1", "sensor_s2", "sensor_s3", "sensor_s4", "sensor_s5", "temperature", "humidity"]
    
    X = df[feature_cols].values
    y_class = df["gas_type"].values
    y_conc = df["concentration_ppm"].values

    # Train test split
    X_train, X_test, y_class_train, y_class_test, y_conc_train, y_conc_test = train_test_split(
        X, y_class, y_conc, test_size=0.2, random_state=42, stratify=y_class
    )

    # Scaler
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Classification Model
    print("Training E-Nose Gas Classification Model...")
    clf = RandomForestClassifier(n_estimators=100, max_depth=12, random_state=42)
    clf.fit(X_train_scaled, y_class_train)

    y_pred_class = clf.predict(X_test_scaled)
    acc = accuracy_score(y_class_test, y_pred_class)
    print(f"E-Nose Classifier Accuracy: {acc * 100:.2f}%")
    print(classification_report(y_class_test, y_pred_class))

    # Concentration Regressor
    print("Training Gas Concentration Estimation Model...")
    reg = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42)
    reg.fit(X_train_scaled, y_conc_train)
    conc_pred = reg.predict(X_test_scaled)
    rmse = np.sqrt(mean_squared_error(y_conc_test, conc_pred))
    print(f"Concentration Regressor RMSE: {rmse:.2f} PPM")

    # Package model payload
    model_payload = {
        "classifier": clf,
        "regressor": reg,
        "scaler": scaler,
        "feature_names": feature_cols,
        "classes": list(clf.classes_),
        "accuracy": acc,
        "rmse": rmse,
        "feature_importances": dict(zip(feature_cols, clf.feature_importances_.tolist()))
    }

    joblib.dump(model_payload, "models/gas_classifier.pkl")
    print("Saved models/gas_classifier.pkl successfully.")
    return model_payload

if __name__ == "__main__":
    train_gas_models()
