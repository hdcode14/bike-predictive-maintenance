import pandas as pd
from sqlalchemy import create_engine, text
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import xgboost as xgb
import joblib
import os
from dotenv import load_dotenv

load_dotenv()

def train_model():
    engine = create_engine(os.getenv("DATABASE_URL"))
    
    # SQLite-compatible query with 30-day window instead of 90
    query = """
    SELECT 
        b.bike_id,
        b.total_distance_km,
        COALESCE((
            SELECT SUM(distance_km) 
            FROM rides r 
            WHERE r.bike_id = b.bike_id 
            AND r.end_time > COALESCE((SELECT MAX(maintenance_date) 
                                    FROM maintenance_records 
                                    WHERE bike_id = b.bike_id AND action = 'replaced'), '2000-01-01')
        ), b.total_distance_km) as km_since_service,
        COALESCE(julianday('now') - julianday(MAX(m.maintenance_date)), 999) as days_since_service,
        COALESCE((
            SELECT AVG(avg_vibration) 
            FROM (
                SELECT avg_vibration 
                FROM rides 
                WHERE bike_id = b.bike_id 
                ORDER BY end_time DESC 
                LIMIT 10
            ) as recent_rides
        ), 0) as avg_vibration_last_10,
        CASE 
            WHEN EXISTS (
                SELECT 1 FROM maintenance_records mr 
                WHERE mr.bike_id = b.bike_id 
                AND mr.maintenance_date BETWEEN date('now', '-30 days') AND date('now')
                AND mr.action = 'replaced'
            ) THEN 1 
            ELSE 0 
        END as had_failure
    FROM bikes b
    LEFT JOIN maintenance_records m ON b.bike_id = m.bike_id
    GROUP BY b.bike_id
    """
    
    df = pd.read_sql_query(query, engine)
    
    if df.empty:
        print("No data available for training")
        return
    
    # Check class distribution
    print("Class distribution:")
    print(df['had_failure'].value_counts())
    
    # If only one class exists, we can't train a proper model
    if len(df['had_failure'].unique()) < 2:
        print("Warning: Only one class found in target variable. Cannot train classification model.")
        print("This usually means all bikes had failures or no bikes had failures in the training period.")
        return
    
    # Prepare features and target
    X = df[['total_distance_km', 'km_since_service', 'days_since_service', 'avg_vibration_last_10']]
    y = df['had_failure']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train XGBoost model
    model = xgb.XGBClassifier(
        objective='binary:logistic',
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        use_label_encoder=False,
        eval_metric='logloss'
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    print("Model Evaluation:")
    print(classification_report(y_test, y_pred))
    
    # Save model
    os.makedirs('prod_model', exist_ok=True)
    joblib.dump(model, 'prod_model/xgboost_model.joblib')
    print("Model saved to prod_model/xgboost_model.joblib")

if __name__ == "__main__":
    train_model()