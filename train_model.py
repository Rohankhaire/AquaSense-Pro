# train_model.py (HYBRID VERSION: Random Forest + XGBoost)
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, classification_report, confusion_matrix
from sklearn.ensemble import RandomForestRegressor, StackingRegressor
from sklearn.linear_model import LinearRegression
from xgboost import XGBRegressor
import joblib
import os

# Create model directory
os.makedirs('model', exist_ok=True)

# --------------------------
# Improved WQI Calculation Logic
# --------------------------
PARAM_RULES = {
    'ph':         {'min': 6.5,  'max': 8.5,  'tol': 1.0,   'weight': 0.05},
    'turbidity':  {'min': 0.0,  'max': 5.0,  'tol': 10.0,  'weight': 0.20},
    'tds':        {'min': 0.0,  'max': 500.0,'tol': 700.0, 'weight': 0.15},
    'do':         {'min': 6.5,  'max': 12.0, 'tol': 4.0,   'weight': 0.25},
    'temp':       {'min': 10.0, 'max': 30.0, 'tol': 10.0,  'weight': 0.05},
    'conductivity':{'min': 0.0, 'max': 1000.0,'tol': 1200.0,'weight': 0.10},
    'chlorine':   {'min': 0.2,  'max': 1.0,  'tol': 1.0,   'weight': 0.05},
    'nitrate':    {'min': 0.0,  'max': 10.0, 'tol': 20.0,  'weight': 0.15},
}

# Normalize weights
total_w = sum(r['weight'] for r in PARAM_RULES.values())
for k in PARAM_RULES:
    PARAM_RULES[k]['weight'] /= total_w


def subindex_for_param(value, rule):
    """Compute subindex (0–100) for a parameter based on how far it deviates from ideal."""
    try:
        v = float(value)
    except Exception:
        return 0.0

    mn, mx, tol = rule['min'], rule['max'], rule['tol']
    if mn <= v <= mx:
        return 100.0

    deviation = (mn - v) if v < mn else (v - mx)
    frac = deviation / (tol if tol > 0 else 1.0)
    subidx = max(0.0, 100.0 * (1.0 - frac))
    return subidx


def calculate_wqi_row(row):
    """Weighted WQI score (0–100)."""
    score = 0.0
    for param, rule in PARAM_RULES.items():
        val = row.get(param, None)
        if val is None:
            continue
        sidx = subindex_for_param(val, rule)
        score += sidx * rule['weight']
    return int(round(max(0, min(100, score))))


# --------------------------
# Load Dataset
# --------------------------
def load_dataset(filepath='water_quality_data_50000.csv'):
    print(f"📂 Loading dataset from {filepath}...")
    try:
        df = pd.read_csv(filepath)
    except FileNotFoundError:
        print(f"❌ Error: File {filepath} not found.")
        return None

    # Map columns to match PARAM_RULES keys
    # CSV Columns: pH,Turbidity,TDS,DO,Temperature,EC,Chlorine,Nitrate,Quality
    column_mapping = {
        'pH': 'ph',
        'Turbidity': 'turbidity',
        'TDS': 'tds',
        'DO': 'do',
        'Temperature': 'temp',
        'EC': 'conductivity',
        'Chlorine': 'chlorine',
        'Nitrate': 'nitrate'
    }
    
    df.rename(columns=column_mapping, inplace=True)
    
    # Check if all required columns exist
    required_cols = list(PARAM_RULES.keys())
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        print(f"⚠️ Warning: Missing columns: {missing_cols}")
    
    # Calculate WQI for the dataset
    print("🔄 Calculating WQI for all rows...")
    df['wqi'] = df.apply(calculate_wqi_row, axis=1)
    
    return df


# --------------------------
# Hybrid Model: Random Forest + XGBoost
# --------------------------
def build_hybrid_model():
    rf = RandomForestRegressor(
        n_estimators=250,
        max_depth=12,
        random_state=42
    )

    xgb = XGBRegressor(
        n_estimators=400,
        learning_rate=0.05,
        max_depth=8,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
        objective='reg:squarederror'
    )

    meta = LinearRegression()

    hybrid_model = StackingRegressor(
        estimators=[('rf', rf), ('xgb', xgb)],
        final_estimator=meta,
        passthrough=True,
        n_jobs=-1
    )

    return hybrid_model


# --------------------------
# Train & Evaluate
# --------------------------
def train_and_save():
    df = load_dataset()
    if df is None:
        return

    # Analyze WQI vs Quality Label
    if 'Quality' in df.columns:
        print("\n📊 Analysis: WQI vs 'Quality' Label")
        print(df.groupby('Quality')['wqi'].describe())
        
        # Simple threshold check
        # Assuming WQI > 50 is generally considered acceptable/fair, but let's see what the data says
        # Usually WQI < 25 is poor, 25-50 marginal, 50-70 fair, 70-90 good, 90-100 excellent
        # Depending on the formula, sometimes higher is better, sometimes lower. 
        # In this code: 100 is ideal (deviation = 0). So Higher WQI = Better water.
        
        # Safe vs Unsafe distribution
        safe_wqis = df[df['Quality'] == 'Safe']['wqi']
        unsafe_wqis = df[df['Quality'] == 'Unsafe']['wqi']
        print(f"\nAverage WQI for Safe: {safe_wqis.mean():.2f}")
        print(f"Average WQI for Unsafe: {unsafe_wqis.mean():.2f}")

    # Prepare features and target
    X = df[list(PARAM_RULES.keys())]
    y = df['wqi']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=1)

    model = build_hybrid_model()
    print("\n🚀 Training Hybrid Random Forest + XGBoost Model...")
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)

    print(f"\n✅ Model Performance:")
    print(f"   R² Score: {r2:.4f}")
    print(f"   MAE: {mae:.3f}")
    print("💾 Saving model to model/model.joblib")
    joblib.dump(model, 'model/model.joblib')

    # Feature importance (optional quick view)
    print("\nTop Features (Random Forest Importance):")
    rf_model = model.estimators_[0][1]
    importances = pd.Series(rf_model.feature_importances_, index=X.columns).sort_values(ascending=False)
    print(importances)


if __name__ == '__main__':
    train_and_save()
