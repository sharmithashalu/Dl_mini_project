/**
 * GASGUARD X - Dynamic Factory Risk Map Controller
 * Renders interactive SVG floor plan with Zones A-D, sensor nodes,
 * worker personnel beacons, equipment assets, and dynamic gas dispersion plumes.
 */

class FactoryRiskMap {
  constructor() {
    this.svgElement = document.getElementById("factoryMapSvg");
    this.tooltipEl = document.getElementById("mapTooltip");
    this.currentLeakZone = "Zone B";
    this.listenForUpdates();
  }

  listenForUpdates() {
    document.addEventListener("gasguard:stateUpdate", (e) => {
      const state = e.detail;
      this.updateMap(state);
    });
  }

  updateMap(state) {
    if (!this.svgElement) return;

    const loc = state.localization || {};
    const risk = state.risk || {};
    const workers = state.workers?.workers || [];
    const sensors = state.sensors?.raw_inputs || {};
    const trust = state.sensors?.health?.trust_scores || {};
    const equipment = state.equipment?.assets || [];

    this.currentLeakZone = loc.probable_zone || "Zone B";

    // 1. Update Zone Tinting & Stroke
    this.updateZoneColors(loc, risk);

    // 2. Update Dynamic Gas Plume
    this.updateGasPlume(loc.coordinates, state.gas?.concentration_ppm, risk.risk_level);

    // 3. Update Sensor Nodes
    this.updateSensorNodes(sensors, trust);

    // 4. Update Worker Pins
    this.updateWorkerPins(workers);

    // 5. Update Equipment Icons
    this.updateEquipmentNodes(equipment);

    // 6. Update Map Header / Legend
    this.updateMapHeader(loc, risk);
  }

  updateZoneColors(loc, risk) {
    const zones = ["ZoneA", "ZoneB", "ZoneC", "ZoneD"];
    const probZoneKey = (loc.probable_zone || "").replace(" ", "");

    zones.forEach(z => {
      const polygon = document.getElementById(`poly${z}`);
      if (!polygon) return;

      if (z === probZoneKey) {
        // High risk active zone
        if (risk.risk_level === "CRITICAL" || risk.risk_level === "RED") {
          polygon.setAttribute("fill", "rgba(239, 68, 68, 0.25)");
          polygon.setAttribute("stroke", "#ef4444");
          polygon.setAttribute("stroke-width", "3");
        } else if (risk.risk_level === "HIGH" || risk.risk_level === "ORANGE") {
          polygon.setAttribute("fill", "rgba(249, 115, 22, 0.20)");
          polygon.setAttribute("stroke", "#f97316");
          polygon.setAttribute("stroke-width", "2.5");
        } else if (risk.risk_level === "YELLOW" || risk.risk_level === "WARNING") {
          polygon.setAttribute("fill", "rgba(245, 158, 11, 0.18)");
          polygon.setAttribute("stroke", "#f59e0b");
          polygon.setAttribute("stroke-width", "2");
        } else {
          polygon.setAttribute("fill", "rgba(16, 185, 129, 0.08)");
          polygon.setAttribute("stroke", "rgba(16, 185, 129, 0.3)");
          polygon.setAttribute("stroke-width", "1.5");
        }
      } else {
        // Ambient adjacent zones
        polygon.setAttribute("fill", "rgba(18, 26, 43, 0.45)");
        polygon.setAttribute("stroke", "rgba(255, 255, 255, 0.1)");
        polygon.setAttribute("stroke-width", "1");
      }
    });
  }

  updateGasPlume(coords, ppm = 0, riskLevel = "SAFE") {
    const plume = document.getElementById("gasPlumeElement");
    if (!plume) return;

    if (!coords || ppm < 15.0 || riskLevel === "SAFE" || riskLevel === "GREEN") {
      plume.setAttribute("visibility", "hidden");
      return;
    }

    plume.setAttribute("visibility", "visible");
    plume.setAttribute("cx", coords.x || 450);
    plume.setAttribute("cy", coords.y || 120);

    // Size scales with concentration
    const radius = Math.min(130, Math.max(35, ppm * 0.95));
    plume.setAttribute("r", radius);

    // Color gradient based on severity
    if (riskLevel === "CRITICAL" || riskLevel === "RED") {
      plume.setAttribute("fill", "url(#plumeCriticalGrad)");
    } else if (riskLevel === "HIGH" || riskLevel === "ORANGE") {
      plume.setAttribute("fill", "url(#plumeHighGrad)");
    } else {
      plume.setAttribute("fill", "url(#plumeWarnGrad)");
    }
  }

  updateSensorNodes(sensors, trust) {
    const sensorList = ["S1", "S2", "S3", "S4", "S5"];
    sensorList.forEach(sId => {
      const node = document.getElementById(`sensorNode_${sId}`);
      const text = document.getElementById(`sensorVal_${sId}`);
      if (!node) return;

      const val = Math.round(sensors[sId] || 100);
      const tScore = trust[sId] || 98;

      if (text) {
        text.textContent = `${sId}: ${val}`;
      }

      if (tScore < 50) {
        node.setAttribute("fill", "#64748b"); // Faulty sensor grey/drift
      } else if (val > 250) {
        node.setAttribute("fill", "#ef4444"); // High gas red
      } else if (val > 150) {
        node.setAttribute("fill", "#f59e0b"); // Warning amber
      } else {
        node.setAttribute("fill", "#06b6d4"); // Nominal cyan
      }
    });
  }

  updateWorkerPins(workers) {
    workers.forEach(w => {
      const pin = document.getElementById(`workerPin_${w.worker_id}`);
      if (!pin) return;

      const circle = pin.querySelector("circle");
      if (circle) {
        if (w.exposure_risk === "CRITICAL") {
          circle.setAttribute("fill", "#ef4444");
          circle.setAttribute("stroke", "#ffffff");
        } else if (w.exposure_risk === "HIGH") {
          circle.setAttribute("fill", "#f97316");
        } else if (w.exposure_risk === "MEDIUM") {
          circle.setAttribute("fill", "#f59e0b");
        } else {
          circle.setAttribute("fill", "#10b981");
        }
      }
    });
  }

  updateEquipmentNodes(equipment) {
    equipment.forEach(item => {
      const icon = document.getElementById(`equipIcon_${item.asset_id}`);
      if (!icon) return;

      if (item.status === "CRITICAL DEGRADATION") {
        icon.setAttribute("stroke", "#ef4444");
      } else if (item.status === "ATTENTION REQUIRED") {
        icon.setAttribute("stroke", "#f59e0b");
      } else {
        icon.setAttribute("stroke", "#38bdf8");
      }
    });
  }

  updateMapHeader(loc, risk) {
    const leakBadge = document.getElementById("mapLeakZoneBadge");
    if (leakBadge) {
      leakBadge.textContent = `${loc.probable_zone || 'None'} (${loc.confidence || 0}% Conf)`;
      leakBadge.className = `badge bg-${risk.badge_class || 'secondary'}`;
    }
  }

  showNodeTooltip(event, title, content) {
    if (!this.tooltipEl) return;
    this.tooltipEl.innerHTML = `<strong>${title}</strong><br>${content}`;
    this.tooltipEl.style.display = "block";
    this.tooltipEl.style.left = `${event.pageX + 12}px`;
    this.tooltipEl.style.top = `${event.pageY + 12}px`;
  }

  hideNodeTooltip() {
    if (!this.tooltipEl) return;
    this.tooltipEl.style.display = "none";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  window.factoryRiskMap = new FactoryRiskMap();
});
