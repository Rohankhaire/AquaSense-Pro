// static/js/analytics.js

// Mock Data Generator for Charts
function generateHistory(days, min, max) {
    return Array.from({ length: days }, () => Math.floor(Math.random() * (max - min + 1) + min));
}

const days = Array.from({ length: 30 }, (_, i) => `Day ${i + 1}`);
const wqiData = [
    65, 68, 70, 72, 60, 55, 50, 48, 52, 60,
    65, 70, 75, 42, 45, 55, 62, 68, 72, 78,
    80, 82, 75, 70, 72, 78, 85, 88, 82, 80
]; // Semi-realistic pattern

// --- Chart 1: Monthly WQI Trend ---
const ctx1 = document.getElementById('monthlyChart').getContext('2d');
new Chart(ctx1, {
    type: 'line',
    data: {
        labels: days,
        datasets: [{
            label: 'WQI Score',
            data: wqiData,
            borderColor: '#ab47bc', // Purple
            backgroundColor: 'rgba(171, 71, 188, 0.2)',
            borderWidth: 3,
            fill: true,
            tension: 0.4,
            pointRadius: 3
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
            y: { min: 0, max: 100, grid: { color: 'rgba(255,255,255,0.05)' } },
            x: { display: false }
        }
    }
});

// --- Chart 2: Correlation (Turbidity vs DO) ---
const ctx2 = document.getElementById('correlationChart1').getContext('2d');
const turbidityData = generateHistory(30, 2, 80);
const doData = turbidityData.map(t => Math.max(0, 10 - (t / 10) + (Math.random() * 1))); // Fake inverse correlation

new Chart(ctx2, {
    type: 'line',
    data: {
        labels: days,
        datasets: [
            {
                label: 'Turbidity (NTU)',
                data: turbidityData,
                borderColor: '#60a5fa', // Blue
                yAxisID: 'y',
                borderWidth: 2,
                tension: 0.4,
                pointRadius: 0
            },
            {
                label: 'Dissolved Oxygen (mg/L)',
                data: doData,
                borderColor: '#34d399', // Green
                yAxisID: 'y1',
                borderWidth: 2,
                borderDash: [5, 5],
                tension: 0.4,
                pointRadius: 0
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { bottom: true } },
        scales: {
            y: { position: 'left', grid: { color: 'rgba(255,255,255,0.05)' } },
            y1: { position: 'right', grid: { display: false } },
            x: { display: false }
        }
    }
});

// --- Heatmap Logic ---
const heatmapGrid = document.getElementById('heatmapGrid');
wqiData.forEach(score => {
    const div = document.createElement('div');
    div.className = 'w-full h-8 rounded';

    // Color logic
    if (score >= 80) div.style.backgroundColor = '#10b981'; // Green
    else if (score >= 60) div.style.backgroundColor = '#fbbf24'; // Yellow
    else div.style.backgroundColor = '#ef4444'; // Red

    // Opacity based on intensity (simple visual trick)
    div.style.opacity = 0.6 + (score / 200);

    div.title = `Score: ${score}`;
    heatmapGrid.appendChild(div);
});
