"""
GASGUARD X - Module 6: Worker Exposure Risk Service
Calculates individual and aggregate worker exposure risks based on real-time spatial positioning,
zone threat levels, gas concentration, and wearable haptic dispatch statuses.
"""

import numpy as np

class WorkerRiskService:
    def __init__(self):
        # Baseline worker roster with initial factory positions
        self.worker_roster = {
            "W001": {
                "name": "John Vance",
                "role": "Senior Operator",
                "zone": "Zone B",
                "x": 420,
                "y": 140,
                "wearable_id": "BAND-901"
            },
            "W002": {
                "name": "Sarah Connor",
                "role": "Process Technician",
                "zone": "Zone B",
                "x": 480,
                "y": 160,
                "wearable_id": "BAND-902"
            },
            "W003": {
                "name": "David Miller",
                "role": "Safety Inspector",
                "zone": "Zone A",
                "x": 130,
                "y": 150,
                "wearable_id": "BAND-903"
            },
            "W004": {
                "name": "Elena Rostova",
                "role": "Mechanical Engineer",
                "zone": "Zone C",
                "x": 210,
                "y": 340,
                "wearable_id": "BAND-904"
            }
        }

    def evaluate_workers(self, leak_zone="Zone B", leak_coords=None, gas_conc=85.0, zone_risk_level="CRITICAL"):
        """
        Assesses each worker's exposure level (LOW, MEDIUM, HIGH, CRITICAL),
        estimated local PPM dosage, and triggers wearable haptic vibration.
        """
        if leak_coords is None:
            leak_coords = {"x": 450, "y": 120}

        evaluated_workers = []
        exposed_count = 0
        critical_count = 0

        for w_id, w_info in self.worker_roster.items():
            dist = np.sqrt((w_info["x"] - leak_coords["x"])**2 + (w_info["y"] - leak_coords["y"])**2)
            
            # Exposure calculation
            is_in_leak_zone = (w_info["zone"] == leak_zone)
            
            # Local concentration approximation using inverse distance decay
            decay = max(0.05, 1.0 - (dist / 400.0))
            local_ppm = round(gas_conc * decay, 1)

            # Categorize worker exposure risk
            if is_in_leak_zone or dist < 120.0:
                if zone_risk_level in ["CRITICAL", "RED"] or local_ppm > 50.0:
                    exposure_level = "CRITICAL"
                    badge_class = "danger"
                    action = "EVACUATE IMMEDIATELY via Corridor A Exit"
                    wearable_status = "PULSING HAPTIC + AUDIBLE CHIRP"
                    critical_count += 1
                    exposed_count += 1
                elif zone_risk_level in ["HIGH", "ORANGE"] or local_ppm > 25.0:
                    exposure_level = "HIGH"
                    badge_class = "orange"
                    action = "DON RESPIRATOR & RETREAT TO SAFE STAGING"
                    wearable_status = "RAPID VIBRATION"
                    exposed_count += 1
                else:
                    exposure_level = "MEDIUM"
                    badge_class = "warning"
                    action = "STANDBY - AVOID COMPRESSOR BAY"
                    wearable_status = "MODERATE VIBRATION"
            elif dist < 220.0 or zone_risk_level == "CRITICAL":
                exposure_level = "MEDIUM"
                badge_class = "warning"
                action = "PROCEED WITH CAUTION - MONITOR DOSIMETER"
                wearable_status = "INTERMITTENT PING"
            else:
                exposure_level = "LOW"
                badge_class = "success"
                action = "SAFE OPERATIONAL SECTOR"
                wearable_status = "NORMAL TELEMETRY"

            evaluated_workers.append({
                "worker_id": w_id,
                "name": w_info["name"],
                "role": w_info["role"],
                "zone": w_info["zone"],
                "x": w_info["x"],
                "y": w_info["y"],
                "wearable_id": w_info["wearable_id"],
                "exposure_risk": exposure_level,
                "badge_class": badge_class,
                "local_ppm": local_ppm,
                "distance_to_leak_m": round(dist * 0.15, 1),
                "action": action,
                "wearable_status": wearable_status
            })

        return {
            "workers": evaluated_workers,
            "total_workers": len(evaluated_workers),
            "workers_exposed": exposed_count,
            "workers_critical": critical_count,
            "zone_at_risk": leak_zone,
            "evacuation_active": critical_count > 0
        }
