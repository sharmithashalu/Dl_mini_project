"""
GASGUARD X - Module 2 & 12: Pre-Leak Risk Prediction & Explainable AI (XAI) Engine
Predicts industrial gas-leak risk (GREEN, YELLOW, ORANGE, RED) using multi-modal telemetry,
and extracts feature attribution explanations for high-risk conditions.
"""

import os
import joblib
import numpy as np

class RiskEngineService:
    def __init__(self, model_path="models/risk_model.pkl"):
        self.model_path = model_path
        self.model_payload = None
        self.load_model()

    def load_model(self):
        if os.path.exists(self.model_path):
            try:
                self.model_payload = joblib.load(self.model_path)
                print("RiskEngineService: ML Risk model loaded successfully.")
            except Exception as e:
                print(f"RiskEngineService: Error loading {self.model_path}: {e}")
                self.model_payload = None
        else:
            print("RiskEngineService: Model file not found. Rule-based fallback active.")

    def calculate_risk(self, gas_conc, pressure, temp, flow, vibration, equip_health, sensor_trust, primary_alarm_status="STANDBY"):
        """
        Calculates Risk Score (0-100), Risk Level (GREEN, YELLOW, ORANGE, RED),
        and generates XAI explanations.
        """
        gas_conc = float(gas_conc)
        pressure = float(pressure)
        temp = float(temp)
        flow = float(flow)
        vibration = float(vibration)
        equip_health = float(equip_health)
        sensor_trust = float(sensor_trust)

        raw_score = None
        is_ml = False

        if self.model_payload is not None:
            try:
                scaler = self.model_payload["scaler"]
                model = self.model_payload["model"]
                features = np.array([[gas_conc, pressure, temp, flow, vibration, equip_health, sensor_trust]])
                features_scaled = scaler.transform(features)
                raw_score = float(model.predict(features_scaled)[0])
                is_ml = True
            except Exception as e:
                print(f"RiskEngineService: Inference error ({e}), falling back to analytical engine.")

        if raw_score is None:
            # Analytical physics-informed fallback
            gas_factor = min(40.0, (gas_conc / 120.0) * 40.0)
            pressure_dev = max(0.0, abs(pressure - 5.2) / 4.0 * 20.0)
            vib_factor = max(0.0, (vibration - 1.5) / 5.0 * 20.0)
            equip_factor = max(0.0, (100.0 - equip_health) * 0.15)
            trust_factor = max(0.0, (100.0 - sensor_trust) * 0.05)
            raw_score = gas_factor + pressure_dev + vib_factor + equip_factor + trust_factor
            is_ml = False

        # Additional risk adjustment if primary alarm has failed during hazardous conditions
        if primary_alarm_status == "FAILED" and raw_score >= 50.0:
            raw_score = min(100.0, raw_score + 10.0)

        risk_score = round(max(0.0, min(100.0, raw_score)), 1)

        # Categorize risk level
        if risk_score < 35.0:
            risk_level = "GREEN"
            level_text = "SAFE"
            badge_class = "success"
        elif risk_score < 65.0:
            risk_level = "YELLOW"
            level_text = "WARNING"
            badge_class = "warning"
        elif risk_score < 85.0:
            risk_level = "ORANGE"
            level_text = "HIGH"
            badge_class = "orange"
        else:
            risk_level = "RED"
            level_text = "CRITICAL"
            badge_class = "danger"

        # Generate Explainable AI breakdown
        xai_explanations = self._generate_xai(
            gas_conc, pressure, temp, flow, vibration, equip_health, sensor_trust, primary_alarm_status, risk_score
        )

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "level_text": level_text,
            "badge_class": badge_class,
            "is_ml": is_ml,
            "xai": xai_explanations
        }

    def _generate_xai(self, gas_conc, pressure, temp, flow, vibration, equip_health, sensor_trust, primary_alarm_status, risk_score):
        """
        Creates Explainable AI cards and factor attribution percentages.
        Answers: 'WHY IS THIS RISK HIGH?'
        """
        factors = []
        attributions = {}

        # 1. Gas Concentration
        if gas_conc >= 50.0:
            pct = min(45, int((gas_conc / 200.0) * 45))
            attributions["Gas Concentration"] = pct
            factors.append({
                "factor": "Gas Concentration Surge",
                "severity": "CRITICAL" if gas_conc >= 100 else "HIGH",
                "value": f"{gas_conc:.1f} PPM",
                "normal_baseline": "< 25.0 PPM",
                "attribution_pct": pct,
                "reason": f"Gas concentration is {gas_conc:.1f} PPM, significantly exceeding standard OSHA safety limits."
            })
        elif gas_conc >= 20.0:
            pct = 15
            attributions["Gas Concentration"] = pct
            factors.append({
                "factor": "Elevated Trace Gas",
                "severity": "WARNING",
                "value": f"{gas_conc:.1f} PPM",
                "normal_baseline": "< 15.0 PPM",
                "attribution_pct": pct,
                "reason": "Trace gas presence detected above ambient baseline."
            })

        # 2. Pressure Anomaly
        if pressure > 7.0 or pressure < 3.5:
            pct = 22
            attributions["Pressure Deviation"] = pct
            factors.append({
                "factor": "Pressure Deviation",
                "severity": "CRITICAL" if pressure > 8.5 else "HIGH",
                "value": f"{pressure:.2f} bar",
                "normal_baseline": "4.8 - 5.6 bar",
                "attribution_pct": pct,
                "reason": f"System pressure at {pressure:.2f} bar deviates by {abs(pressure - 5.2):.2f} bar from setpoint, straining gaskets."
            })

        # 3. Vibration Level
        if vibration > 4.0:
            pct = 20
            attributions["Mechanical Vibration"] = pct
            factors.append({
                "factor": "High Mechanical Vibration",
                "severity": "CRITICAL" if vibration > 6.0 else "HIGH",
                "value": f"{vibration:.2f} mm/s",
                "normal_baseline": "1.0 - 2.5 mm/s",
                "attribution_pct": pct,
                "reason": f"Vibration amplitude at {vibration:.2f} mm/s indicates severe mechanical flutter or bearing wear."
            })

        # 4. Equipment Health
        if equip_health < 65.0:
            pct = 18
            attributions["Equipment Degradation"] = pct
            factors.append({
                "factor": "Equipment Degradation",
                "severity": "CRITICAL" if equip_health < 45 else "HIGH",
                "value": f"{equip_health:.1f}% Health",
                "normal_baseline": "> 85.0%",
                "attribution_pct": pct,
                "reason": f"Asset health deteriorated to {equip_health:.1f}%, raising probability of containment breach."
            })

        # 5. Primary Alarm Status
        if primary_alarm_status == "FAILED":
            pct = 15
            attributions["Alarm System Failure"] = pct
            factors.append({
                "factor": "Primary Siren Circuit Failure",
                "severity": "CRITICAL",
                "value": "FAILED / UNACKNOWLEDGED",
                "normal_baseline": "STANDBY / ACTIVE",
                "attribution_pct": pct,
                "reason": "Primary audible siren failed to sound or was not acknowledged, increasing human exposure hazard."
            })

        # 6. Sensor Trust / Anomaly
        if sensor_trust < 70.0:
            pct = 10
            attributions["Sensor Uncertainty"] = pct
            factors.append({
                "factor": "Sensor Signal Discrepancy",
                "severity": "WARNING",
                "value": f"{sensor_trust:.1f}% Trust",
                "normal_baseline": "> 90.0%",
                "attribution_pct": pct,
                "reason": f"Sensor trust score dropped to {sensor_trust:.1f}%; cross-sensor variance indicates potential drift."
            })

        # If risk is green/low, provide nominal operation card
        if not factors:
            attributions["Baseline Operations"] = 100
            factors.append({
                "factor": "Nominal Operating Envelope",
                "severity": "SAFE",
                "value": "All Telemetry Normal",
                "normal_baseline": "Within standard limits",
                "attribution_pct": 100,
                "reason": "Gas concentrations, pressures, vibrations, and equipment health metrics are within verified safe ranges."
            })

        return {
            "factors": factors,
            "attributions": attributions,
            "primary_driver": factors[0]["factor"] if factors else "Normal Operations",
            "recommended_action": self._get_recommended_action(risk_score, primary_alarm_status)
        }

    def _get_recommended_action(self, risk_score, alarm_status):
        if risk_score >= 85.0:
            if alarm_status == "FAILED":
                return "IMMEDIATE EVACUATION: Primary siren failed. Verify backup visual strobes and wearable alerts. Trip isolation valve."
            return "IMMEDIATE EVACUATION: Sound facility klaxon, seal emergency isolation valves, deploy hazardous spill crew."
        elif risk_score >= 65.0:
            return "DISPATCH SAFETY TEAM: Inspect indicated zone, prepare backup ventilation, notify area supervisor."
        elif risk_score >= 35.0:
            return "INCREASE MONITORING: Check valve seals, verify sensor calibration, maintain continuous observation."
        return "ROUTINE MONITORING: System operating under verified safety tolerances."
