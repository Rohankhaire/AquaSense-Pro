# server.py
from flask import Flask, request, jsonify, render_template
import joblib
import numpy as np
import os
from datetime import datetime, timedelta
from time import sleep

# ------------------ GOOGLE EARTH ENGINE SETUP ------------------
EE_PROJECT = "seventh-helix-486409-q9"  # 👈 your registered project ID
EE_AVAILABLE = False  # Flag to track if Earth Engine is available

try:
    import ee
    
    def init_ee(retries=1):
        """Initializes Google Earth Engine with your Cloud Project ID."""
        global EE_AVAILABLE
        for i in range(retries):
            try:
                ee.Initialize(project=EE_PROJECT)
                print(f" Earth Engine initialized with project: {EE_PROJECT}")
                EE_AVAILABLE = True
                return
            except Exception as e:
                print(f"⚠️  ee.Initialize failed: {e}")
                print("⚠️  Running in LOCAL MODE without Earth Engine (using default values)")
                EE_AVAILABLE = False
                return

    init_ee()
except ImportError:
    print("  Earth Engine module not available")
    print(" Running in LOCAL MODE - using default parameter values")
    EE_AVAILABLE = False
except Exception as e:
    print(f"  Earth Engine not available: {e}")
    print(" Running in LOCAL MODE - using default parameter values")
    EE_AVAILABLE = False
# ---------------------------------------------------------------

app = Flask(__name__, static_folder='static', template_folder='templates')

# Load your ML model
MODEL_PATH = os.path.join('model', 'model.joblib')
if not os.path.exists(MODEL_PATH):
    raise RuntimeError("❌ Model not found. Run train_model.py first.")
model = joblib.load(MODEL_PATH)
print(" Model loaded successfully.")

# --- Default fallback values ---
PARAM_DEFAULTS = {
    'ph': 7.5, 'turbidity': 2.0, 'tds': 350, 'do': 8.5,
    'temp': 22.0, 'conductivity': 700, 'chlorine': 0.8, 'nitrate': 4.0
}

MODEL_FEATURES = ['ph','turbidity','tds','do','temp','conductivity','chlorine','nitrate']

# Define Ganga ROI (Varanasi example) - only if Earth Engine is available
GANGA_REGION = None
if EE_AVAILABLE:
    try:
        import ee
        GANGA_REGION = ee.Geometry.Rectangle([82.9, 25.2, 83.1, 25.4])
    except:
        pass

def get_assessment(wqi):
    if wqi >= 90: return "Excellent Quality (Safe)"
    elif wqi >= 75: return "Good Quality (Minor Issues)"
    elif wqi >= 55: return "Fair Quality (Monitor Closely)"
    elif wqi >= 35: return "Poor Quality (Immediate Concern)"
    else: return "Hazardous Quality (Critical)"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/analytics')
def analytics():
    return render_template('analytics.html')

@app.route('/simulator')
def simulator():
    return render_template('simulator.html')


# 🌍 Fetch real-time Sentinel-2 data
def get_latest_sentinel2_data():
    if not EE_AVAILABLE:
        print("  Earth Engine not available. Using default parameter values.")
        return PARAM_DEFAULTS
    
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=10)

        collection = (
            ee.ImageCollection('COPERNICUS/S2_SR')
            .filterBounds(GANGA_REGION)
            .filterDate(start_date.isoformat(), end_date.isoformat())
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
            .median()
        )

        ndwi = collection.normalizedDifference(['B3', 'B8']).rename('NDWI')
        ndvi = collection.normalizedDifference(['B8', 'B4']).rename('NDVI')
        mndwi = collection.normalizedDifference(['B3', 'B11']).rename('MNDWI')

        ndwi_val = ndwi.reduceRegion(ee.Reducer.mean(), GANGA_REGION, 30).get('NDWI').getInfo()
        ndvi_val = ndvi.reduceRegion(ee.Reducer.mean(), GANGA_REGION, 30).get('NDVI').getInfo()
        mndwi_val = mndwi.reduceRegion(ee.Reducer.mean(), GANGA_REGION, 30).get('MNDWI').getInfo()

        if ndwi_val is None or ndvi_val is None or mndwi_val is None:
            print("⚠️  Sentinel-2 data unavailable for the last 10 days.")
            return PARAM_DEFAULTS  # fallback

        # Convert spectral indices → approximate parameters
        data = {
            'ph': round(7.0 + (ndvi_val or 0) * 0.5, 2),
            'turbidity': round(max(0.1, (1 - (ndwi_val or 0)) * 10), 2),
            'tds': round(300 + (1 - (mndwi_val or 0)) * 200, 2),
            'do': round(8.0 - (ndvi_val or 0) * 2, 2),
            'temp': 25.0,
            'conductivity': round(600 + (1 - (mndwi_val or 0)) * 400, 2),
            'chlorine': 0.8,
            'nitrate': round(5.0 + (1 - (ndvi_val or 0)) * 3, 2)
        }

        print(f"✅ Live Sentinel-2 data: {data}")
        return data
    except Exception as e:
        print(f"❌ Error fetching Sentinel-2 data: {e}")
        return PARAM_DEFAULTS


@app.route('/api/get-live-data')
def get_live_data():
    try:
        data = get_latest_sentinel2_data()
        return jsonify(data)
    except Exception as e:
        print("❌ Error fetching Sentinel-2 data:", e)
        return jsonify(PARAM_DEFAULTS)


@app.route('/api/predict', methods=['POST'])
def predict():
    data = request.get_json()
    try:
        features = [float(data[key]) for key in MODEL_FEATURES]
    except Exception as e:
        return jsonify({'error': 'Invalid or missing input', 'details': str(e)}), 400

    pred = model.predict([features])[0]
    wqi = int(round(pred))
    wqi = max(0, min(100, wqi))

    # 🔧 Apply calibration to make predictions realistic
    # (scales down optimistic results ~25% and adds a small offset)
    wqi_calibrated = int(round(0.75 * wqi + 5))
    wqi = max(0, min(100, wqi_calibrated))

    return jsonify({'wqi': wqi, 'assessment': get_assessment(wqi)})


if __name__ == '__main__':
    app.run(debug=True)
