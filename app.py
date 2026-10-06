"""
GASGUARD X – AI-Based Multi-Layer Industrial Gas Safety & Leakage Localization System
Main Flask Application Server
"""

import os
import json
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory
from database.init_db import init_database, get_connection
from services.state_manager import plant_state

app = Flask(__name__)
app.secret_key = "gasguard-x-industrial-safety-secret-key-2026"

# Ensure database is initialized on startup
init_database()

# -------------------------------------------------------------
# PAGE ROUTES
# -------------------------------------------------------------

@app.route("/")
def index():
    if request.args.get("view") == "legacy":
        role = request.args.get("role", "control_room").lower()
        valid_roles = ["control_room", "safety_officer", "worker", "maintenance"]
        if role not in valid_roles:
            role = "control_room"
        state = plant_state.get_full_state()
        return render_template("dashboard.html", state=state, active_role=role, active_page="dashboard")
    return send_from_directory(".", "index.html")

@app.route("/react")
def react_app():
    return send_from_directory(".", "index.html")

@app.route("/legacy")
def legacy_dashboard():
    role = request.args.get("role", "control_room").lower()
    valid_roles = ["control_room", "safety_officer", "worker", "maintenance"]
    if role not in valid_roles:
        role = "control_room"
    state = plant_state.get_full_state()
    return render_template("dashboard.html", state=state, active_role=role, active_page="dashboard")

@app.route("/e-nose")
def e_nose_view():
    state = plant_state.get_full_state()
    return render_template("e_nose.html", state=state, active_page="e_nose")

@app.route("/leak-map")
def leak_map_view():
    state = plant_state.get_full_state()
    return render_template("leak_map.html", state=state, active_page="leak_map")

@app.route("/workers")
def workers_view():
    state = plant_state.get_full_state()
    return render_template("workers.html", state=state, active_page="workers")

@app.route("/equipment")
def equipment_view():
    state = plant_state.get_full_state()
    return render_template("equipment.html", state=state, active_page="equipment")

@app.route("/alerts")
def alerts_view():
    state = plant_state.get_full_state()
    return render_template("alerts.html", state=state, active_page="alerts")

@app.route("/digital-twin")
def digital_twin_view():
    state = plant_state.get_full_state()
    return render_template("digital_twin.html", state=state, active_page="digital_twin")

@app.route("/incidents")
def incidents_view():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM incidents ORDER BY timestamp DESC")
    incidents = [dict(row) for row in cursor.fetchall()]
    conn.close()
    state = plant_state.get_full_state()
    return render_template("incidents.html", state=state, incidents=incidents, active_page="incidents")

