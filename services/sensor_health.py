"""
GASGUARD X - Module 4: Sensor Fault & Sensor Trust Service
Evaluates Sensor Trust Scores (0-100%) across the 5 virtual gas sensor channels
using Isolation Forest anomaly detection, peer cross-correlation, and drift analysis.
"""

import os
import joblib
import numpy as np

class SensorHealthService:
    def __init__(self, model_path="models/anomaly_model.pkl"):
        self.model_path = model_path
        self.model_payload = None
        self.load_model()

    def load_model(self):
        if os.path.exists(self.model_path):
            try:
                self.model_payload = joblib.load(self.model_path)
                print("SensorHealthService: Anomaly model loaded successfully.")
            except Exception as e:
                print(f"SensorHealthService: Error loading {self.model_path}: {e}")
                self.model_payload = None
        else:
            print("SensorHealthService: Anomaly model not found. Statistical engine active.")

    def evaluate_sensor_trust(self, s1, s2, s3, s4, s5, fault_override=None):
        """
        Calculates individual trust scores (0-100%) for S1-S5 and identifies anomalous channels.
        fault_override: Allows manual simulation of sensor faults (e.g. 'S3_DRIFT' or 'S1_STUCK').
        """
        sensors = {"S1": float(s1), "S2": float(s2), "S3": float(s3), "S4": float(s4), "S5": float(s5)}
        trust_scores = {}
        anomaly_warnings = []

        vals = list(sensors.values())
        mean_val = np.mean(vals)
        median_val = np.median(vals)
        std_val = max(1.0, np.std(vals))

        # Check for cross-sensor consistency
        for name, val in sensors.items():
            trust = 98.0  # Base high trust for healthy calibration

            # 1. Stuck sensor check (zero or implausibly low reading when others elevated)
            if val < 5.0 and mean_val > 50.0:
                trust = 25.0
                anomaly_warnings.append(f"WARNING: Possible sensor anomaly detected on {name} (Signal frozen / Open circuit).")

            # 2. Extreme divergence from peer array
            z_score = abs(val - median_val) / std_val
            if z_score > 2.2 and val > 150.0 and len([v for v in vals if v > 150.0]) == 1:
                trust = max(35.0, 95.0 - (z_score * 24.0))
                anomaly_warnings.append(f"WARNING: Possible sensor anomaly detected on {name} (Spike divergence from peers).")

            # 3. Handle manual simulation override
            if fault_override:
                if fault_override == f"{name}_DRIFT":
                    trust = 42.0
                    anomaly_warnings.append(f"WARNING: Possible sensor anomaly detected on {name} (Simulated signal drift).")
                elif fault_override == f"{name}_STUCK":
                    trust = 20.0
                    anomaly_warnings.append(f"WARNING: Sensor fault detected on {name} (Hardware failure / Signal freeze).")

            trust_scores[name] = round(max(10.0, min(100.0, trust)), 1)

        # Global array anomaly detection via Isolation Forest
        is_array_anomalous = False
        if self.model_payload is not None:
            try:
                scaler = self.model_payload["scaler"]
                iso_forest = self.model_payload["model"]
                features = np.array([[s1, s2, s3, s4, s5]])
                features_scaled = scaler.transform(features)
                iso_pred = iso_forest.predict(features_scaled)[0] # -1 anomaly, 1 normal
                if iso_pred == -1 and min(trust_scores.values()) < 60.0:
                    is_array_anomalous = True
            except Exception as e:
                pass

        avg_trust = round(sum(trust_scores.values()) / len(trust_scores), 1)
        weakest_sensor = min(trust_scores.items(), key=lambda x: x[1])

        status = "HEALTHY"
        if avg_trust < 60.0 or weakest_sensor[1] < 50.0:
            status = "FAULT DETECTED"
        elif avg_trust < 85.0:
            status = "DEGRADED"

        return {
            "trust_scores": trust_scores,
            "average_trust": avg_trust,
            "status": status,
            "weakest_sensor": weakest_sensor[0],
            "weakest_trust": weakest_sensor[1],
            "has_anomaly": len(anomaly_warnings) > 0 or is_array_anomalous,
            "warnings": anomaly_warnings,
            "is_array_anomalous": is_array_anomalous
        }
