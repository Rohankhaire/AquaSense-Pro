// static/js/app.js

// --- Global Variables ---
let predictionChart;
let map;
let sessionHistory = []; // Stores {wqi, time} for the current session

// DOM Elements
const metricsGrid = document.getElementById('metrics-grid');
const alertLog = document.getElementById('alert-log');
const wqiScoreDisplay = document.getElementById('wqi-score');
const qualityBadge = document.getElementById('quality-badge');
const predictButton = document.getElementById('predictButton');
const fetchLiveButton = document.getElementById('fetchLiveButton');
const recommendationsPanel = document.getElementById('recommendations-panel');
const recommendationsList = document.getElementById('recommendations-list');
const downloadReportBtn = document.getElementById('downloadReportBtn');
const qualityRing = document.getElementById('score-ring');
const pulseEffect = document.getElementById('pulse-effect');

// Parameter Definitions with Extended Metadata
const parameters = [
  { id: 'ph', label: 'pH Level', unit: 'pH', min: 0, max: 14, idealMin: 6.5, idealMax: 8.5, step: 0.1, msgHigh: "Neutralize acidity immediately.", msgLow: "Increase alkalinity.", labelClass: "text-slate-700" },
  { id: 'turbidity', label: 'Turbidity', unit: 'NTU', min: 0, max: 100, idealMin: 0, idealMax: 5.0, step: 0.1, msgHigh: "High suspension. Filtration required.", labelClass: "text-slate-700" },
  { id: 'tds', label: 'TDS', unit: 'mg/L', min: 0, max: 2000, idealMin: 0, idealMax: 500, step: 1, msgHigh: "High dissolved solids. Reverse Osmosis recommended.", labelClass: "text-slate-700" },
  { id: 'do', label: 'Dissolved Oxygen', unit: 'mg/L', min: 0, max: 20, idealMin: 6.5, idealMax: 20, step: 0.1, msgLow: "Critical oxygen depletion. Aeration needed.", labelClass: "text-slate-700" },
  { id: 'temp', label: 'Temperature', unit: '°C', min: 0, max: 50, idealMin: 10, idealMax: 30, step: 0.1, msgHigh: "Temperature too high for aquatic balance.", msgLow: "Temperature too low.", labelClass: "text-slate-700" },
  { id: 'conductivity', label: 'Conductivity', unit: 'µS/cm', min: 0, max: 2000, idealMin: 0, idealMax: 1000, step: 1, msgHigh: "High ionic content detected.", labelClass: "text-slate-700" },
  { id: 'chlorine', label: 'Chlorine', unit: 'mg/L', min: 0, max: 10, idealMin: 0.2, idealMax: 1.0, step: 0.01, msgHigh: "Dechlorination required.", msgLow: "Disinfection risk.", labelClass: "text-slate-700" },
  { id: 'nitrate', label: 'Nitrate', unit: 'mg/L', min: 0, max: 100, idealMin: 0, idealMax: 10.0, step: 0.1, msgHigh: "Runoff pollution. Denitrification needed.", labelClass: "text-slate-700" }
];

// --- Initialization ---
window.onload = function () {
  // Page Detection
  const isSimulator = document.getElementById('metrics-grid') !== null;
  const isHome = document.getElementById('map') !== null && !isSimulator;

  if (document.getElementById('map')) {
    initMap();
  }

  if (isSimulator) {
    generateMetricInputs();
    predictButton.addEventListener('click', predictQuality);
  } else if (isHome) {
    // Manual sync requested by user, removed auto-fetch
    // fetchLiveData(); 
  }

  initChart(); // Chart exists on both pages

  const fetchBtn = document.getElementById('fetchLiveButton');
  if (fetchBtn) {
    fetchBtn.addEventListener('click', fetchLiveData);
  }

  if (downloadReportBtn) {
    downloadReportBtn.addEventListener('click', generatePDFReport);
  }
};

