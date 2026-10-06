"""
GASGUARD X - Module 3: Equipment Health Monitoring Service
Monitors simulated industrial assets (Valve, Pipeline, Compressor, Pump)
using Pressure, Flow, Temperature, and Vibration telemetry to compute health scores (0-100)
and identify degradation root causes.
"""

class EquipmentHealthService:
    def __init__(self):
        # Baseline ideal parameters for industrial assets
        self.asset_baselines = {
            "V-01": {"type": "Valve", "zone": "Zone B", "nominal_p": 5.0, "nominal_f": 45.0, "nominal_t": 28.0, "nominal_v": 1.2},
            "P-02": {"type": "Pipeline", "zone": "Zone A", "nominal_p": 5.2, "nominal_f": 70.0, "nominal_t": 24.0, "nominal_v": 1.1},
            "C-01": {"type": "Compressor", "zone": "Zone C", "nominal_p": 7.5, "nominal_f": 65.0, "nominal_t": 48.0, "nominal_v": 2.2},
            "P-04": {"type": "Pump", "zone": "Zone D", "nominal_p": 5.5, "nominal_f": 72.0, "nominal_t": 30.0, "nominal_v": 1.5}
        }

    def evaluate_asset(self, asset_id, p, f, t, v):
        """
        Evaluates health score (0-100) and specific faults for a single asset.
        """
        baseline = self.asset_baselines.get(asset_id, self.asset_baselines["V-01"])
        
        # Penalties calculation
        p_diff = abs(p - baseline["nominal_p"])
        f_diff = abs(f - baseline["nominal_f"])
        t_diff = max(0.0, t - baseline["nominal_t"])
        v_diff = max(0.0, v - baseline["nominal_v"])

        # Health score calculation
        health = 100.0 - (p_diff * 6.5) - (f_diff * 0.45) - (t_diff * 0.5) - (v_diff * 9.5)
        health = round(max(5.0, min(100.0, health)), 1)

        # Fault reasons identification
        reasons = []
        if v > 4.5:
            reasons.append(f"Increasing vibration ({v:.1f} mm/s exceeds ISO limit)")
        elif v > 3.0:
            reasons.append("Minor vibration flutter detected")

        if p > (baseline["nominal_p"] + 2.0):
            reasons.append(f"Pressure deviation (+{p_diff:.1f} bar over setpoint)")
        elif p < (baseline["nominal_p"] - 1.8):
            reasons.append(f"Pressure drop (-{p_diff:.1f} bar loss)")

        if f < (baseline["nominal_f"] * 0.65):
            reasons.append("Irregular flow reduction (possible obstruction/leak)")

        if t > (baseline["nominal_t"] + 25.0):
            reasons.append("Thermal stress / overheating")

        if not reasons:
            reasons.append("Nominal operational tolerances")

        # Status categorization
        if health >= 80.0:
            status = "OPTIMAL"
            status_class = "success"
        elif health >= 55.0:
            status = "ATTENTION REQUIRED"
            status_class = "warning"
        else:
            status = "CRITICAL DEGRADATION"
            status_class = "danger"

        return {
            "asset_id": asset_id,
            "type": baseline["type"],
            "zone": baseline["zone"],
            "pressure": round(p, 2),
            "flow": round(f, 1),
            "temperature": round(t, 1),
            "vibration": round(v, 2),
            "health_score": health,
            "status": status,
            "status_class": status_class,
            "fault_reason": "; ".join(reasons),
            "reasons_list": reasons,
            "disclaimer": "Simulated degradation model; not a physical structural warranty."
        }

    def evaluate_fleet(self, telemetry_dict=None):
        """
        Evaluates all monitored industrial assets and returns fleet status + overall equipment health.
        """
        if telemetry_dict is None:
            telemetry_dict = {}

        fleet = []
        # Defaults with active telemetry overrides
        fleet.append(self.evaluate_asset(
            "V-01",
            telemetry_dict.get("v01_pressure", 7.6),
            telemetry_dict.get("v01_flow", 36.0),
            telemetry_dict.get("v01_temp", 48.0),
            telemetry_dict.get("v01_vibration", 4.4)
        ))
        fleet.append(self.evaluate_asset(
            "P-02",
            telemetry_dict.get("p02_pressure", 5.2),
            telemetry_dict.get("p02_flow", 69.0),
            telemetry_dict.get("p02_temp", 25.0),
            telemetry_dict.get("p02_vibration", 1.2)
        ))
        fleet.append(self.evaluate_asset(
            "C-01",
            telemetry_dict.get("c01_pressure", 8.2),
            telemetry_dict.get("c01_flow", 60.0),
            telemetry_dict.get("c01_temp", 54.0),
            telemetry_dict.get("c01_vibration", 5.8)
        ))
        fleet.append(self.evaluate_asset(
            "P-04",
            telemetry_dict.get("p04_pressure", 5.4),
            telemetry_dict.get("p04_flow", 71.0),
            telemetry_dict.get("p04_temp", 31.0),
            telemetry_dict.get("p04_vibration", 1.6)
        ))

        avg_health = round(sum(a["health_score"] for a in fleet) / len(fleet), 1)

        lowest_asset = min(fleet, key=lambda a: a["health_score"])

        return {
            "assets": fleet,
            "average_health": avg_health,
            "lowest_asset": lowest_asset,
            "total_assets": len(fleet),
            "critical_count": sum(1 for a in fleet if a["status"] == "CRITICAL DEGRADATION"),
            "attention_count": sum(1 for a in fleet if a["status"] == "ATTENTION REQUIRED")
        }
