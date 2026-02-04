# 🌊 AquaSense Pro - Water Quality Intelligence Platform

An AI-powered water quality monitoring system that uses satellite data and machine learning to predict Water Quality Index (WQI) in real-time.

## 🚀 Features

- **Real-time Satellite Data Integration**: Fetches live data from Sentinel-2 satellites via Google Earth Engine
- **AI-Powered Predictions**: Hybrid ML model (Random Forest + XGBoost) for accurate WQI calculation
- **Interactive Dashboard**: Beautiful, modern UI with live data visualization
- **Manual Calibration**: Simulator page for testing different water parameter scenarios
- **PDF Report Generation**: Export detailed water quality reports
- **Analytics Dashboard**: Historical trends and data insights

## 🛠️ Tech Stack

- **Backend**: Python, Flask
- **Machine Learning**: scikit-learn, XGBoost
- **Satellite Data**: Google Earth Engine API
- **Frontend**: HTML, CSS (Tailwind), JavaScript
- **Visualization**: Chart.js, Leaflet Maps

## 📦 Installation

1. Clone the repository:
```bash
git clone https://github.com/Rohankhaire/aqua-sense-pro.git
cd aqua-sense-pro
```

2. Create a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Train the ML model (if not already present):
```bash
python train_model.py
```

5. Run the application:
```bash
python server.py
```

6. Open your browser and navigate to:
```
http://127.0.0.1:5000
```

## 🌐 Google Earth Engine Setup (Optional)

For live satellite data:
1. Create a Google Cloud Project
2. Enable Earth Engine API
3. Authenticate: `earthengine authenticate`
4. Update `EE_PROJECT` in `server.py` with your project ID

**Note**: The app works in LOCAL MODE with default values if Earth Engine is not configured.

## 📊 Usage

### Home Page
- Click **"Sync Satellite"** to fetch live satellite data
- View real-time WQI score and water quality assessment
- Download PDF reports

### Simulator Page
- Manually adjust water parameters using sliders
- Test different scenarios
- View instant WQI predictions

### Analytics Page
- View historical trends
- Analyze parameter correlations

## 🎯 Water Quality Parameters

The system monitors 8 key parameters:
- pH Level
- Turbidity
- Total Dissolved Solids (TDS)
- Dissolved Oxygen (DO)
- Temperature
- Conductivity
- Chlorine
- Nitrate

## 📈 WQI Scale

- **90-100**: Excellent Quality (Safe)
- **75-89**: Good Quality (Minor Issues)
- **55-74**: Fair Quality (Monitor Closely)
- **35-54**: Poor Quality (Immediate Concern)
- **0-34**: Hazardous Quality (Critical)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available under the MIT License.

## 👨‍💻 Author

**Rohan Khaire**
- GitHub: [@Rohankhaire](https://github.com/Rohankhaire)

## 🙏 Acknowledgments

- Sentinel-2 Satellite Data (ESA Copernicus)
- Google Earth Engine
- Open-source ML libraries
