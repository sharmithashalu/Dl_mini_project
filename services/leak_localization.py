"""
GASGUARD X - Module 5: Leakage Localization Service
Estimates the probable gas leakage zone (Zone A, B, C, or D) and coordinates
using multi-sensor spatial concentration weighting, sensor trust, and airflow vectors.
"""

import numpy as np

class LeakLocalizationService:
    def __init__(self):
        # Factory layout definition (SVG coordinate space: 600 wide x 450 high)
        self.zones = {
            "Zone A": {
                "name": "Zone A - Raw Gas Storage & Tank Farm",
                "center": (150, 120),
                "bounds": {"x_min": 20, "x_max": 280, "y_min": 20, "y_max": 220},
                "color": "#3b82f6"
            },
            "Zone B": {
                "name": "Zone B - Compressor Bay & Valve Manifold",
                "center": (450, 120),
                "bounds": {"x_min": 300, "x_max": 580, "y_min": 20, "y_max": 220},
                "color": "#ef4444"
            },
            "Zone C": {
                "name": "Zone C - Process Pipeline Corridor",
                "center": (180, 330),
                "bounds": {"x_min": 20, "x_max": 330, "y_min": 240, "y_max": 430},
                "color": "#f59e0b"
            },
            "Zone D": {
                "name": "Zone D - Venting Hub & High-Pressure Pumps",
                "center": (460, 330),
                "bounds": {"x_min": 350, "x_max": 580, "y_min": 240, "y_max": 430},
                "color": "#10b981"
            }
        }

        # Virtual sensor positions mapped across factory floor
        self.sensor_positions = {
            "S1": {"zone": "Zone A", "x": 150, "y": 120, "label": "S1 (Storage North)"},
            "S2": {"zone": "Zone B", "x": 450, "y": 120, "label": "S2 (Compressor Manifold)"},
            "S3": {"zone": "Zone B", "x": 510, "y": 190, "label": "S3 (Valve V-01 Seal)"},
            "S4": {"zone": "Zone C", "x": 180, "y": 330, "label": "S4 (Pipeline Central)"},
            "S5": {"zone": "Zone D", "x": 460, "y": 330, "label": "S5 (Pump Distribution)"}
        }

    def localize_leak(self, sensor_readings, sensor_trust_scores=None, airflow_direction="NE", airflow_speed=2.5):
        """
        sensor_readings: dict like {'S1': 110.0, 'S2': 420.0, 'S3': 380.0, 'S4': 105.0, 'S5': 115.0}
        sensor_trust_scores: dict like {'S1': 98.0, 'S2': 95.0, ...} to downweight faulty sensors.
        airflow_direction: e.g. 'N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'
        airflow_speed: in m/s
        """
        if sensor_trust_scores is None:
            sensor_trust_scores = {k: 100.0 for k in self.sensor_positions}

        # Baseline noise subtraction (under 120 is clean ambient baseline)
        weights = {}
        total_weight = 0.0

        for s_id, pos in self.sensor_positions.items():
            val = sensor_readings.get(s_id, 100.0)
            trust = sensor_trust_scores.get(s_id, 100.0) / 100.0
            
            # Net effective signal above baseline
            signal = max(0.0, val - 110.0)
            # Weight is scaled by trust and non-linear power to emphasize peak
            w = (signal ** 1.8) * trust
            weights[s_id] = w
            total_weight += w

        # If all readings are nominal baseline
        if total_weight < 15.0:
            return {
                "probable_zone": "None (Safe Baseline)",
                "zone_key": "NONE",
                "confidence": 98.0,
                "coordinates": {"x": 300, "y": 225},
                "zone_probabilities": {"Zone A": 5.0, "Zone B": 5.0, "Zone C": 5.0, "Zone D": 5.0},
                "airflow": {"direction": airflow_direction, "speed": airflow_speed},
                "disclaimer": "Zone-level localization for prototype; not exact pipe-crack localization."
            }

        # Airflow drift offset vectors (dispersion plume pushes downwind, so leak source is upwind)
        wind_offsets = {
            "N": (0, 15), "NE": (-12, 12), "E": (-15, 0), "SE": (-12, -12),
            "S": (0, -15), "SW": (12, -12), "W": (15, 0), "NW": (12, 12)
        }
        dx, dy = wind_offsets.get(airflow_direction.upper(), (-10, 10))
        drift_factor = min(30.0, airflow_speed * 4.0)

        # Weighted Centroid Calculation
        centroid_x = sum(self.sensor_positions[s]["x"] * w for s, w in weights.items()) / total_weight
        centroid_y = sum(self.sensor_positions[s]["y"] * w for s, w in weights.items()) / total_weight

        # Upwind compensation for plume source estimation
        source_x = centroid_x + (dx / 15.0) * drift_factor
        source_y = centroid_y + (dy / 15.0) * drift_factor

        # Clamp to plant boundaries
        source_x = max(30, min(570, source_x))
        source_y = max(30, min(420, source_y))

        # Calculate distances to each zone center
        zone_scores = {}
        for z_key, z_data in self.zones.items():
            zc_x, zc_y = z_data["center"]
            dist = np.sqrt((source_x - zc_x)**2 + (source_y - zc_y)**2)
            # Inverted distance score
            zone_scores[z_key] = 1.0 / (dist + 40.0)

        total_zone_score = sum(zone_scores.values())
        zone_probs = {z: round((score / total_zone_score) * 100.0, 1) for z, score in zone_scores.items()}

        best_zone = max(zone_probs.items(), key=lambda x: x[1])
        confidence = min(96.0, round(best_zone[1] * 1.08, 1))

        return {
            "probable_zone": best_zone[0],
            "zone_key": best_zone[0],
            "confidence": confidence,
            "coordinates": {"x": round(source_x, 1), "y": round(source_y, 1)},
            "zone_probabilities": zone_probs,
            "airflow": {"direction": airflow_direction, "speed": airflow_speed},
            "sensor_weights": {s: round(w, 1) for s, w in weights.items()},
            "disclaimer": "Zone-level localization for prototype; not exact pipe-crack localization."
        }