// ... inside fetchLiveData ...
async function fetchLiveData() {
  // ...
  // Populate fields OR Read-Only Display
  const isSimulator = document.getElementById('metrics-grid') !== null;

  if (isSimulator) {
    parameters.forEach(p => {
      if (data[p.id] !== undefined) {
        const el = document.getElementById(p.id);
        const slide = document.getElementById(`${p.id}-slide`);
        el.value = data[p.id];
        slide.value = data[p.id];
        validateRangeColor(el, p);
      }
    });
    await predictQuality(); // Auto-predict on Simulator sync
  } else {
    // Home Page: We don't have inputs, so we just calculate score internally or update a Read-Only Grid
    // For now, let's just create a hidden predictive call or update the "Live Trend" if possible
    // But wait, predictQuality needs inputs.
    // We should create a specialized 'predictFromData' function or refactor.

    // Quick Hack: Just update the chart with random 'Live' data for visual effect on Home?
    // Better: Send the fetched data to backend for prediction without reading DOM

    const mockInputs = {};
    parameters.forEach(p => mockInputs[p.id] = data[p.id] || ((p.min + p.max) / 2));

    // Call prediction API directly
    const predResp = await fetch('/api/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(mockInputs)
    });
    const predData = await predResp.json();

    animateValue(wqiScoreDisplay, parseInt(wqiScoreDisplay.textContent) || 0, predData.wqi, 1500);
    updateAssessmentUI(predData.wqi, predData.assessment);
    updateChart(predData.wqi);
  }
  // ...
}

// --- Map Setup (Leaflet) ---
function initMap() {
  // Coordinates for Varanasi (Ganga)
  const lat = 25.3176;
  const lng = 82.9739;

  map = L.map('map', {
    center: [lat, lng],
    zoom: 13,
    zoomControl: false,
    attributionControl: false
  });

  // Light Theme Tiles (CartoDB Positron)
  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
  }).addTo(map);

  L.marker([lat, lng]).addTo(map)
    .bindPopup('<b>Monitoring Station A1</b><br>Ganga River, Varanasi')
    .openPopup();
}

// --- UI Generation & Sync ---
function generateMetricInputs() {
  metricsGrid.innerHTML = parameters.map(p => `
    <div class="col-span-1 space-y-2">
      <div class="flex justify-between items-center">
        <label for="${p.id}" class="text-sm font-medium text-slate-700">${p.label}</label>
        <span class="text-xs text-slate-500">${p.unit}</span>
      </div>
      <div class="flex items-center space-x-3">
        <input type="range" id="${p.id}-slide" 
          min="${p.min}" max="${p.max}" step="${p.step}" value="${(p.min + p.max) / 2}"
          class="flex-grow h-2 bg-slate-300 rounded-lg appearance-none cursor-pointer">
          
        <input type="number" id="${p.id}" 
          class="form-input w-24 text-center font-mono font-bold text-slate-900 bg-white border-slate-300" 
          step="${p.step}" placeholder="0" value="${(p.min + p.max) / 2}">
      </div>
      <div class="flex justify-between text-[10px] text-slate-500 font-mono">
        <span>Min: ${p.min}</span>
        <span class="text-teal-600">Ideal: ${p.idealMin}-${p.idealMax}</span>
        <span>Max: ${p.max}</span>
      </div>
    </div>
  `).join('');

  // Add event listeners for sync
  parameters.forEach(p => {
    const slide = document.getElementById(`${p.id}-slide`);
    const input = document.getElementById(`${p.id}`);

    // Slide -> Input
    slide.addEventListener('input', (e) => {
      input.value = e.target.value;
      validateRangeColor(input, p);
    });

    // Input -> Slide
    input.addEventListener('input', (e) => {
      let val = parseFloat(e.target.value);
      if (!isNaN(val)) {
        slide.value = val;
        validateRangeColor(input, p);
      }
    });
  });
}

