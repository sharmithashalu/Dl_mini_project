/**
 * GASGUARD X - Charts & Telemetry Visualizations
 * Chart.js configurations for E-Nose sensor radar, live trend stream,
 * equipment health bars, and safety resilience gauges.
 */

class GasGuardCharts {
  constructor() {
    this.enoseChart = null;
    this.telemetryTrendChart = null;
    this.resilienceChart = null;
    this.equipmentChart = null;

    this.trendHistory = {
      labels: [],
      ppm: [],
      pressure: [],
      vibration: []
    };
    this.maxHistoryPoints = 15;

    this.initCharts();
    this.listenForUpdates();
  }

  initCharts() {
    // 1. E-Nose Array Radar Chart
    const enoseCtx = document.getElementById("enoseRadarChart");
    if (enoseCtx) {
      this.enoseChart = new Chart(enoseCtx, {
        type: 'radar',
        data: {
          labels: ['S1 (NH3)', 'S2 (CH4)', 'S3 (CO)', 'S4 (LPG)', 'S5 (VOC)'],
          datasets: [{
            label: 'Sensor Resistance/Voltage (A.U.)',
            data: [115, 108, 95, 102, 120],
            backgroundColor: 'rgba(6, 182, 212, 0.25)',
            borderColor: '#06b6d4',
            pointBackgroundColor: '#38bdf8',
            pointBorderColor: '#fff',
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: '#38bdf8',
            borderWidth: 2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            r: {
              angleLines: { color: 'rgba(255, 255, 255, 0.1)' },
              grid: { color: 'rgba(255, 255, 255, 0.08)' },
              pointLabels: { color: '#94a3b8', font: { family: 'Outfit', size: 11, weight: '600' } },
              ticks: { display: false, backdropColor: 'transparent' }
            }
          },
          plugins: {
            legend: { display: false }
          }
        }
      });
    }

    // 2. Live Telemetry Trend Line Chart
    const trendCtx = document.getElementById("telemetryTrendChart");
    if (trendCtx) {
      this.telemetryTrendChart = new Chart(trendCtx, {
        type: 'line',
        data: {
          labels: [],
          datasets: [
            {
              label: 'Gas Concentration (PPM)',
              data: [],
              borderColor: '#ef4444',
              backgroundColor: 'rgba(239, 68, 68, 0.15)',
              yAxisID: 'yGas',
              tension: 0.35,
              fill: true,
              borderWidth: 2
            },
            {
              label: 'Line Pressure (bar)',
              data: [],
              borderColor: '#38bdf8',
              yAxisID: 'yTech',
              tension: 0.35,
              borderWidth: 2
            },
            {
              label: 'Vibration (mm/s)',
              data: [],
              borderColor: '#f59e0b',
              yAxisID: 'yTech',
              tension: 0.35,
              borderWidth: 2
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { mode: 'index', intersect: false },
          scales: {
            x: {
              grid: { color: 'rgba(255, 255, 255, 0.05)' },
              ticks: { color: '#64748b', font: { family: 'JetBrains Mono', size: 10 } }
            },
            yGas: {
              type: 'linear',
              position: 'left',
              title: { display: true, text: 'PPM', color: '#ef4444' },
              grid: { color: 'rgba(255, 255, 255, 0.05)' },
              ticks: { color: '#ef4444' }
            },
            yTech: {
              type: 'linear',
              position: 'right',
              title: { display: true, text: 'bar / mm/s', color: '#38bdf8' },
              grid: { drawOnChartArea: false },
              ticks: { color: '#94a3b8' }
            }
          },
          plugins: {
            legend: {
              labels: { color: '#cbd5e1', font: { family: 'Outfit', size: 11 } }
            }
          }
        }
      });
    }

    // 3. Resilience Score Breakdown Bar Chart
    const resCtx = document.getElementById("resilienceBarChart");
    if (resCtx) {
      this.resilienceChart = new Chart(resCtx, {
        type: 'bar',
        data: {
          labels: ['Sensors', 'Alarm', 'Backup', 'Equipment', 'Comm/Workers'],
          datasets: [{
            data: [90, 45, 100, 70, 85],
            backgroundColor: [
              'rgba(56, 189, 248, 0.65)',
              'rgba(239, 68, 68, 0.65)',
              'rgba(16, 185, 129, 0.65)',
              'rgba(245, 158, 11, 0.65)',
              'rgba(99, 102, 241, 0.65)'
            ],
            borderRadius: 6,
            borderWidth: 1,
            borderColor: 'rgba(255, 255, 255, 0.15)'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              max: 100,
              min: 0,
              grid: { color: 'rgba(255, 255, 255, 0.05)' },
              ticks: { color: '#94a3b8' }
            },
            x: {
              grid: { display: false },
              ticks: { color: '#cbd5e1', font: { family: 'Outfit', size: 10 } }
            }
          },
          plugins: {
            legend: { display: false }
          }
        }
      });
    }

    // 4. Equipment Health Horizontal Bar Chart
    const equipCtx = document.getElementById("equipmentHealthChart");
    if (equipCtx) {
      this.equipmentChart = new Chart(equipCtx, {
        type: 'bar',
        data: {
          labels: ['Valve V-01', 'Pipe P-02', 'Compressor C-01', 'Pump P-04'],
          datasets: [{
            axis: 'y',
            data: [64, 92, 58, 88],
            backgroundColor: [
              'rgba(245, 158, 11, 0.7)',
              'rgba(16, 185, 129, 0.7)',
              'rgba(239, 68, 68, 0.7)',
              'rgba(16, 185, 129, 0.7)'
            ],
            borderRadius: 6
          }]
        },
        options: {
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            x: {
              max: 100,
              min: 0,
              grid: { color: 'rgba(255, 255, 255, 0.05)' },
              ticks: { color: '#94a3b8' }
            },
            y: {
              grid: { display: false },
              ticks: { color: '#cbd5e1', font: { family: 'Outfit', size: 11 } }
            }
          },
          plugins: {
            legend: { display: false }
          }
        }
      });
    }
  }

  listenForUpdates() {
    document.addEventListener("gasguard:stateUpdate", (e) => {
      const state = e.detail;
      this.updateCharts(state);
    });
  }

  updateCharts(state) {
    // Update E-Nose Radar
    if (this.enoseChart && state.sensors?.raw_inputs) {
      const raw = state.sensors.raw_inputs;
      this.enoseChart.data.datasets[0].data = [
        raw.S1 || 115, raw.S2 || 108, raw.S3 || 95, raw.S4 || 102, raw.S5 || 120
      ];
      this.enoseChart.update('none');
    }

    // Update Telemetry Trend Line
    if (this.telemetryTrendChart && state.gas && state.equipment) {
      const timeLabel = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      const worstAsset = state.equipment.lowest_asset || {};

      this.trendHistory.labels.push(timeLabel);
      this.trendHistory.ppm.push(state.gas.concentration_ppm || 0);
      this.trendHistory.pressure.push(worstAsset.pressure || 5.0);
      this.trendHistory.vibration.push(worstAsset.vibration || 1.2);

      if (this.trendHistory.labels.length > this.maxHistoryPoints) {
        this.trendHistory.labels.shift();
        this.trendHistory.ppm.shift();
        this.trendHistory.pressure.shift();
        this.trendHistory.vibration.shift();
      }

      this.telemetryTrendChart.data.labels = [...this.trendHistory.labels];
      this.telemetryTrendChart.data.datasets[0].data = [...this.trendHistory.ppm];
      this.telemetryTrendChart.data.datasets[1].data = [...this.trendHistory.pressure];
      this.telemetryTrendChart.data.datasets[2].data = [...this.trendHistory.vibration];
      this.telemetryTrendChart.update('none');
    }

    // Update Resilience Breakdown Bar
    if (this.resilienceChart && state.resilience?.breakdown) {
      const bd = state.resilience.breakdown;
      const scores = [
        bd["Sensor Reliability"]?.score || 90,
        bd["Alarm Reliability"]?.score || 45,
        bd["Backup Alert Readiness"]?.score || 100,
        bd["Equipment Health"]?.score || 70,
        bd["Emergency Communication"]?.score || 85
      ];
      this.resilienceChart.data.datasets[0].data = scores;
      this.resilienceChart.update('none');
    }

    // Update Equipment Fleet Health
    if (this.equipmentChart && state.equipment?.assets) {
      const scores = state.equipment.assets.map(a => a.health_score);
      const colors = scores.map(s => s >= 80 ? 'rgba(16, 185, 129, 0.7)' : (s >= 55 ? 'rgba(245, 158, 11, 0.7)' : 'rgba(239, 68, 68, 0.7)'));
      this.equipmentChart.data.datasets[0].data = scores;
      this.equipmentChart.data.datasets[0].backgroundColor = colors;
      this.equipmentChart.update('none');
    }
  }
}

document.addEventListener("DOMContentLoaded", () => {
  window.gasguardCharts = new GasGuardCharts();
});
