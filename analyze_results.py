import pandas as pd
import joblib
from sklearn.metrics import r2_score, mean_absolute_error
from train_model import load_dataset, PARAM_RULES

def analyze():
    print("Loading model...")
    model = joblib.load('model/model.joblib')
    
    print("Loading data...")
    df = load_dataset()
    
    if df is None:
        return

    # WQI Analysis vs Quality
    if 'Quality' in df.columns:
        print("\n📊 WQI Stats by Quality Label:")
        stats = df.groupby('Quality')['wqi'].describe()
        print(stats)
        
        safe_mean = df[df['Quality'] == 'Safe']['wqi'].mean()
        unsafe_mean = df[df['Quality'] == 'Unsafe']['wqi'].mean()
        print(f"\nAverage WQI for Safe: {safe_mean:.2f}")
        print(f"Average WQI for Unsafe: {unsafe_mean:.2f}")

    # Model Evaluation
    X = df[list(PARAM_RULES.keys())]
    y = df['wqi']
    
    print("\nRunning predictions...")
    y_pred = model.predict(X)
    
    r2 = r2_score(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    
    print(f"\n✅ Model Performance on Full Dataset:")
    print(f"   R² Score: {r2:.4f}")
    print(f"   MAE: {mae:.3f}")

if __name__ == "__main__":
    analyze()
