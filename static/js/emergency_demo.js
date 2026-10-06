/**
 * GASGUARD X - Emergency Demo Simulation Controller
 * Orchestrates the automated 16-step emergency lifecycle demonstration:
 * Baseline -> Equipment Wear -> Gas Release -> AI Classification ->
 * Alarm Trigger -> Siren Failure -> Autonomous Failover -> SQLite Incident Logging & Replay.
 */

class EmergencyDemoManager {
  constructor() {
    this.timer = null;
    this.currentStep = 0;
    this.totalSteps = 16;
    this.stepIntervalMs = 2800;
    this.bindEvents();
  }

  bindEvents() {
    const startBtns = document.querySelectorAll(".run-emergency-demo-btn");
    startBtns.forEach(btn => {
      btn.addEventListener("click", () => this.startDemo());
    });

    const stepBtn = document.getElementById("demoStepNextBtn");
    if (stepBtn) {
      stepBtn.addEventListener("click", () => this.stepNext());
    }

    const stopBtn = document.getElementById("demoStopBtn");
    if (stopBtn) {
      stopBtn.addEventListener("click", () => this.stopDemo());
    }
  }

  async startDemo() {
    this.stopDemo();
    this.currentStep = 0;

    // Show Demo Modal or HUD if present
    const demoBanner = document.getElementById("demoControlBanner");
    if (demoBanner) {
      demoBanner.classList.remove("d-none");
    }

    try {
      const res = await fetch("/api/demo/start", { method: "POST" });
      const data = await res.json();
      this.updateUI(data.state);

      window.gasguardClient?.showToast(
        "EMERGENCY SIMULATION STARTED",
        "Autonomous 16-step multi-layer safety scenario is running...",
        "warning"
      );

      // Launch automated stepping timer
      this.timer = setInterval(() => {
        this.stepNext();
      }, this.stepIntervalMs);

    } catch (e) {
      console.error("Failed to start demo:", e);
    }
  }

  async stepNext() {
    try {
      const res = await fetch("/api/demo/step", { method: "POST" });
      const data = await res.json();
      const state = data.state;
      this.currentStep = state.demo?.current_step || 0;
      this.updateUI(state);

      if (this.currentStep >= this.totalSteps) {
        this.completeDemo(state);
      }
    } catch (e) {
      console.error("Demo step error:", e);
      this.stopDemo();
    }
  }

  stopDemo() {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }

  updateUI(state) {
    // Notify all components
    document.dispatchEvent(new CustomEvent("gasguard:stateUpdate", { detail: state }));

    const stepBadge = document.getElementById("demoStepNumber");
    if (stepBadge) {
      stepBadge.textContent = `STEP ${state.demo?.current_step} / ${this.totalSteps}`;
    }

    const msgEl = document.getElementById("demoStepMessage");
    if (msgEl) {
      msgEl.textContent = state.demo?.message || "Running...";
    }

    const progBar = document.getElementById("demoProgressBar");
    if (progBar) {
      const pct = Math.round((state.demo?.current_step / this.totalSteps) * 100);
      progBar.style.width = `${pct}%`;
      progBar.textContent = `${pct}%`;
    }
  }

  completeDemo(state) {
    this.stopDemo();
    window.gasguardClient?.showToast(
      "SIMULATION COMPLETED & LOGGED",
      "Incident stored in SQLite. Incident Replay and Compliance Report are now available.",
      "success"
    );

    // Show Completion Prompt Modal if present
    const modalEl = document.getElementById("demoCompleteModal");
    if (modalEl && window.bootstrap?.Modal) {
      const modal = new bootstrap.Modal(modalEl);
      modal.show();
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  window.emergencyDemo = new EmergencyDemoManager();
});
