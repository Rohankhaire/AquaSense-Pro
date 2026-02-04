# 🛠️ AquaSense Pro - Technical Stack & Architecture

## 📋 Table of Contents
1. [Technology Stack](#technology-stack)
2. [System Architecture](#system-architecture)
3. [Data Flow](#data-flow)
4. [Component Details](#component-details)
5. [ML Model Pipeline](#ml-model-pipeline)

---

## 🔧 Technology Stack

### **Backend Technologies**
| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.11+ | Core programming language |
| **Flask** | 3.0+ | Web framework for API and routing |
| **Google Earth Engine** | Latest | Satellite data acquisition (Sentinel-2) |

### **Machine Learning Stack**
| Technology | Purpose |
|------------|---------|
| **scikit-learn** | Base ML framework, Random Forest model |
| **XGBoost** | Gradient boosting model for enhanced accuracy |
| **NumPy** | Numerical computations |
| **Pandas** | Data manipulation and preprocessing |
| **Joblib** | Model serialization/deserialization |

### **Frontend Technologies**
| Technology | Purpose |
|------------|---------|
| **HTML5** | Structure and semantic markup |
| **Tailwind CSS** | Utility-first styling framework |
| **Vanilla JavaScript** | Client-side logic and interactivity |
| **Chart.js** | Data visualization (line charts, trends) |
| **Leaflet.js** | Interactive maps for monitoring stations |
| **jsPDF** | Client-side PDF report generation |

### **Data Sources**
| Source | Type | Update Frequency |
|--------|------|------------------|
| **Sentinel-2** | Satellite imagery | 5-day revisit cycle |
| **Google Earth Engine** | Geospatial data platform | Real-time API |
| **Synthetic Training Data** | Generated dataset | One-time (4000 samples) |

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Dashboard   │  │  Simulator   │  │  Analytics   │      │
│  │   (Home)     │  │   (Manual)   │  │   (Trends)   │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    FLASK WEB SERVER                          │
│  ┌────────────────────────────────────────────────────┐     │
│  │  Routes:                                            │     │
│  │  • GET  /              → index.html                │     │
│  │  • GET  /simulator     → simulator.html            │     │
│  │  • GET  /analytics     → analytics.html            │     │
│  │  • GET  /api/get-live-data → Satellite fetch       │     │
│  │  • POST /api/predict   → ML prediction             │     │
│  └────────────────────────────────────────────────────┘     │
└─────────┬───────────────────────────┬───────────────────────┘
          │                           │
          ▼                           ▼
┌──────────────────────┐    ┌──────────────────────┐
│  GOOGLE EARTH ENGINE │    │   ML MODEL ENGINE    │
│  ┌────────────────┐  │    │  ┌────────────────┐  │
│  │ Sentinel-2 API │  │    │  │ Hybrid Model:  │  │
│  │ • NDWI         │  │    │  │ • Random Forest│  │
│  │ • NDVI         │  │    │  │ • XGBoost      │  │
│  │ • MNDWI        │  │    │  │ • Stacking     │  │
│  └────────────────┘  │    │  └────────────────┘  │
└──────────────────────┘    └──────────────────────┘
          │                           │
          └───────────┬───────────────┘
                      ▼
          ┌──────────────────────┐
          │   WQI CALCULATION    │
          │   (0-100 Scale)      │
          └──────────────────────┘
```

---

## 🔄 Data Flow Diagram

### **1. Live Satellite Data Flow**

```
User clicks "Sync Satellite"
         │
         ▼
┌─────────────────────────┐
│  Frontend (app.js)      │
│  fetchLiveData()        │
└───────────┬─────────────┘
            │ AJAX GET /api/get-live-data
            ▼
┌─────────────────────────────────────────┐
│  Backend (server.py)                    │
│  @app.route('/api/get-live-data')       │
│  ├─ Check EE_AVAILABLE                  │
│  ├─ If True: get_latest_sentinel2_data()│
│  │   ├─ Query Sentinel-2 (last 10 days) │
│  │   ├─ Filter clouds (<20%)            │
│  │   ├─ Calculate spectral indices:     │
│  │   │   • NDWI = (B3-B8)/(B3+B8)       │
│  │   │   • NDVI = (B8-B4)/(B8+B4)       │
│  │   │   • MNDWI = (B3-B11)/(B3+B11)    │
│  │   └─ Convert to water parameters     │
│  └─ If False: Return PARAM_DEFAULTS     │
└───────────┬─────────────────────────────┘
            │ JSON Response
            ▼
┌─────────────────────────┐
│  Frontend receives:     │
│  {                      │
│    ph: 7.2,             │
│    turbidity: 3.5,      │
│    tds: 420,            │
│    do: 7.8,             │
│    temp: 25.0,          │
│    conductivity: 750,   │
│    chlorine: 0.8,       │
│    nitrate: 6.2         │
│  }                      │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Display on Dashboard   │
│  • Update parameter cards│
│  • Auto-predict WQI     │
└─────────────────────────┘
```

### **2. WQI Prediction Flow**

```
User triggers prediction (Auto or Manual)
         │
         ▼
┌─────────────────────────┐
│  Collect 8 parameters:  │
│  • pH                   │
│  • Turbidity            │
│  • TDS                  │
│  • Dissolved Oxygen     │
│  • Temperature          │
│  • Conductivity         │
│  • Chlorine             │
│  • Nitrate              │
└───────────┬─────────────┘
            │ POST /api/predict
            ▼
┌─────────────────────────────────────────┐
│  Backend ML Pipeline                    │
│  @app.route('/api/predict')             │
│  ├─ Load model.joblib                   │
│  ├─ Prepare feature vector [8 values]   │
│  ├─ model.predict([features])           │
│  │   ├─ Random Forest prediction        │
│  │   ├─ XGBoost prediction              │
│  │   └─ Meta-learner combines results   │
│  ├─ Apply calibration (0.75*wqi + 5)    │
│  ├─ Clamp to [0, 100]                   │
│  └─ Generate assessment text            │
└───────────┬─────────────────────────────┘
            │ JSON Response
            ▼
┌─────────────────────────┐
│  {                      │
│    wqi: 78,             │
│    assessment:          │
│      "Good Quality      │
│       (Minor Issues)"   │
│  }                      │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Frontend Updates:      │
│  • Animated WQI score   │
│  • Color-coded badge    │
│  • Update trend chart   │
│  • Generate recommendations│
│  • Enable PDF button    │
└─────────────────────────┘
```

---

## 🧩 Component Details

### **1. Backend Components**

#### **server.py** - Main Flask Application
```python
Key Functions:
├─ init_ee()                    # Initialize Google Earth Engine
├─ get_latest_sentinel2_data()  # Fetch satellite data
├─ get_assessment(wqi)          # Convert WQI to text assessment
└─ Routes:
   ├─ /                         # Home dashboard
   ├─ /simulator                # Manual testing page
   ├─ /analytics                # Historical trends
   ├─ /api/get-live-data        # Satellite data endpoint
   └─ /api/predict              # ML prediction endpoint
```

**Satellite Data Conversion Logic:**
```python
# Spectral indices → Water parameters
ph = 7.0 + (NDVI * 0.5)                    # Range: 6.5-8.5
turbidity = max(0.1, (1 - NDWI) * 10)      # Range: 0-100 NTU
tds = 300 + (1 - MNDWI) * 200              # Range: 0-2000 mg/L
do = 8.0 - (NDVI * 2)                      # Range: 0-20 mg/L
conductivity = 600 + (1 - MNDWI) * 400     # Range: 0-2000 µS/cm
```

#### **train_model.py** - ML Model Training
```python
Pipeline:
1. generate_synthetic(n=4000)
   ├─ Creates realistic water quality dataset
   ├─ Uses normal/exponential distributions
   └─ Calculates ground truth WQI

2. build_hybrid_model()
   ├─ RandomForestRegressor (250 trees, depth=12)
   ├─ XGBRegressor (400 trees, lr=0.05, depth=8)
   └─ StackingRegressor with LinearRegression meta-learner

3. train_and_save()
   ├─ 80/20 train-test split
   ├─ Fit model on training data
   ├─ Evaluate: R² score, MAE
   └─ Save to model/model.joblib (28MB)
```

**WQI Calculation Formula:**
```python
WQI = Σ(subindex_i × weight_i)

Where:
subindex_i = 100 × (1 - deviation/tolerance)
deviation = |value - ideal_range|

Weights:
├─ Dissolved Oxygen: 25%
├─ Turbidity: 20%
├─ TDS: 15%
├─ Nitrate: 15%
├─ Conductivity: 10%
├─ pH: 5%
├─ Temperature: 5%
└─ Chlorine: 5%
```

### **2. Frontend Components**

#### **app.js** - Main JavaScript Logic
```javascript
Key Functions:
├─ initMap()                    # Initialize Leaflet map
├─ generateMetricInputs()       # Create parameter sliders
├─ fetchLiveData()              # Fetch from satellite API
├─ predictQuality()             # Send data to ML API
├─ updateAssessmentUI()         # Update visual feedback
├─ updateChart()                # Add point to trend chart
├─ generateRecommendations()    # AI-based suggestions
└─ generatePDFReport()          # Export PDF report
```

**Parameter Validation:**
```javascript
Ideal Ranges:
├─ pH: 6.5-8.5
├─ Turbidity: 0-5 NTU
├─ TDS: 0-500 mg/L
├─ DO: 6.5-20 mg/L
├─ Temperature: 10-30°C
├─ Conductivity: 0-1000 µS/cm
├─ Chlorine: 0.2-1.0 mg/L
└─ Nitrate: 0-10 mg/L

Visual Feedback:
├─ Green border: Within ideal range
└─ Red border: Outside ideal range
```

#### **Chart.js Integration**
```javascript
Chart Configuration:
├─ Type: Line chart
├─ Data: Last 10 WQI readings
├─ Y-axis: 0-100 (WQI scale)
├─ X-axis: Timestamps
├─ Features:
│  ├─ Smooth curves (tension: 0.4)
│  ├─ Fill area under line
│  └─ Responsive design
```

---

## 🤖 ML Model Pipeline

### **Training Phase** (One-time)

```
┌─────────────────────────┐
│  Synthetic Data Gen     │
│  • 4000 samples         │
│  • 8 features           │
│  • Realistic distributions│
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Feature Engineering    │
│  • Normalize weights    │
│  • Calculate WQI labels │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Model Training         │
│  ┌───────────────────┐  │
│  │ Random Forest     │  │
│  │ • 250 estimators  │  │
│  │ • Max depth: 12   │  │
│  └─────────┬─────────┘  │
│  ┌─────────▼─────────┐  │
│  │ XGBoost           │  │
│  │ • 400 estimators  │  │
│  │ • Learning: 0.05  │  │
│  │ • Max depth: 8    │  │
│  └─────────┬─────────┘  │
│  ┌─────────▼─────────┐  │
│  │ Stacking          │  │
│  │ • Meta: LinReg    │  │
│  │ • Passthrough: On │  │
│  └───────────────────┘  │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Model Evaluation       │
│  • R² Score: ~0.95+     │
│  • MAE: <3 points       │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Save Model             │
│  model/model.joblib     │
│  (28.8 MB)              │
└─────────────────────────┘
```

### **Prediction Phase** (Runtime)

```
Input: [ph, turbidity, tds, do, temp, conductivity, chlorine, nitrate]
         │
         ▼
┌─────────────────────────┐
│  Load model.joblib      │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Random Forest          │
│  Prediction: 82.3       │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  XGBoost                │
│  Prediction: 79.8       │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Meta-Learner           │
│  Weighted Average       │
│  Raw WQI: 81.2          │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Calibration            │
│  WQI = 0.75×81.2 + 5    │
│  Final WQI: 66          │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  Assessment Mapping     │
│  66 → "Fair Quality     │
│       (Monitor Closely)"│
└─────────────────────────┘
```

---

## 🌐 API Endpoints

### **GET /api/get-live-data**
**Purpose:** Fetch real-time satellite data

**Response:**
```json
{
  "ph": 7.2,
  "turbidity": 3.5,
  "tds": 420,
  "do": 7.8,
  "temp": 25.0,
  "conductivity": 750,
  "chlorine": 0.8,
  "nitrate": 6.2
}
```

### **POST /api/predict**
**Purpose:** Calculate WQI from parameters

**Request:**
```json
{
  "ph": 7.2,
  "turbidity": 3.5,
  "tds": 420,
  "do": 7.8,
  "temp": 25.0,
  "conductivity": 750,
  "chlorine": 0.8,
  "nitrate": 6.2
}
```

**Response:**
```json
{
  "wqi": 78,
  "assessment": "Good Quality (Minor Issues)"
}
```

---

## 📊 Performance Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| **Model R² Score** | 0.95+ | Excellent fit |
| **Mean Absolute Error** | <3 points | High accuracy |
| **Model Size** | 28.8 MB | Compressed with joblib |
| **Prediction Time** | <50ms | Fast inference |
| **Satellite Data Fetch** | 2-5s | Depends on GEE API |
| **Page Load Time** | <1s | Optimized assets |

---

## 🔐 Security Considerations

1. **API Keys**: Earth Engine credentials stored securely
2. **Input Validation**: All user inputs sanitized
3. **CORS**: Configured for production deployment
4. **Rate Limiting**: Recommended for production (not implemented)

---

## 🚀 Deployment Architecture

### **Recommended Stack:**
```
┌─────────────────────────┐
│  Frontend (Static)      │
│  • GitHub Pages         │
│  • Netlify              │
│  • Vercel               │
└───────────┬─────────────┘
            │ API Calls
            ▼
┌─────────────────────────┐
│  Backend (Python)       │
│  • Render               │
│  • Railway              │
│  • PythonAnywhere       │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│  External Services      │
│  • Google Earth Engine  │
│  • Sentinel-2 Satellites│
└─────────────────────────┘
```

---

## 📝 File Structure

```
aqua-sense-pro/
├── server.py                 # Flask backend (176 lines)
├── train_model.py            # ML training script (146 lines)
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation
├── TECH_STACK.md            # This file
├── .gitignore               # Git exclusions
├── model/
│   └── model.joblib         # Trained ML model (28.8 MB)
├── static/
│   ├── css/
│   │   └── style.css        # Custom styles
│   └── js/
│       ├── app.js           # Main frontend logic (535 lines)
│       └── analytics.js     # Analytics page logic
└── templates/
    ├── index.html           # Dashboard (225 lines)
    ├── simulator.html       # Manual testing page
    ├── analytics.html       # Trends visualization
    └── about.html           # Methodology documentation
```

---

## 🎯 Future Enhancements

1. **Real-time Monitoring**: WebSocket integration for live updates
2. **Historical Database**: PostgreSQL for long-term data storage
3. **User Authentication**: Multi-user support with role-based access
4. **Mobile App**: React Native companion app
5. **Advanced Analytics**: Time-series forecasting with LSTM
6. **Multi-location**: Support for multiple monitoring stations
7. **Alert System**: Email/SMS notifications for critical WQI levels

---

**Last Updated:** February 4, 2026  
**Version:** 1.0.0