function validateRangeColor(inputElement, param) {
  const val = parseFloat(inputElement.value);
  if (isNaN(val)) return;

  // Visual feedback on the input border and text
  if (val >= param.idealMin && val <= param.idealMax) {
    inputElement.style.borderColor = "#2dd4bf"; // Teal (Good)
    inputElement.style.color = "#0f766e"; // Dark Teal Text for visibility
  } else {
    inputElement.style.borderColor = "#f43f5e"; // Red (Warning)
    inputElement.style.color = "#be123c"; // Dark Red Text
  }
}

// --- Core Logic: Prediction ---
async function predictQuality() {
  const inputs = {};
  let isValid = true;

  // Gather data
  parameters.forEach(p => {
    const val = parseFloat(document.getElementById(p.id).value);
    if (isNaN(val)) {
      showAlert(`Missing input for ${p.label}`, 'warn');
      isValid = false;
      // Highlight empty
      document.getElementById(p.id).classList.add('border-red-500');
    } else {
      inputs[p.id] = val;
      document.getElementById(p.id).classList.remove('border-red-500');
    }
  });

  if (!isValid) return;

  predictButton.innerHTML = `<span class="animate-spin mr-2 inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full"></span> Analyzing...`;

  try {
    const resp = await fetch('/api/predict', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(inputs)
    });

    const data = await resp.json();

    // 1. Update Score with Animation
    animateValue(wqiScoreDisplay, parseInt(wqiScoreDisplay.textContent) || 0, data.wqi, 1500);

    // 2. Update Badge & Visuals
    updateAssessmentUI(data.wqi, data.assessment);

    // 3. Update Chart
    updateChart(data.wqi);

    // 4. Generate Recommendations
    generateRecommendations(inputs, data.wqi);

    // 5. Show Report Button
    downloadReportBtn.classList.remove('hidden');

    showAlert(`Analysis Complete. WQI: ${data.wqi}`, 'success');

  } catch (e) {
    showAlert('API Error: ' + e.message, 'error');
  } finally {
    predictButton.innerHTML = `<svg class="w-5 h-5 mr-2 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg> Analyze Water Quality`;
  }
}

// --- Visual Helpers ---
function animateValue(obj, start, end, duration) {
  let startTimestamp = null;
  const step = (timestamp) => {
    if (!startTimestamp) startTimestamp = timestamp;
    const progress = Math.min((timestamp - startTimestamp) / duration, 1);
    obj.innerHTML = Math.floor(progress * (end - start) + start);
    if (progress < 1) {
      window.requestAnimationFrame(step);
    } else {
      obj.innerHTML = end;
    }
  };
  window.requestAnimationFrame(step);
}

function updateAssessmentUI(wqi, text) {
  const badge = qualityBadge;
  const ring = qualityRing;

  let colorClass = "";
  let ringColor = "";

  if (wqi >= 90) {
    colorClass = "bg-emerald-100 text-emerald-800 border-emerald-200";
    ringColor = "border-emerald-500";
    pulseEffect.className = "absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-48 h-48 bg-emerald-500/20 rounded-full blur-2xl animate-pulse";
  }
  else if (wqi >= 75) {
    colorClass = "bg-teal-100 text-teal-800 border-teal-200";
    ringColor = "border-teal-500";
    pulseEffect.className = "absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-48 h-48 bg-teal-500/10 rounded-full blur-xl";
  }
  else if (wqi >= 55) {
    colorClass = "bg-yellow-100 text-yellow-800 border-yellow-200";
    ringColor = "border-yellow-500";
    pulseEffect.className = "absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-32 h-32 bg-yellow-500/10 rounded-full blur-xl";
  }
  else {
    colorClass = "bg-red-100 text-red-800 border-red-200";
    ringColor = "border-red-500";
    pulseEffect.className = "absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-48 h-48 bg-red-500/30 rounded-full blur-2xl animate-pulse";
  }

  badge.className = `inline-block px-6 py-2 rounded-full text-base font-bold backdrop-blur-md border transition-all duration-300 shadow-sm ${colorClass}`;
  badge.textContent = text;

  ring.className = `absolute inset-0 border-4 rounded-2xl pointer-events-none transition-colors duration-1000 ${ringColor} status-ring`;
}

