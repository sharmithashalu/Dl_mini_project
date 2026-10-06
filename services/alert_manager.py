"""
GASGUARD X - Module 8 & 9: Primary Alarm Failure Detection & Multi-Layer Backup Alert Service
Detects primary audible siren failure / acknowledgement timeouts,
and automatically coordinates 5 redundant multi-layer backup channels.
Provides IoT / ESP32 integration payload.
"""

from datetime import datetime

class AlertManagerService:
    def __init__(self):
        self.primary_alarm_status = "STANDBY" # STANDBY, ACTIVE, ACKNOWLEDGED, FAILED
        self.alarm_trigger_time = None
        self.ack_timeout_seconds = 15 # 15-second simulation window
        self.simulated_failure_forced = False

        # Multi-layer backup systems status
        self.backup_systems = {
            "visual_beacon": {
                "name": "High-Intensity Visual Strobe & Beacons",
                "type": "Visual",
                "status": "STANDBY", # STANDBY / ACTIVE
                "details": "Pulsing red/amber xenon strobe grid across Zone B & evacuation pathways"
            },
            "mobile_notification": {
                "name": "Emergency Mobile Push & SMS Dispatch",
                "type": "Cellular",
                "status": "STANDBY",
                "details": "Automated SMS & urgent push dispatched to Plant Safety Manager & Shift Supervisors"
            },
            "control_room_alert": {
                "name": "Control Room Master Klaxon & HUD Lockdown",
                "type": "SCADA",
                "status": "STANDBY",
                "details": "Flashing priority override modal, audio klaxon chime, and automatic SCADA isolation"
            },
            "worker_wearable": {
                "name": "Worker Wearable Haptic Evacuation Wristbands",
                "type": "IoT BLE/LoRa",
                "status": "STANDBY",
                "details": "Dual-frequency vibration pulses dispatched to W001, W002 band receivers"
            },
            "voice_alert": {
                "name": "Automated PA Synthesized Voice Evacuation Broadcast",
                "type": "Acoustic PA",
                "status": "STANDBY",
                "details": "Speech synthesizer announcement repeating zone evacuation orders"
            }
        }

    def update_alarm_state(self, risk_level, auto_timeout_check=True):
        """
        Updates primary alarm life cycle based on risk severity and acknowledgement timing.
        """
        now = datetime.now()

        if risk_level in ["CRITICAL", "RED", "HIGH", "ORANGE"]:
            # If standing by, trigger primary alarm
            if self.primary_alarm_status == "STANDBY":
                self.primary_alarm_status = "ACTIVE"
                self.alarm_trigger_time = now

            # If forced failure simulation active
            if self.simulated_failure_forced:
                self.primary_alarm_status = "FAILED"

            # Check for acknowledgement timeout
            elif self.primary_alarm_status == "ACTIVE" and self.alarm_trigger_time and auto_timeout_check:
                elapsed = (now - self.alarm_trigger_time).total_seconds()
                if elapsed > self.ack_timeout_seconds:
                    self.primary_alarm_status = "FAILED"

        else: # SAFE or WARNING
            if not self.simulated_failure_forced and self.primary_alarm_status not in ["ACKNOWLEDGED"]:
                self.primary_alarm_status = "STANDBY"
                self.alarm_trigger_time = None

        # Automatically engage backup systems if primary fails
        backup_active = (self.primary_alarm_status == "FAILED")
        for key in self.backup_systems:
            self.backup_systems[key]["status"] = "ACTIVE" if backup_active else "STANDBY"

        return self.get_alert_status()

    def acknowledge_alarm(self):
        """Operator acknowledges the alarm manually."""
        if self.primary_alarm_status in ["ACTIVE", "FAILED"]:
            self.primary_alarm_status = "ACKNOWLEDGED"
            self.simulated_failure_forced = False
            for key in self.backup_systems:
                self.backup_systems[key]["status"] = "STANDBY"
        return self.get_alert_status()

    def simulate_failure(self, force=True):
        """Manually test/force primary alarm failure."""
        self.simulated_failure_forced = force
        if force:
            self.primary_alarm_status = "FAILED"
            for key in self.backup_systems:
                self.backup_systems[key]["status"] = "ACTIVE"
        else:
            self.primary_alarm_status = "STANDBY"
            for key in self.backup_systems:
                self.backup_systems[key]["status"] = "STANDBY"
        return self.get_alert_status()

    def reset(self):
        self.primary_alarm_status = "STANDBY"
        self.alarm_trigger_time = None
        self.simulated_failure_forced = False
        for key in self.backup_systems:
            self.backup_systems[key]["status"] = "STANDBY"
        return self.get_alert_status()

    def get_alert_status(self):
        is_failed = (self.primary_alarm_status == "FAILED")
        is_backup_active = any(s["status"] == "ACTIVE" for s in self.backup_systems.values())

        return {
            "primary_alarm": {
                "status": self.primary_alarm_status,
                "is_failed": is_failed,
                "is_active": self.primary_alarm_status in ["ACTIVE", "FAILED"],
                "is_acknowledged": self.primary_alarm_status == "ACKNOWLEDGED",
                "badge_class": "danger" if is_failed else ("warning" if self.primary_alarm_status == "ACTIVE" else "success")
            },
            "backup_alerts": {
                "overall_status": "ACTIVATED" if is_backup_active else "STANDBY",
                "is_activated": is_backup_active,
                "active_count": sum(1 for s in self.backup_systems.values() if s["status"] == "ACTIVE"),
                "badge_class": "danger" if is_backup_active else "secondary",
                "systems": self.backup_systems
            },
            # ESP32 IoT payload representation
            "iot_payload": {
                "timestamp": datetime.now().isoformat(),
                "primary_buzzer_relay_gpio18": 1 if self.primary_alarm_status == "ACTIVE" else 0,
                "backup_strobe_relay_gpio19": 1 if is_backup_active else 0,
                "backup_haptic_lora_gpio21": 1 if is_backup_active else 0,
                "alarm_state": self.primary_alarm_status,
                "failover_triggered": 1 if is_backup_active else 0
            }
        }
