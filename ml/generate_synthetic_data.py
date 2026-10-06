"""
GASGUARD X - Synthetic Data Generator
Generates realistic, physically-grounded synthetic datasets for:
1. E-Nose multi-channel sensor array signatures (MQ/electrochemical simulated responses)
2. Equipment telemetry & multi-parameter degradation time-series
3. Historical industrial incident logs
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Create target directories
os.makedirs("data", exist_ok=True)
os.makedirs("models", exist_ok=True)
os.makedirs("database", exist_ok=True)

np.random.seed(42)

def generate_gas_signatures(n_samples=2500):
    """
    Simulates cross-sensitive responses for a 5-sensor electronic nose array:
    - S1: High sensitivity to Ammonia (NH3), moderate to CO
    - S2: High sensitivity to Methane (CH4), moderate to LPG
    - S3: High sensitivity to Carbon Monoxide (CO), low to others
    - S4: High sensitivity to LPG (Propane/Butane), moderate to CH4
    - S5: Broad-band Hydrocarbon / VOC sensor
    Also models temperature and humidity interference effects.
    """
    gases = ["Normal Air", "Ammonia", "Methane", "Carbon Monoxide", "LPG"]
    samples_per_gas = n_samples // len(gases)
    records = []

    for gas in gases:
        for _ in range(samples_per_gas):
            temp = np.random.uniform(18.0, 38.0)
            hum = np.random.uniform(30.0, 80.0)
            
            # Baseline ambient noise (clean air)
            s1 = np.random.normal(120, 15)
            s2 = np.random.normal(110, 12)
            s3 = np.random.normal(95, 10)
            s4 = np.random.normal(105, 14)
            s5 = np.random.normal(130, 16)
            
            if gas == "Normal Air":
                conc = np.random.uniform(0.0, 5.0)
                status = "Normal"
            elif gas == "Ammonia":
                conc = np.random.uniform(15.0, 350.0)
                # S1 responds strongly, S5 moderately
                s1 += conc * 3.8 + np.random.normal(0, 10)
                s2 += conc * 0.4 + np.random.normal(0, 6)
                s3 += conc * 0.8 + np.random.normal(0, 8)
                s4 += conc * 0.5 + np.random.normal(0, 7)
                s5 += conc * 2.1 + np.random.normal(0, 9)
            elif gas == "Methane":
                conc = np.random.uniform(50.0, 600.0)
                # S2 and S4 respond strongly
                s1 += conc * 0.3 + np.random.normal(0, 6)
                s2 += conc * 3.5 + np.random.normal(0, 12)
                s3 += conc * 0.4 + np.random.normal(0, 5)
                s4 += conc * 2.6 + np.random.normal(0, 10)
                s5 += conc * 1.9 + np.random.normal(0, 9)
            elif gas == "Carbon Monoxide":
                conc = np.random.uniform(10.0, 280.0)
                # S3 responds strongly, S1 slightly
                s1 += conc * 0.9 + np.random.normal(0, 7)
                s2 += conc * 0.2 + np.random.normal(0, 5)
                s3 += conc * 4.2 + np.random.normal(0, 11)
                s4 += conc * 0.3 + np.random.normal(0, 6)
                s5 += conc * 1.2 + np.random.normal(0, 8)
            elif gas == "LPG":
                conc = np.random.uniform(30.0, 500.0)
                # S4 and S5 respond strongly, S2 moderately
                s1 += conc * 0.4 + np.random.normal(0, 6)
                s2 += conc * 2.2 + np.random.normal(0, 9)
                s3 += conc * 0.3 + np.random.normal(0, 5)
                s4 += conc * 4.0 + np.random.normal(0, 13)
                s5 += conc * 3.1 + np.random.normal(0, 11)

            # Humidity and temperature mild drift (characteristic of physical chemoresistive sensors)
            temp_factor = 1.0 + (temp - 25.0) * 0.004
            hum_factor = 1.0 - (hum - 50.0) * 0.002
            
            s1 = max(50.0, s1 * temp_factor * hum_factor)
            s2 = max(50.0, s2 * temp_factor * hum_factor)
            s3 = max(50.0, s3 * temp_factor * hum_factor)
            s4 = max(50.0, s4 * temp_factor * hum_factor)
            s5 = max(50.0, s5 * temp_factor * hum_factor)
            
            if gas == "Normal Air":
                status = "Normal"
            elif conc < 40:
                status = "Elevated"
            elif conc < 120:
                status = "Warning"
            else:
                status = "Critical"

            records.append({
                "sensor_s1": round(s1, 2),
                "sensor_s2": round(s2, 2),
                "sensor_s3": round(s3, 2),
                "sensor_s4": round(s4, 2),
                "sensor_s5": round(s5, 2),
                "temperature": round(temp, 1),
                "humidity": round(hum, 1),
                "gas_type": gas,
                "concentration_ppm": round(conc, 1),
                "status": status
            })

    df = pd.DataFrame(records)
    df = df.sample(frac=1.0, random_state=42).reset_index(drop=True)
    df.to_csv("data/gas_signatures.csv", index=False)
    print(f"Generated data/gas_signatures.csv with {len(df)} samples.")
    return df


def generate_equipment_sensor_data(n_samples=1800):
    """
    Generates multi-parameter telemetry for pre-leak risk prediction:
    - Gas concentration
    - Pressure (normal 4.0 - 6.5 bar)
    - Temperature (normal 20 - 45 C)
    - Flow rate (normal 45 - 85 m3/h)
    - Vibration (normal 1.0 - 2.8 mm/s)
    - Equipment health (0 - 100)
    - Sensor trust (0 - 100)
    - Target: Risk Score (0 - 100) and Risk Level (GREEN, YELLOW, ORANGE, RED)
    """
    records = []
    base_time = datetime.now() - timedelta(days=5)

    for i in range(n_samples):
        timestamp = base_time + timedelta(minutes=i * 4)
        scenario = np.random.choice(["normal", "mild_anomaly", "leak_developing", "critical_leak"], 
                                    p=[0.55, 0.20, 0.15, 0.10])
        
        if scenario == "normal":
            gas_ppm = np.random.uniform(0.5, 15.0)
            pressure = np.random.uniform(4.8, 5.6)
            temp = np.random.uniform(22.0, 32.0)
            flow = np.random.uniform(55.0, 75.0)
            vibration = np.random.uniform(1.1, 2.3)
            equip_health = np.random.uniform(85.0, 99.0)
            sensor_trust = np.random.uniform(92.0, 100.0)
            risk_score = np.random.uniform(5.0, 30.0)
        elif scenario == "mild_anomaly":
            gas_ppm = np.random.uniform(18.0, 45.0)
            pressure = np.random.uniform(5.8, 6.7)
            temp = np.random.uniform(32.0, 48.0)
            flow = np.random.uniform(40.0, 54.0)
            vibration = np.random.uniform(2.5, 3.8)
            equip_health = np.random.uniform(65.0, 84.0)
            sensor_trust = np.random.uniform(80.0, 95.0)
            risk_score = np.random.uniform(35.0, 64.0)
        elif scenario == "leak_developing":
            gas_ppm = np.random.uniform(50.0, 110.0)
            pressure = np.random.uniform(6.8, 8.2)
            temp = np.random.uniform(45.0, 65.0)
            flow = np.random.uniform(30.0, 45.0)
            vibration = np.random.uniform(3.9, 5.8)
            equip_health = np.random.uniform(45.0, 64.0)
            sensor_trust = np.random.uniform(70.0, 90.0)
            risk_score = np.random.uniform(65.0, 84.0)
        else: # critical_leak
            gas_ppm = np.random.uniform(115.0, 380.0)
            pressure = np.random.uniform(8.3, 11.5)
            temp = np.random.uniform(60.0, 88.0)
            flow = np.random.uniform(15.0, 35.0)
            vibration = np.random.uniform(5.9, 9.5)
            equip_health = np.random.uniform(18.0, 44.0)
            sensor_trust = np.random.uniform(50.0, 88.0)
            risk_score = np.random.uniform(85.0, 99.0)

        # Risk level categorization
        if risk_score < 35:
            risk_level = "GREEN"
        elif risk_score < 65:
            risk_level = "YELLOW"
        elif risk_score < 85:
            risk_level = "ORANGE"
        else:
            risk_level = "RED"

        records.append({
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "gas_concentration": round(gas_ppm, 1),
            "pressure": round(pressure, 2),
            "temperature": round(temp, 1),
            "flow": round(flow, 1),
            "vibration": round(vibration, 2),
            "equipment_health": round(equip_health, 1),
            "sensor_trust": round(sensor_trust, 1),
            "risk_score": round(risk_score, 1),
            "risk_level": risk_level
        })

    df = pd.DataFrame(records)
    df.to_csv("data/sensor_data.csv", index=False)
    print(f"Generated data/sensor_data.csv with {len(df)} samples.")
    return df


def generate_seed_incidents():
    """
    Generates realistic historical incident logs for audit and replay.
    """
    incidents = [
        {
            "incident_id": "INC-2026-001",
            "timestamp": (datetime.now() - timedelta(days=14, hours=4)).strftime("%Y-%m-%d %H:%M:%S"),
            "gas_type": "Ammonia",
            "concentration_ppm": 85.4,
            "zone": "Zone B",
            "equipment": "Valve V-01",
            "risk_level": "CRITICAL",
            "risk_score": 88,
            "primary_alarm_status": "FAILED",
            "backup_alert_status": "ACTIVATED",
            "workers_exposed": 2,
            "response_status": "RESOLVED",
            "root_causes": "Seal degradation under high thermal stress; primary siren breaker tripped",
            "notes": "Backup mobile and visual beacons successfully evacuated technicians W001 and W002 in 42 seconds."
        },
        {
            "incident_id": "INC-2026-002",
            "timestamp": (datetime.now() - timedelta(days=9, hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
            "gas_type": "Methane",
            "concentration_ppm": 145.0,
            "zone": "Zone C",
            "equipment": "Compressor C-01",
            "risk_level": "HIGH",
            "risk_score": 76,
            "primary_alarm_status": "ACKNOWLEDGED",
            "backup_alert_status": "STANDBY",
            "workers_exposed": 1,
            "response_status": "RESOLVED",
            "root_causes": "Impeller imbalance causing 6.2 mm/s vibration and flange pinhole leakage",
            "notes": "Operator acknowledged siren promptly. Automated isolation valve tripped in Zone C."
        },
        {
            "incident_id": "INC-2026-003",
            "timestamp": (datetime.now() - timedelta(days=4, hours=8)).strftime("%Y-%m-%d %H:%M:%S"),
            "gas_type": "Carbon Monoxide",
            "concentration_ppm": 68.2,
            "zone": "Zone A",
            "equipment": "Pipeline P-02",
            "risk_level": "WARNING",
            "risk_score": 58,
            "primary_alarm_status": "ACKNOWLEDGED",
            "backup_alert_status": "STANDBY",
            "workers_exposed": 0,
            "response_status": "RESOLVED",
            "root_causes": "Flue gas exhaust backdraft under low ventilation fan velocity",
            "notes": "Emergency booster exhaust automatically engaged. Zero personnel exposed."
        },
        {
            "incident_id": "INC-2026-004",
            "timestamp": (datetime.now() - timedelta(days=1, hours=6)).strftime("%Y-%m-%d %H:%M:%S"),
            "gas_type": "LPG",
            "concentration_ppm": 95.0,
            "zone": "Zone D",
            "equipment": "Pump P-04",
            "risk_level": "HIGH",
            "risk_score": 81,
            "primary_alarm_status": "FAILED",
            "backup_alert_status": "ACTIVATED",
            "workers_exposed": 3,
            "response_status": "RESOLVED",
            "root_causes": "Mechanical seal dry running and cable conduit severing primary horn power",
            "notes": "Multi-layer backup system triggered synthetic voice broadcasts and wearable haptics to workers."
        }
    ]
    df = pd.DataFrame(incidents)
    df.to_csv("data/incident_data.csv", index=False)
    print(f"Generated data/incident_data.csv with {len(df)} samples.")
    return df

if __name__ == "__main__":
    generate_gas_signatures()
    generate_equipment_sensor_data()
    generate_seed_incidents()
    print("All synthetic datasets generated successfully.")
