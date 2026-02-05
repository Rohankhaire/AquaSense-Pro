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


# 🌍 Realistic Fallback Generator (Aligned with Training Data Distribution)
def generate_realistic_ganga_data():
    """
    Generates data that aligns with the statistical distribution of the training dataset.
    Dataset Stats:
    - pH: 7.0 ± 1.2
    - Turbidity: 5.0 ± 2.9
    - TDS: 802 ± 405
    - DO: 5.5 ± 2.0
    - Temp: 25.0 ± 5.8
    - EC: 1052 ± 548
    - Chlorine: 1.05 ± 0.55
    - Nitrate: 7.5 ± 4.3
    """
    now = datetime.now()
    month = now.month
    hour = now.hour
    rng = np.random
    
    # 1. Seasonal Offsets (shifts the mean slightly based on season)
    is_summer = 3 <= month <= 6
    is_winter = 11 <= month or month <= 2
    
    # Temperature: seasonal shift from dataset mean (25.0)
    temp_offset = 0
    if is_summer: temp_offset = 5.0
    elif is_winter: temp_offset = -7.0
    
    # Diurnal Temp Variation
    diurnal = -2.0 * np.cos((hour - 14) * np.pi / 12) # Peak at 2 PM
    temp = 25.0 + temp_offset + diurnal + rng.normal(0, 2.0)
    
    # 2. Parameter Generation (Centered on Dataset Means)
    
    # pH: Mean 7.0
    ph = rng.normal(7.0, 0.5) # tighter std dev for realism than raw dataset
    ph = max(4.0, min(10.0, ph))
    
    # Turbidity: Mean ~5.0
    turb_offset = 2.0 if (7 <= month <= 9) else 0 # Higher in monsoon
    turbidity = max(0.1, rng.normal(5.0 + turb_offset, 2.0))
    
    # TDS: Mean ~800
    tds = max(50, rng.normal(802.5, 200.0)) # 200 std dev for stability
    
    # Conductivity (EC): Mean ~1050.  Correlation: EC ~= 1.3 * TDS usually
    # Dataset Ratio: 1051 / 802 = 1.31
    conductivity = tds * 1.31 + rng.normal(0, 50)
    
    # DO: Mean ~5.5. Inverse to Temp.
    # If Temp > 25, DO should be < 5.5
    do_offset = (25.0 - temp) * 0.1 # Small adjustment
    do = max(1.0, rng.normal(5.5 + do_offset, 1.5))
    
    # Chlorine: Mean ~1.05
    chlorine = max(0.01, rng.normal(1.05, 0.3))
    
    # Nitrate: Mean ~7.5
    nitrate = max(0.0, rng.normal(7.54, 2.0))

    return {
        'ph': round(ph, 2),
        'turbidity': round(turbidity, 2),
        'tds': round(tds, 2),
        'do': round(do, 2),
        'temp': round(temp, 2),
        'conductivity': round(conductivity, 2),
        'chlorine': round(chlorine, 2),
        'nitrate': round(nitrate, 2)
    }


# 🌍 Helper: Get last known data from CSV to prevent random fluctuations
def get_last_known_data():
    csv_file = 'live_predictions.csv'
    if not os.path.exists(csv_file):
        return None, None
    
    try:
        import csv
        with open(csv_file, 'r') as f:
            lines = list(csv.reader(f))
            if len(lines) < 2:  # Only header or empty
                return None, None
            
            last_row = lines[-1]
            # CSV Header: timestamp, ph, turbidity, tds, do, temp, conductivity, chlorine, nitrate, wqi, assessment
            if len(last_row) < 9:
                return None, None
            
            timestamp = last_row[0]
            data = {
                'ph': float(last_row[1]),
                'turbidity': float(last_row[2]),
                'tds': float(last_row[3]),
                'do': float(last_row[4]),
                'temp': float(last_row[5]),
                'conductivity': float(last_row[6]),
                'chlorine': float(last_row[7]),
                'nitrate': float(last_row[8])
            }
            return data, timestamp
    except Exception as e:
        print(f"⚠️ Error reading last known data: {e}")
        return None, None

