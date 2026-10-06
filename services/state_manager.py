"""
GASGUARD X - Central Plant State & Digital Twin Simulation Manager
Maintains live plant telemetry, handles Digital Twin / What-If scenarios,
runs the automated 16-step Emergency Demo Scenario, and coordinates all safety services.
"""

import time
import sqlite3
import numpy as np
from datetime import datetime
from services.gas_detection import GasDetectionService
from services.risk_engine import RiskEngineService
from services.equipment_health import EquipmentHealthService
from services.sensor_health import SensorHealthService
from services.leak_localization import LeakLocalizationService
from services.worker_risk import WorkerRiskService
from services.alert_manager import AlertManagerService
from services.resilience_score import ResilienceScoreService
from database.init_db import get_connection

class PlantStateManager:
    def __init__(self):
        # Service singletons
        self.gas_service = GasDetectionService()
        self.risk_service = RiskEngineService()
        self.equipment_service = EquipmentHealthService()
        self.sensor_service = SensorHealthService()
        self.localization_service = LeakLocalizationService()
        self.worker_service = WorkerRiskService()
        self.alert_service = AlertManagerService()
        self.resilience_service = ResilienceScoreService()

        # Baseline baseline state
        self.reset_to_baseline()

        # Emergency Demo runner state
        self.demo_running = False
        self.demo_step = 0
        self.demo_last_tick = 0
        self.demo_messages = [
            "1. Baseline Normal: All plant sensors and equipment operating safely.",
            "2. Valve V-01 Pressure Rise: Line pressure starts creeping upwards.",
            "3. Mechanical Stress: Compressor C-01 shaft vibration increases past 4.5 mm/s.",
            "4. Flow Perturbation: Flow drops through Valve V-01 (-25% reduction).",
            "5. Micro-leak Formed: E-Nose sensors S2 & S3 detect rising gas signatures.",
            "6. AI Risk Engine: Pre-leak risk climbs from GREEN to YELLOW (Warning).",
            "7. E-Nose ML Classification: Chemical signature identified as Ammonia (92% Conf).",
            "8. Dynamic Map Alert: Zone B tinted Orange/Red as concentration reaches 85 PPM.",
            "9. Worker Tracking: Technicians W001 & W002 flagged at CRITICAL exposure risk.",
            "10. Primary Siren Triggered: Audible alarm sounds in Zone B (15s Ack window).",
            "11. Primary Siren Failure: Alarm heartbeat drops / Breaker fails to acknowledge.",
            "12. Failure Detected: AI system detects primary alarm failure status.",
            "13. Multi-Layer Failover: Autonomous activation of Visual Strobe, SMS, Wearables & PA Voice.",
            "14. Safety Resilience Drop: Resilience score plunges from 88 to 44 (Weakest: Alarm).",
            "15. Incident Auto-Logged: INC-2026-EMG logged to SQLite database with full telemetry snapshot.",
            "16. Resolution & Replay: Automatic ventilation boost engaged; Incident replay ready."
        ]

    def reset_to_baseline(self):
        """Restores factory to safe nominal baseline state."""
        self.active_scenario = "NORMAL_BASELINE"
        self.sensor_inputs = {
            "S1": 115.0,
            "S2": 108.0,
            "S3": 95.0,
            "S4": 102.0,
            "S5": 120.0,
            "temperature": 24.5,
            "humidity": 48.0
        }
        self.equipment_telemetry = {
            "v01_pressure": 5.1,
            "v01_flow": 46.0,
            "v01_temp": 28.0,
            "v01_vibration": 1.2,
            "p02_pressure": 5.2,
            "p02_flow": 70.0,
            "p02_temp": 24.0,
            "p02_vibration": 1.1,
            "c01_pressure": 7.4,
            "c01_flow": 66.0,
            "c01_temp": 46.0,
            "c01_vibration": 2.1,
            "p04_pressure": 5.5,
            "p04_flow": 72.0,
            "p04_temp": 29.0,
            "p04_vibration": 1.4
        }
        self.sensor_fault_override = None
        self.alert_service.reset()
        self.demo_running = False
        self.demo_step = 0

    def get_full_state(self):
        """
        Executes end-to-end multi-layer pipeline and compiles complete plant state snapshot.
        """
        # Module 1: E-Nose Gas Detection
        gas_res = self.gas_service.predict(
            self.sensor_inputs["S1"],
            self.sensor_inputs["S2"],
            self.sensor_inputs["S3"],
            self.sensor_inputs["S4"],
            self.sensor_inputs["S5"],
            self.sensor_inputs["temperature"],
            self.sensor_inputs["humidity"]
        )

        # Module 3: Equipment Health
        equip_res = self.equipment_service.evaluate_fleet(self.equipment_telemetry)

        # Module 4: Sensor Trust & Anomaly
        sensor_res = self.sensor_service.evaluate_sensor_trust(
            self.sensor_inputs["S1"],
            self.sensor_inputs["S2"],
            self.sensor_inputs["S3"],
            self.sensor_inputs["S4"],
            self.sensor_inputs["S5"],
            fault_override=self.sensor_fault_override
        )

        # Module 8 & 9: Alert Status Check
        # Use tentative risk to check alarm
        alert_res = self.alert_service.get_alert_status()
        primary_alarm_status = alert_res["primary_alarm"]["status"]

        # Module 2 & 12: Risk Engine & XAI
        # Aggregate representative line pressure, temp, flow, vib from most critical asset
        worst_asset = equip_res["lowest_asset"]
        risk_res = self.risk_service.calculate_risk(
            gas_conc=gas_res["concentration_ppm"],
            pressure=worst_asset["pressure"],
            temp=worst_asset["temperature"],
            flow=worst_asset["flow"],
            vibration=worst_asset["vibration"],
            equip_health=equip_res["average_health"],
            sensor_trust=sensor_res["average_trust"],
            primary_alarm_status=primary_alarm_status
        )

        # Update alerts based on calculated risk
        alert_res = self.alert_service.update_alarm_state(risk_res["risk_level"])

        # Module 5: Leak Localization
        loc_res = self.localization_service.localize_leak(
            sensor_readings=self.sensor_inputs,
            sensor_trust_scores=sensor_res["trust_scores"],
            airflow_direction="NE",
            airflow_speed=2.5
        )

        # Module 6: Worker Exposure Risk
        worker_res = self.worker_service.evaluate_workers(
            leak_zone=loc_res["probable_zone"],
            leak_coords=loc_res["coordinates"],
            gas_conc=gas_res["concentration_ppm"],
            zone_risk_level=risk_res["risk_level"]
        )

        # Module 10: Safety Resilience Score
        resilience_res = self.resilience_service.calculate_score(
            sensor_trust_avg=sensor_res["average_trust"],
            primary_alarm_status=alert_res["primary_alarm"]["status"],
            backup_activated=alert_res["backup_alerts"]["is_activated"],
            equip_health_avg=equip_res["average_health"],
            workers_at_risk=worker_res["workers_exposed"]
        )

        # Combined State Payload
        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "scenario": self.active_scenario,
            "demo": {
                "is_running": self.demo_running,
                "current_step": self.demo_step,
                "total_steps": len(self.demo_messages),
                "message": self.demo_messages[self.demo_step - 1] if self.demo_step > 0 else "System ready.",
                "progress_pct": round((self.demo_step / len(self.demo_messages)) * 100, 1)
            },
            "gas": gas_res,
            "risk": risk_res,
            "equipment": equip_res,
            "sensors": {
                "raw_inputs": self.sensor_inputs,
                "health": sensor_res
            },
            "localization": loc_res,
            "workers": worker_res,
            "alerts": alert_res,
            "resilience": resilience_res,
            "disclaimer": "GASGUARD X Prototype: Industrial Decision-Support System (Simulated & Safe Data Only)"
        }

    def apply_digital_twin_scenario(self, scenario_type, params=None):
        """
        Applies preset or customized What-if scenarios from Module 11.
        """
        if params is None:
            params = {}

        self.active_scenario = scenario_type

        if scenario_type == "GAS_LEAK":
            gas_choice = params.get("gas", "Ammonia")
            intensity = float(params.get("intensity", 85.0))
            if gas_choice == "Ammonia":
                self.sensor_inputs["S1"] = 120.0 + intensity * 3.8
                self.sensor_inputs["S2"] = 110.0 + intensity * 0.4
                self.sensor_inputs["S3"] = 95.0 + intensity * 0.8
                self.sensor_inputs["S4"] = 105.0 + intensity * 0.5
                self.sensor_inputs["S5"] = 130.0 + intensity * 2.1
            elif gas_choice == "Methane":
                self.sensor_inputs["S1"] = 120.0 + intensity * 0.3
                self.sensor_inputs["S2"] = 110.0 + intensity * 3.5
                self.sensor_inputs["S3"] = 95.0 + intensity * 0.4
                self.sensor_inputs["S4"] = 105.0 + intensity * 2.6
                self.sensor_inputs["S5"] = 130.0 + intensity * 1.9
            elif gas_choice == "Carbon Monoxide":
                self.sensor_inputs["S1"] = 120.0 + intensity * 0.9
                self.sensor_inputs["S2"] = 110.0 + intensity * 0.2
                self.sensor_inputs["S3"] = 95.0 + intensity * 4.2
                self.sensor_inputs["S4"] = 105.0 + intensity * 0.3
                self.sensor_inputs["S5"] = 130.0 + intensity * 1.2
            else: # LPG
                self.sensor_inputs["S1"] = 120.0 + intensity * 0.4
                self.sensor_inputs["S2"] = 110.0 + intensity * 2.2
                self.sensor_inputs["S3"] = 95.0 + intensity * 0.3
                self.sensor_inputs["S4"] = 105.0 + intensity * 4.0
                self.sensor_inputs["S5"] = 130.0 + intensity * 3.1

        elif scenario_type == "VALVE_FAILURE":
            self.equipment_telemetry["v01_pressure"] = 8.8
            self.equipment_telemetry["v01_flow"] = 18.0
            self.equipment_telemetry["v01_vibration"] = 6.2
            self.equipment_telemetry["v01_temp"] = 58.0
            # Gas leakage follows valve seal failure
            self.sensor_inputs["S1"] = 420.0
            self.sensor_inputs["S2"] = 160.0
            self.sensor_inputs["S3"] = 150.0

        elif scenario_type == "PRESSURE_SPIKE":
            self.equipment_telemetry["v01_pressure"] = 9.4
            self.equipment_telemetry["c01_pressure"] = 10.8
            self.equipment_telemetry["c01_vibration"] = 5.4

        elif scenario_type == "REDUCE_VENTILATION":
            self.sensor_inputs["temperature"] = 38.5
            self.sensor_inputs["humidity"] = 72.0
            # Higher trapped concentrations
            for k in ["S1", "S2", "S3", "S4", "S5"]:
                self.sensor_inputs[k] *= 1.45

        elif scenario_type == "SENSOR_FAILURE":
            self.sensor_fault_override = "S3_DRIFT"
            self.sensor_inputs["S3"] = 42.0 # Stuck / diverging low

        elif scenario_type == "PRIMARY_ALARM_FAILURE":
            self.alert_service.simulate_failure(force=True)

        elif scenario_type == "NORMAL":
            self.reset_to_baseline()

        return self.get_full_state()

    def advance_demo_step(self):
        """
        Executes one step of the 16-step Emergency Demo Scenario.
        """
        if self.demo_step >= len(self.demo_messages):
            self.demo_running = False
            return self.get_full_state()

        self.demo_step += 1
        step = self.demo_step

        if step == 1:
            self.reset_to_baseline()
            self.demo_running = True
            self.demo_step = 1

        elif step == 2:
            # Pressure creeping up
            self.equipment_telemetry["v01_pressure"] = 6.5

        elif step == 3:
            # Vibration increases
            self.equipment_telemetry["c01_vibration"] = 4.8
            self.equipment_telemetry["v01_vibration"] = 3.8

        elif step == 4:
            # Flow reduction
            self.equipment_telemetry["v01_flow"] = 32.0

        elif step == 5:
            # Micro-leak trace gas
            self.sensor_inputs["S1"] = 210.0
            self.sensor_inputs["S2"] = 140.0
            self.sensor_inputs["S5"] = 190.0

        elif step == 6:
            # Risk increases to YELLOW
            self.equipment_telemetry["v01_pressure"] = 7.4
            self.sensor_inputs["S1"] = 290.0

        elif step == 7:
            # Full Ammonia signature
            self.sensor_inputs["S1"] = 445.0
            self.sensor_inputs["S2"] = 150.0
            self.sensor_inputs["S3"] = 140.0
            self.sensor_inputs["S4"] = 145.0
            self.sensor_inputs["S5"] = 310.0

        elif step == 8:
            # Zone B critical
            self.equipment_telemetry["v01_pressure"] = 8.6
            self.equipment_telemetry["v01_vibration"] = 6.4

        elif step == 9:
            # Workers exposed
            pass # calculated automatically in get_full_state()

        elif step == 10:
            # Primary alarm activates
            self.alert_service.primary_alarm_status = "ACTIVE"
            self.alert_service.alarm_trigger_time = datetime.now()

        elif step == 11:
            # Simulate primary alarm failure
            self.alert_service.simulate_failure(force=True)

        elif step == 12:
            # System detects alarm failure
            pass # AlertManager sets failed

        elif step == 13:
            # Backup alerts engage
            pass # auto activated in alert manager

        elif step == 14:
            # Resilience score drops
            pass # evaluated automatically

        elif step == 15:
            # Store incident in database
            self._log_demo_incident()

        elif step == 16:
            # Incident resolution & replay ready
            self.demo_running = False

        return self.get_full_state()

    def _log_demo_incident(self):
        """Persists the simulated emergency into the SQLite database."""
        conn = get_connection()
        cursor = conn.cursor()
        incident_id = f"INC-{datetime.now().strftime('%Y%m%d-%H%M')}"
        try:
            cursor.execute("""
            INSERT OR REPLACE INTO incidents (
                incident_id, timestamp, gas_type, concentration_ppm, zone,
                equipment, risk_level, risk_score, primary_alarm_status,
                backup_alert_status, workers_exposed, response_status, root_causes, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                incident_id,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Ammonia",
                88.5,
                "Zone B",
                "Valve V-01",
                "CRITICAL",
                88.0,
                "FAILED",
                "ACTIVATED",
                2,
                "RESOLVED",
                "Thermal fatigue on flange gasket; primary acoustic horn breaker tripped",
                "Simulated emergency run: Multi-layer backup successfully alerted W001 & W002."
            ))
            conn.commit()
            print(f"Logged incident {incident_id} to database.")
        except Exception as e:
            print(f"Error logging demo incident: {e}")
        finally:
            conn.close()

# Global plant state singleton
plant_state = PlantStateManager()