// --- Recommendations Logic ---
function generateRecommendations(inputs, wqi) {
  recommendationsList.innerHTML = '';
  let count = 0;

  // Hard Rule Checks
  parameters.forEach(p => {
    const val = inputs[p.id];
    if (p.idealMax && val > p.idealMax) {
      addRec(p.msgHigh || `High ${p.label} detected. Investigate source.`);
      count++;
    }
    if (p.idealMin && val < p.idealMin) {
      addRec(p.msgLow || `Low ${p.label} detected.`);
      count++;
    }
  });

  if (wqi < 50) addRec("WQI is Critical. Immediate water treatment halted recommended.");

  if (count > 0) {
    recommendationsPanel.classList.remove('hidden');
    recommendationsPanel.classList.add('animate-enter');
  } else {
    recommendationsPanel.classList.add('hidden');
  }
}

function addRec(text) {
  const li = document.createElement('li');
  li.innerHTML = text;
  recommendationsList.appendChild(li);
}

// --- Chart Logic ---
function initChart() {
  const ctx = document.getElementById('predictionChart').getContext('2d');
  // Start with last 5 hypothetical points
  const initData = [70, 72, 71, 74, 73];
  const labels = ['T-4', 'T-3', 'T-2', 'T-1', 'Start'];

  predictionChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'WQI History',
        data: initData,
        borderColor: '#0d9488',
        backgroundColor: 'rgba(13, 148, 136, 0.1)',
        borderWidth: 2,
        tension: 0.4,
        pointRadius: 4,
        pointHoverRadius: 6,
        fill: true
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { min: 0, max: 100, grid: { color: '#e2e8f0' }, ticks: { color: '#64748b' } },
        x: { grid: { display: false }, ticks: { color: '#64748b' } }
      },
      plugins: { legend: { display: false } }
    }
  });
}

function updateChart(newVal) {
  const timeLabel = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  predictionChart.data.labels.push(timeLabel);
  predictionChart.data.datasets[0].data.push(newVal);

  // Keep chart not too crowded
  if (predictionChart.data.labels.length > 10) {
    predictionChart.data.labels.shift();
    predictionChart.data.datasets[0].data.shift();
  }
  predictionChart.update();
}

// --- Live Data Fetching ---
async function fetchLiveData() {
  showAlert('Contacting Sentinel-2 Satellite API...', 'info');
  const fetchBtn = document.getElementById('fetchLiveButton');
  if (fetchBtn) fetchBtn.classList.add('opacity-50', 'cursor-not-allowed');

  try {
    const resp = await fetch('/api/get-live-data');
    const data = await resp.json();

    const isSimulator = document.getElementById('metrics-grid') !== null;

    if (isSimulator) {
      parameters.forEach(p => {
        if (data[p.id] !== undefined) {
          const el = document.getElementById(p.id);
          const slide = document.getElementById(`${p.id}-slide`);
          el.value = data[p.id];
          slide.value = data[p.id];
          validateRangeColor(el, p);
        }
      });
      showAlert('Satellite Data Synced Successfully.', 'success');
      await predictQuality();
    } else {
      // Home Page Logic
      const grid = document.getElementById('live-readings-grid');
      if (grid) grid.innerHTML = ''; // Clear loading

      const mockInputs = {};
      parameters.forEach(p => {
        const val = data[p.id] || ((p.min + p.max) / 2);
        mockInputs[p.id] = val;

        if (grid) {
          // Create Card
          grid.innerHTML += `
               <div class="bg-slate-50 border border-slate-200 p-4 rounded-xl text-center shadow-sm hover:shadow-md transition">
                  <div class="text-xs text-slate-500 uppercase font-bold mb-1 tracking-wider">${p.label}</div>
                  <div class="text-2xl font-black text-slate-800">${parseFloat(val).toFixed(1)} <span class="text-xs font-normal text-slate-400">${p.unit}</span></div>
               </div>
            `;
        }
      });

      const predResp = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mockInputs)
      });
      const predData = await predResp.json();

      animateValue(wqiScoreDisplay, parseInt(wqiScoreDisplay.textContent) || 0, predData.wqi, 1500);
      updateAssessmentUI(predData.wqi, predData.assessment);
      updateChart(predData.wqi);
      showAlert('Live Satellite Data Updated.', 'success');

      // Show report button after sync
      if (downloadReportBtn) {
        downloadReportBtn.classList.remove('hidden');
      }
    }

    // Store globally for PDF report
    window.lastFetchedData = data;

  } catch (e) {
    showAlert('Data Sync Failed: ' + e.message, 'error');
  } finally {
    if (fetchBtn) fetchBtn.classList.remove('opacity-50', 'cursor-not-allowed');
  }
}

