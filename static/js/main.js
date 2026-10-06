/**
 * GASGUARD X - Main Client-Side Controller
 * Handles live polling, audio synthesis, voice alert broadcasts,
 * toast alerts, and primary alarm failover interactions.
 */

class GasGuardClient {
  constructor() {
    this.pollInterval = null;
    this.audioContext = null;
    this.isMuted = false;
    this.lastAlarmStatus = "STANDBY";
    this.speechSynthesisActive = false;
    this.init();
  }

  init() {
    this.initAudioContext();
    this.bindGlobalEvents();
    this.startPolling();
  }

  initAudioContext() {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        this.audioContext = new AudioCtx();
      }
    } catch (e) {
      console.warn("Web Audio API not supported:", e);
    }
  }

  // Play synthesized dual-frequency warning buzzer using Web Audio API
  playSirenTone(freq1 = 880, freq2 = 1200, duration = 0.8) {
    if (this.isMuted || !this.audioContext) return;
    try {
      if (this.audioContext.state === 'suspended') {
        this.audioContext.resume();
      }
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();
      
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(freq1, this.audioContext.currentTime);
      osc.frequency.linearRampToValueAtTime(freq2, this.audioContext.currentTime + duration * 0.5);
      osc.frequency.linearRampToValueAtTime(freq1, this.audioContext.currentTime + duration);

      gain.gain.setValueAtTime(0.08, this.audioContext.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.audioContext.currentTime + duration);

      osc.connect(gain);
      gain.connect(this.audioContext.destination);

      osc.start();
      osc.stop(this.audioContext.currentTime + duration);
    } catch (e) {
      console.warn("Audio tone error:", e);
    }
  }

  // Speak voice announcement using Web Speech API
  speakAlert(text) {
    if (this.isMuted || !('speechSynthesis' in window)) return;
    try {
      window.speechSynthesis.cancel(); // Stop prior speeches
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.05;
      utterance.pitch = 1.0;
      utterance.volume = 0.9;
      window.speechSynthesis.speak(utterance);
    } catch (e) {
      console.warn("Speech synthesis error:", e);
    }
  }

  bindGlobalEvents() {
    // Mute/Unmute audio button
    const muteBtn = document.getElementById("toggleMuteBtn");
    if (muteBtn) {
      muteBtn.addEventListener("click", () => {
        this.isMuted = !this.isMuted;
        muteBtn.innerHTML = this.isMuted 
          ? '<i class="bi bi-volume-mute-fill"></i> Sound Muted' 
          : '<i class="bi bi-volume-up-fill"></i> Sound Active';
        muteBtn.classList.toggle("btn-outline-secondary", this.isMuted);
        muteBtn.classList.toggle("btn-outline-info", !this.isMuted);
      });
    }

    // Acknowledge Alarm Button
    const ackBtn = document.getElementById("ackAlarmBtn");
    if (ackBtn) {
      ackBtn.addEventListener("click", () => this.acknowledgeAlarm());
    }

    // Simulate Primary Alarm Failure Button
    const failBtn = document.getElementById("simAlarmFailBtn");
    if (failBtn) {
      failBtn.addEventListener("click", () => this.simulateAlarmFailure());
    }

    // Reset Factory Button
    const resetBtn = document.getElementById("resetFactoryBtn");
    if (resetBtn) {
      resetBtn.addEventListener("click", () => this.resetFactory());
    }
  }

  startPolling() {
    this.pollInterval = setInterval(() => {
      this.fetchTelemetry();
    }, 2800);
  }

  async fetchTelemetry() {
    try {
      const response = await fetch("/api/telemetry");
      if (!response.ok) return;
      const state = await response.json();
      this.handleStateUpdate(state);
    } catch (e) {
      console.warn("Telemetry fetch error:", e);
    }
  }

  handleStateUpdate(state) {
    // Dispatch custom event for widgets, charts, and maps to consume
    const event = new CustomEvent("gasguard:stateUpdate", { detail: state });
    document.dispatchEvent(event);

    this.updateNavbarMetrics(state);
    this.checkAlarmTransitions(state);
  }

  updateNavbarMetrics(state) {
    const riskBadge = document.getElementById("navRiskBadge");
    if (riskBadge && state.risk) {
      riskBadge.textContent = `${state.risk.risk_score}/100 (${state.risk.level_text})`;
      riskBadge.className = `badge bg-${state.risk.badge_class}`;
    }

    const resilienceBadge = document.getElementById("navResilienceBadge");
    if (resilienceBadge && state.resilience) {
      resilienceBadge.textContent = `${state.resilience.resilience_score}/100`;
      resilienceBadge.className = `badge bg-${state.resilience.badge_class}`;
    }
  }

  checkAlarmTransitions(state) {
    const primaryStatus = state.alerts?.primary_alarm?.status;
    const isBackupActive = state.alerts?.backup_alerts?.is_activated;

    // Siren and speech triggers
    if (primaryStatus === "FAILED" && this.lastAlarmStatus !== "FAILED") {
      this.showToast("CRITICAL FAILOVER", "Primary Siren Failed! Autonomous multi-layer backup alerts engaged.", "danger");
      this.playSirenTone(700, 1400, 1.2);
      this.speakAlert("Warning. Primary alarm failed. Multi-layer backup systems activated. Evacuate zone immediately.");
      document.body.classList.add("beacon-active-overlay");
    } else if (primaryStatus === "ACTIVE" && this.lastAlarmStatus !== "ACTIVE") {
      this.showToast("PRIMARY ALARM ACTIVE", "Audible siren triggered in plant. Awaiting acknowledgment.", "warning");
      this.playSirenTone(880, 1100, 0.6);
      this.speakAlert("Attention. Gas concentration threshold exceeded. Safety protocol engaged.");
    } else if (primaryStatus === "STANDBY" || primaryStatus === "ACKNOWLEDGED") {
      document.body.classList.remove("beacon-active-overlay");
    }

    this.lastAlarmStatus = primaryStatus;
  }

  async acknowledgeAlarm() {
    try {
      const res = await fetch("/api/alarm/acknowledge", { method: "POST" });
      const data = await res.json();
      this.showToast("Alarm Acknowledged", "Operator acknowledged active alarm. Multi-layer backup returned to standby.", "success");
      this.fetchTelemetry();
    } catch (e) {
      console.error("Ack error:", e);
    }
  }

  async simulateAlarmFailure() {
    try {
      const res = await fetch("/api/alarm/simulate-failure", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ force: true })
      });
      const data = await res.json();
      this.showToast("Failure Injected", "Primary audible alarm circuit faulted. Multi-layer failover initiated.", "danger");
      this.fetchTelemetry();
    } catch (e) {
      console.error("Fail error:", e);
    }
  }

  async resetFactory() {
    try {
      const res = await fetch("/api/demo/reset", { method: "POST" });
      const data = await res.json();
      this.showToast("System Reset", "All plant parameters and alarm circuits restored to safe baseline.", "info");
      this.fetchTelemetry();
    } catch (e) {
      console.error("Reset error:", e);
    }
  }

  showToast(title, message, type = "info") {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toastEl = document.createElement("div");
    toastEl.className = `toast align-items-center text-white bg-${type === 'danger' ? 'danger' : (type === 'warning' ? 'warning text-dark' : 'dark')} border-0 show mb-2`;
    toastEl.setAttribute("role", "alert");
    toastEl.innerHTML = `
      <div class="d-flex">
        <div class="toast-body">
          <strong>${title}</strong><br>${message}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
      </div>
    `;
    container.appendChild(toastEl);
    setTimeout(() => {
      toastEl.classList.remove("show");
      setTimeout(() => toastEl.remove(), 400);
    }, 4500);
  }
}

// Global client instance
window.gasguardClient = new GasGuardClient();
