"""
GASGUARD X - Module 10: Safety Resilience Score Service
Calculates overall plant Safety Resilience Score (0-100) and layer breakdown,
identifying the single weakest safety layer to guide preventive maintenance.
"""

class ResilienceScoreService:
    def __init__(self):
        # Layer weighting factors (sum = 1.00)
        self.weights = {
            "sensor_reliability": 0.20,
            "alarm_reliability": 0.25,
            "backup_alert_readiness": 0.20,
            "equipment_health": 0.20,
            "emergency_comm_coverage": 0.15
        }

    def calculate_score(self, sensor_trust_avg, primary_alarm_status, backup_activated, equip_health_avg, workers_at_risk):
        """
        Computes composite resilience score and layer breakdown.
        """
        # 1. Sensor Reliability (0-100)
        sensor_rel = round(max(10.0, min(100.0, float(sensor_trust_avg))), 1)

        # 2. Alarm Reliability (0-100)
        if primary_alarm_status == "ACKNOWLEDGED":
            alarm_rel = 95.0
        elif primary_alarm_status == "STANDBY":
            alarm_rel = 90.0
        elif primary_alarm_status == "ACTIVE":
            alarm_rel = 75.0
        else: # FAILED
            alarm_rel = 25.0 # Severe penalty for failed primary siren

        # 3. Backup Alert Readiness (0-100)
        # If backup has successfully activated during a primary failure, resilience is partially buffered
        if primary_alarm_status == "FAILED":
            backup_readiness = 100.0 if backup_activated else 30.0
        else:
            backup_readiness = 98.0 # In ready standby

        # 4. Equipment Health (0-100)
        equip_rel = round(max(10.0, min(100.0, float(equip_health_avg))), 1)

        # 5. Emergency Communication & Worker Coverage (0-100)
        # Drops if workers are trapped in high risk zones
        comm_coverage = 95.0 - (workers_at_risk * 10.0)
        comm_coverage = round(max(30.0, min(100.0, comm_coverage)), 1)

        # Composite weighted score
        composite = (
            (sensor_rel * self.weights["sensor_reliability"]) +
            (alarm_rel * self.weights["alarm_reliability"]) +
            (backup_readiness * self.weights["backup_alert_readiness"]) +
            (equip_rel * self.weights["equipment_health"]) +
            (comm_coverage * self.weights["emergency_comm_coverage"])
        )
        resilience_score = round(max(0.0, min(100.0, composite)), 1)

        # Breakdown dictionary
        breakdown = {
            "Sensor Reliability": {
                "score": sensor_rel,
                "weight": "20%",
                "status": "Good" if sensor_rel >= 80 else ("Moderate" if sensor_rel >= 60 else "Poor"),
                "description": f"Array signal consistency across 5 channels ({sensor_rel}%)"
            },
            "Alarm Reliability": {
                "score": alarm_rel,
                "weight": "25%",
                "status": "Good" if alarm_rel >= 80 else ("Moderate" if alarm_rel >= 60 else "Critical"),
                "description": f"Primary acoustic siren heartbeat ({alarm_rel}%)"
            },
            "Backup Alert Readiness": {
                "score": backup_readiness,
                "weight": "20%",
                "status": "Active / Ready" if backup_readiness >= 80 else "Degraded",
                "description": f"Autonomous multi-layer failover grid ({backup_readiness}%)"
            },
            "Equipment Health": {
                "score": equip_rel,
                "weight": "20%",
                "status": "Good" if equip_rel >= 80 else ("Attention" if equip_rel >= 55 else "Critical"),
                "description": f"Valves, pipelines, compressors & pumps index ({equip_rel}%)"
            },
            "Emergency Communication": {
                "score": comm_coverage,
                "weight": "15%",
                "status": "Good" if comm_coverage >= 80 else "Compromised",
                "description": f"Worker wearable LoRa link & staging coverage ({comm_coverage}%)"
            }
        }

        # Find the single weakest safety layer
        weakest_layer_name, weakest_layer_data = min(breakdown.items(), key=lambda item: item[1]["score"])

        # Determine resilience tier badge
        if resilience_score >= 80.0:
            tier = "ROBUST"
            badge_class = "success"
        elif resilience_score >= 60.0:
            tier = "MODERATE"
            badge_class = "warning"
        elif resilience_score >= 40.0:
            tier = "VULNERABLE"
            badge_class = "orange"
        else:
            tier = "CRITICALLY COMPROMISED"
            badge_class = "danger"

        return {
            "resilience_score": resilience_score,
            "tier": tier,
            "badge_class": badge_class,
            "breakdown": breakdown,
            "weakest_layer": {
                "layer_name": weakest_layer_name,
                "score": weakest_layer_data["score"],
                "recommendation": self._get_layer_recommendation(weakest_layer_name, weakest_layer_data["score"])
            }
        }

    def _get_layer_recommendation(self, layer_name, score):
        if layer_name == "Alarm Reliability":
            return "Primary audible siren failed or unacknowledged. Replace siren driver circuit and verify SCADA buzzer relays."
        elif layer_name == "Sensor Reliability":
            return "Sensor calibration drift detected. Clean sensor manifold and perform zero-gas span recalibration."
        elif layer_name == "Equipment Health":
            return "Mechanical degradation detected in assets. Inspect Valve V-01 and Compressor C-01 vibration bearings."
        elif layer_name == "Emergency Communication":
            return "Evacuate personnel immediately from hazardous perimeter and verify wearable band signal link."
        elif layer_name == "Backup Alert Readiness":
            return "Verify auxiliary beacon strobe power supply and GSM cellular dispatch gateway."
        return "Conduct routine multi-barrier safety audit."
