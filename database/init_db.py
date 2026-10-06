"""
GASGUARD X - Database Initialization & Seed Script
Initializes SQLite database schemas for incidents, telemetry logs, worker tracking, and equipment assets.
"""

import os
import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "gasguard.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    cursor = conn.cursor()

    # Incidents Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS incidents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        incident_id TEXT UNIQUE NOT NULL,
        timestamp TEXT NOT NULL,
        gas_type TEXT NOT NULL,
        concentration_ppm REAL NOT NULL,
        zone TEXT NOT NULL,
        equipment TEXT NOT NULL,
        risk_level TEXT NOT NULL,
        risk_score REAL NOT NULL,
        primary_alarm_status TEXT NOT NULL,
        backup_alert_status TEXT NOT NULL,
        workers_exposed INTEGER NOT NULL,
        response_status TEXT NOT NULL,
        root_causes TEXT,
        notes TEXT
    )
    """)

    # Telemetry Logs Table (Real-time history for charts & compliance audits)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS telemetry_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        gas_type TEXT,
        concentration_ppm REAL,
        risk_score REAL,
        risk_level TEXT,
        zone TEXT,
        equipment_health REAL,
        sensor_trust REAL,
        resilience_score REAL
    )
    """)

    # Workers Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        worker_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        role TEXT NOT NULL,
        current_zone TEXT NOT NULL,
        exposure_risk TEXT NOT NULL,
        personal_ppm REAL DEFAULT 0.0,
        wearable_status TEXT DEFAULT 'CONNECTED'
    )
    """)

    # Equipment Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS equipment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipment_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        zone TEXT NOT NULL,
        pressure REAL NOT NULL,
        flow REAL NOT NULL,
        temperature REAL NOT NULL,
        vibration REAL NOT NULL,
        health_score REAL NOT NULL,
        status TEXT NOT NULL,
        fault_reason TEXT
    )
    """)

    conn.commit()

    # Seed initial data if tables are empty
    # 1. Seed Incidents
    cursor.execute("SELECT COUNT(*) FROM incidents")
    if cursor.fetchone()[0] == 0:
        seed_csv = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "incident_data.csv")
        if os.path.exists(seed_csv):
            df_incidents = pd.read_csv(seed_csv)
            for _, row in df_incidents.iterrows():
                cursor.execute("""
                INSERT OR IGNORE INTO incidents (
                    incident_id, timestamp, gas_type, concentration_ppm, zone,
                    equipment, risk_level, risk_score, primary_alarm_status,
                    backup_alert_status, workers_exposed, response_status, root_causes, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row["incident_id"], row["timestamp"], row["gas_type"],
                    row["concentration_ppm"], row["zone"], row["equipment"],
                    row["risk_level"], row["risk_score"], row["primary_alarm_status"],
                    row["backup_alert_status"], row["workers_exposed"],
                    row["response_status"], row["root_causes"], row["notes"]
                ))
            print("Seeded incidents from CSV.")

    # 2. Seed Workers
    cursor.execute("SELECT COUNT(*) FROM workers")
    if cursor.fetchone()[0] == 0:
        workers = [
            ("W001", "John Vance", "Senior Operator", "Zone B", "CRITICAL", 82.5, "ALERTED - VIBRATING"),
            ("W002", "Sarah Connor", "Process Technician", "Zone B", "CRITICAL", 74.0, "ALERTED - VIBRATING"),
            ("W003", "David Miller", "Safety Inspector", "Zone A", "LOW", 4.2, "STANDBY"),
            ("W004", "Elena Rostova", "Mechanical Engineer", "Zone C", "MEDIUM", 22.0, "MONITORING"),
        ]
        cursor.executemany("""
        INSERT OR IGNORE INTO workers (worker_id, name, role, current_zone, exposure_risk, personal_ppm, wearable_status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, workers)
        print("Seeded worker fleet.")

    # 3. Seed Equipment
    cursor.execute("SELECT COUNT(*) FROM equipment")
    if cursor.fetchone()[0] == 0:
        equipment_list = [
            ("V-01", "Isolation Control Valve V-01", "Valve", "Zone B", 7.8, 38.5, 52.0, 4.2, 64.0, "ATTENTION REQUIRED", "Pressure deviation & seal micro-flutter"),
            ("P-02", "Main Feed Pipeline P-02", "Pipeline", "Zone A", 5.1, 68.0, 24.5, 1.4, 92.0, "OPTIMAL", "Nominal operational envelope"),
            ("C-01", "Rotary Compressor C-01", "Compressor", "Zone C", 8.4, 62.0, 58.0, 5.6, 58.0, "ATTENTION REQUIRED", "Elevated shaft vibration (5.6 mm/s)"),
            ("P-04", "Heavy Hydrocarbon Pump P-04", "Pump", "Zone D", 5.4, 71.0, 28.0, 1.8, 88.0, "OPTIMAL", "Routine operation"),
        ]
        cursor.executemany("""
        INSERT OR IGNORE INTO equipment (equipment_id, name, type, zone, pressure, flow, temperature, vibration, health_score, status, fault_reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, equipment_list)
        print("Seeded industrial equipment assets.")

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

if __name__ == "__main__":
    init_database()