# 🌍 Fetch real-time Sentinel-2 data
def get_latest_sentinel2_data():
    # 1. Try Earth Engine (Real Data)
    if EE_AVAILABLE:
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

            # Check if we actually have data coverage
            check = collection.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=GANGA_REGION,
                scale=100
            ).getInfo()
            
            if not check or not any(check.values()):
                raise ValueError("No recent satellite data found (Cloudy/No Pass)")

            ndwi = collection.normalizedDifference(['B3', 'B8']).rename('NDWI')
            ndvi = collection.normalizedDifference(['B8', 'B4']).rename('NDVI')
            mndwi = collection.normalizedDifference(['B3', 'B11']).rename('MNDWI')
            
            # Reduce region
            image = collection.addBands([ndwi, ndvi, mndwi])
            stats = image.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=GANGA_REGION,
                scale=30
            ).getInfo()

            red_val = stats.get('B4', 0.05)
            ndvi_val = stats.get('NDVI', 0)
            
            # --- Scientific Approximations ---
            turbidity = max(0.5, round(100 * (red_val ** 1.5), 2)) 
            tds = round(200 + (turbidity * 15), 2)
            ph = max(6.5, min(9.0, round(7.2 + (ndvi_val * 3.0), 2)))
            
            current_month = datetime.now().month
            base_temp = 28.0 if 4 <= current_month <= 9 else (18.0 if 10 <= current_month <= 3 else 20.0)
            temp = base_temp + (red_val * 10)
            
            do = round((14.6 - (0.3 * temp)) * 0.85, 2)
            nitrate = round(max(0.5, ndvi_val * 50), 2)
            conductivity = round(tds * 1.6, 2)
            chlorine = 0.2

            data = {
                'ph': ph, 'turbidity': turbidity, 'tds': tds, 'do': do,
                'temp': round(temp, 2), 'conductivity': conductivity,
                'chlorine': chlorine, 'nitrate': nitrate
            }
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"✅ Live Sentinel-2 data: {data}")
            return data, "live", timestamp

        except Exception as e:
            print(f"⚠️ Earth Engine fetch failed/incomplete: {e}")

    # 2. Fallback: Use LAST KNOWN DATA (Stability)
    last_data, last_ts = get_last_known_data()
    if last_data:
        print(f"ℹ️ Using last known data from {last_ts}")
        return last_data, "cached", last_ts

    # 3. Last Resort: Generate New Simulation
    print("⚠️ No history found. Generating simulation.")
    return generate_realistic_ganga_data(), "simulated", datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@app.route('/api/get-live-data')
def get_live_data():
    try:
        # 1. Fetch Data with Metadata
        data, source, timestamp = get_latest_sentinel2_data()
        
        # 2. Predict WQI Server-Side
        try:
            features = [float(data[key]) for key in MODEL_FEATURES]
            pred = model.predict([features])[0]
            wqi = int(round(max(0, min(100, pred))))
            assessment = get_assessment(wqi)
        except Exception as e:
            print(f"❌ Prediction error: {e}")
            wqi = 0
            assessment = "Error"

        # 3. Store Only if 'Live' or 'Simulated' (Don't duplicate cached rows unless forced logic changes)
        # Actually, for history consistency, we might want to log user requests, but let's only append if it's NEW data
        # or just append every fetch for "Time Series" continuity? 
        # Requirement: "values change honar nahit" -> So we should NOT append if it is cached data?
        # But if we don't append, the charts won't update?
        # Let's append only if source is NOT 'cached' to avoid duplicates? 
        # User asked for "Last known data" fallback.
        
        csv_file = 'live_predictions.csv'
        if source != "cached": 
            try:
                file_exists = os.path.isfile(csv_file)
                with open(csv_file, 'a', newline='') as f:
                    import csv
                    writer = csv.writer(f)
                    if not file_exists:
                        writer.writerow(['timestamp'] + MODEL_FEATURES + ['wqi', 'assessment'])
                    writer.writerow([timestamp] + [data[key] for key in MODEL_FEATURES] + [wqi, assessment])
                    print(f"💾 Live/Sim prediction saved to {csv_file}")
            except Exception as e:
                print(f"❌ Error saving to CSV: {e}")

        # 4. Return combined response
        response = {
            'features': data,
            'prediction': {
                'wqi': wqi,
                'assessment': assessment
            },
            'metadata': {
                'source': source,
                'timestamp': timestamp
            }
        }
        return jsonify(response)
        
    except Exception as e:
        print("❌ Error fetching/predicting live data:", e)
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

    # Calibration removed to use direct model prediction based on new dataset
    # wqi_calibrated = int(round(0.75 * wqi + 5))
    # wqi = max(0, min(100, wqi_calibrated))

    return jsonify({'wqi': wqi, 'assessment': get_assessment(wqi)})


if __name__ == '__main__':
    app.run(debug=True)
