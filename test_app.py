"""
GASGUARD X - Comprehensive Automated Verification Test Suite
Tests all pages, role views, ML inferences, Digital Twin scenarios, and REST endpoints.
"""

import unittest
from app import app
from services.state_manager import plant_state

class GasGuardIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        plant_state.reset_to_baseline()

    def test_pages_render(self):
        pages = [
            "/",
            "/?role=control_room",
            "/?role=safety_officer",
            "/?role=worker",
            "/?role=maintenance",
            "/e-nose",
            "/leak-map",
            "/workers",
            "/equipment",
            "/alerts",
            "/digital-twin",
            "/incidents",
            "/incidents/replay/INC-2026-001",
            "/reports",
            "/reports?incident_id=INC-2026-001"
        ]
        for page in pages:
            res = self.client.get(page)
            self.assertEqual(res.status_code, 200, f"Page {page} failed with status {res.status_code}")
            self.assertIn(b"GASGUARD", res.data)

    def test_telemetry_api(self):
        res = self.client.get("/api/telemetry")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("gas", data)
        self.assertIn("risk", data)
        self.assertIn("equipment", data)
        self.assertIn("sensors", data)
        self.assertIn("localization", data)
        self.assertIn("workers", data)
        self.assertIn("alerts", data)
        self.assertIn("resilience", data)

    def test_enose_predict_api(self):
        payload = {
            "sensor_s1": 450,
            "sensor_s2": 130,
            "sensor_s3": 110,
            "sensor_s4": 120,
            "sensor_s5": 300,
            "temperature": 25.0,
            "humidity": 50.0
        }
        res = self.client.post("/api/e-nose/predict", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["gas_type"], "Ammonia")
        self.assertGreater(data["confidence"], 70.0)
        self.assertGreater(data["concentration_ppm"], 20.0)

    def test_digital_twin_scenarios(self):
        scenarios = ["GAS_LEAK", "VALVE_FAILURE", "PRESSURE_SPIKE", "REDUCE_VENTILATION", "SENSOR_FAILURE", "PRIMARY_ALARM_FAILURE", "NORMAL"]
        for sc in scenarios:
            res = self.client.post("/api/digital-twin/scenario", json={"scenario": sc})
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertTrue(data["success"])

    def test_primary_alarm_failover(self):
        # Force failure
        res = self.client.post("/api/alarm/simulate-failure", json={"force": True})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["alert_status"]["primary_alarm"]["status"], "FAILED")
        self.assertEqual(data["alert_status"]["backup_alerts"]["overall_status"], "ACTIVATED")

        # Acknowledge
        res = self.client.post("/api/alarm/acknowledge")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["alert_status"]["primary_alarm"]["status"], "ACKNOWLEDGED")

    def test_emergency_demo_lifecycle(self):
        res = self.client.post("/api/demo/start")
        self.assertEqual(res.status_code, 200)
        state = res.get_json()["state"]
        self.assertEqual(state["demo"]["current_step"], 1)

        # Advance through all 16 steps
        for step in range(2, 17):
            res = self.client.post("/api/demo/step")
            self.assertEqual(res.status_code, 200)
            state = res.get_json()["state"]
            self.assertEqual(state["demo"]["current_step"], step)

        # Step 16 completes and logs incident
        self.assertFalse(state["demo"]["is_running"])

    def test_iot_endpoints(self):
        # Status
        res = self.client.get("/api/iot/status")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("primary_buzzer_relay", data)
        self.assertIn("backup_strobe_relay", data)

        # Ingestion
        res = self.client.post("/api/iot/telemetry", json={"S1": 150, "temperature": 27.5})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "SUCCESS")

if __name__ == "__main__":
    unittest.main()