// --- Utilities ---
// --- Utilities ---
function showAlert(msg, type) {
  const div = document.createElement('div');
  const color = type === 'error' ? 'text-red-600' : (type === 'success' ? 'text-emerald-600' : 'text-blue-600');
  div.className = `${color} text-xs py-1 border-b border-slate-200 font-mono`;
  // Simple arrow prompt instead of emoji
  div.innerText = `> ${msg}`;
  alertLog.prepend(div);
}

// Update loading text without emoji
// ... inside predictQuality ...
// predictButton.innerHTML = `<span class="animate-spin mr-2 inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full"></span> Analyzing...`;

// --- PDF Report ---
function generatePDFReport() {
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF();

  doc.setFont("helvetica", "bold");
  doc.setFontSize(22);
  doc.setTextColor(0, 128, 128); // Teal color
  doc.text("PureCast | Water Quality Report", 20, 20);

  doc.setFontSize(12);
  doc.setTextColor(100);
  doc.text(`Generated: ${new Date().toLocaleString()}`, 20, 30);
  doc.text(`Location: Ganga River Monitoring Station (Varanasi)`, 20, 36);

  doc.setLineWidth(0.5);
  doc.line(20, 40, 190, 40);

  // Results
  doc.setFontSize(16);
  doc.setTextColor(0);
  doc.text("Analysis Results", 20, 50);

  const wqi = wqiScoreDisplay.innerText;
  const assessment = qualityBadge.innerText;

  doc.setFontSize(14);
  doc.text(`Overall WQI Score: ${wqi}/100`, 20, 60);
  doc.text(`Assessment: ${assessment}`, 20, 68);

  // Parameters Table
  let y = 85;
  doc.setFontSize(12);
  doc.text("Parameter Readings:", 20, 80);

  parameters.forEach(p => {
    let val = "N/A";
    const el = document.getElementById(p.id);
    if (el) {
      val = el.value;
    } else if (window.lastFetchedData && window.lastFetchedData[p.id] !== undefined) {
      val = window.lastFetchedData[p.id];
    }

    doc.text(`${p.label}: ${parseFloat(val).toFixed(2)} ${p.unit}`, 30, y);
    y += 8;
  });

  // Recommendations
  if (!recommendationsPanel.classList.contains('hidden')) {
    y += 10;
    doc.setFontSize(14);
    doc.setTextColor(200, 0, 0);
    doc.text("AI Recommendations:", 20, y);
    y += 8;
    doc.setFontSize(10);
    doc.setTextColor(0);

    const recs = recommendationsList.getElementsByTagName('li');
    for (let li of recs) {
      doc.text(`• ${li.innerText}`, 25, y);
      y += 6;
    }
  }

  doc.save("PureCast_Report.pdf");
}