@app.route("/incidents/replay/<incident_id>")
def incident_replay_view(incident_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM incidents WHERE incident_id = ?", (incident_id,))
    incident = cursor.fetchone()
    conn.close()
    if not incident:
        flash(f"Incident {incident_id} not found.", "warning")
        return redirect(url_for("incidents_view"))
    incident_dict = dict(incident)
    state = plant_state.get_full_state()
    return render_template("incident_replay.html", state=state, incident=incident_dict, active_page="incidents")

@app.route("/reports")
def reports_view():
    incident_id = request.args.get("incident_id")
    conn = get_connection()
    cursor = conn.cursor()
    
    if incident_id:
        cursor.execute("SELECT * FROM incidents WHERE incident_id = ?", (incident_id,))
        selected_incident = cursor.fetchone()
    else:
        cursor.execute("SELECT * FROM incidents ORDER BY timestamp DESC LIMIT 1")
        selected_incident = cursor.fetchone()

    cursor.execute("SELECT * FROM incidents ORDER BY timestamp DESC")
    all_incidents = [dict(row) for row in cursor.fetchall()]
    conn.close()

    incident_data = dict(selected_incident) if selected_incident else None
    state = plant_state.get_full_state()
    return render_template("reports.html", state=state, incident=incident_data, all_incidents=all_incidents, active_page="reports")

# -------------------------------------------------------------
# REST API ENDPOINTS
# -------------------------------------------------------------

@app.route("/api/telemetry", methods=["GET"])
def api_telemetry():
    """Returns current live multi-layer plant telemetry snapshot."""
    return jsonify(plant_state.get_full_state())

@app.route("/api/e-nose/predict", methods=["POST"])
def api_enose_predict():
    """Manual or simulated E-Nose classification endpoint."""
    data = request.get_json() or {}
    s1 = float(data.get("sensor_s1", 115.0))
    s2 = float(data.get("sensor_s2", 108.0))
    s3 = float(data.get("sensor_s3", 95.0))
    s4 = float(data.get("sensor_s4", 102.0))
    s5 = float(data.get("sensor_s5", 120.0))
    temp = float(data.get("temperature", 24.5))
    hum = float(data.get("humidity", 48.0))

    prediction = plant_state.gas_service.predict(s1, s2, s3, s4, s5, temp, hum)
    return jsonify(prediction)

@app.route("/api/digital-twin/scenario", methods=["POST"])
def api_digital_twin_scenario():
    """Triggers What-if Digital Twin scenarios."""
    data = request.get_json() or {}
    scenario = data.get("scenario", "NORMAL")
    params = data.get("params", {})
    updated_state = plant_state.apply_digital_twin_scenario(scenario, params)
    return jsonify({"success": True, "scenario": scenario, "state": updated_state})

@app.route("/api/alarm/acknowledge", methods=["POST"])
def api_alarm_ack():
    """Simulates operator acknowledgement of active siren."""
    alert_status = plant_state.alert_service.acknowledge_alarm()
    return jsonify({"success": True, "alert_status": alert_status})

@app.route("/api/alarm/simulate-failure", methods=["POST"])
def api_alarm_fail():
    """Forces primary alarm failure to demonstrate autonomous backup failover."""
    data = request.get_json() or {}
    force = data.get("force", True)
    alert_status = plant_state.alert_service.simulate_failure(force=force)
    return jsonify({"success": True, "alert_status": alert_status})

@app.route("/api/demo/start", methods=["POST"])
def api_demo_start():
    """Starts the 16-step Emergency Demo Scenario."""
    plant_state.reset_to_baseline()
    plant_state.demo_running = True
    plant_state.demo_step = 0
    state = plant_state.advance_demo_step()
    return jsonify({"success": True, "state": state})

@app.route("/api/demo/step", methods=["POST"])
def api_demo_step():
    """Steps to the next stage in the emergency demonstration."""
    state = plant_state.advance_demo_step()
    return jsonify({"success": True, "state": state})

@app.route("/api/demo/reset", methods=["POST"])
def api_demo_reset():
    """Resets the factory back to nominal baseline."""
    plant_state.reset_to_baseline()
    return jsonify({"success": True, "state": plant_state.get_full_state()})

@app.route("/api/iot/status", methods=["GET"])
def api_iot_status():
    """
    ESP32 / IoT Hardware Integration Endpoint.
    Returns machine-friendly GPIO relay commands for physical buzzers,
    visual beacon relays, and LoRa wearable transceivers.
    """
    state = plant_state.get_full_state()
    return jsonify({
        "device_target": "ESP32_GATEWAY_V1",
        "timestamp": state["timestamp"],
        "primary_buzzer_relay": 1 if state["alerts"]["primary_alarm"]["status"] == "ACTIVE" else 0,
        "backup_strobe_relay": 1 if state["alerts"]["backup_alerts"]["is_activated"] else 0,
        "backup_wearable_lora_trigger": 1 if state["alerts"]["backup_alerts"]["is_activated"] else 0,
        "risk_level": state["risk"]["risk_level"],
        "risk_score": state["risk"]["risk_score"],
        "leak_zone": state["localization"]["probable_zone"],
        "gas_type": state["gas"]["gas_type"],
        "concentration_ppm": state["gas"]["concentration_ppm"]
    })

@app.route("/api/iot/telemetry", methods=["POST"])
def api_iot_telemetry():
    """
    Accepts incoming physical sensor readings from ESP32 microcontrollers
    (e.g., MQ-2, MQ-135, DHT22 sensors).
    """
    data = request.get_json() or {}
    for key in ["S1", "S2", "S3", "S4", "S5"]:
        if key in data:
            plant_state.sensor_inputs[key] = float(data[key])
    if "temperature" in data:
        plant_state.sensor_inputs["temperature"] = float(data["temperature"])
    if "humidity" in data:
        plant_state.sensor_inputs["humidity"] = float(data["humidity"])

    return jsonify({"status": "SUCCESS", "message": "External IoT telemetry ingested", "state": plant_state.get_full_state()})

# -------------------------------------------------------------
# RUN APPLICATION
# -------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"GASGUARD X Server starting on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
