# backend/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
import pandas as pd
from datetime import datetime, timedelta
import joblib
import os
from dotenv import load_dotenv
import requests
import numpy as np
import random

from database import get_db, engine
import models

load_dotenv()

app = FastAPI(title="Bike Predictive Maintenance API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
from pydantic import BaseModel
from typing import List, Optional

class RideData(BaseModel):
    bike_id: int
    start_time: datetime
    end_time: datetime
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    distance_km: float
    avg_vibration: float
    weather_condition: str

class BikePrediction(BaseModel):
    bike_id: int
    failure_probability: float
    total_km: float
    days_since_last_service: int

@app.get("/")
def read_root():
    return {"message": "Bike Predictive Maintenance API"}

@app.post("/rides")
def add_ride(ride: RideData, db: Session = Depends(get_db)):
    try:
        # Create new ride
        db_ride = models.Ride(**ride.dict())
        db.add(db_ride)
        db.commit()
        db.refresh(db_ride)
        
        # Update bike's total distance
        bike = db.query(models.Bike).filter(models.Bike.bike_id == ride.bike_id).first()
        if bike:
            bike.total_distance_km += ride.distance_km
            db.commit()
        
        return {"message": "Ride logged successfully", "ride_id": db_ride.ride_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/bikes")
def get_bikes(db: Session = Depends(get_db)):
    bikes = db.query(models.Bike).all()
    return bikes

@app.get("/predictions")
def get_predictions(db: Session = Depends(get_db)):
    try:
        # Load trained model
        try:
            model = joblib.load('prod_model/xgboost_model.joblib')
        except:
            return {"error": "Model not trained yet. Please train the model first."}
        
        # Calculate features for prediction
        query = """
        SELECT 
            b.bike_id,
            b.total_distance_km as total_km,
            COALESCE((
                SELECT SUM(distance_km) 
                FROM rides r 
                WHERE r.bike_id = b.bike_id 
                AND r.end_time > COALESCE((SELECT MAX(maintenance_date) 
                                        FROM maintenance_records 
                                        WHERE bike_id = b.bike_id), '2000-01-01')
            ), b.total_distance_km) as km_since_service,
            COALESCE(EXTRACT(DAY FROM NOW() - MAX(m.maintenance_date)), 999) as days_since_service,
            COALESCE((
                SELECT AVG(avg_vibration) 
                FROM (
                    SELECT avg_vibration 
                    FROM rides 
                    WHERE bike_id = b.bike_id 
                    ORDER BY end_time DESC 
                    LIMIT 10
                ) as recent_rides
            ), 0) as avg_vibration_last_10
        FROM bikes b
        LEFT JOIN maintenance_records m ON b.bike_id = m.bike_id
        WHERE b.status = 'active'
        GROUP BY b.bike_id
        """
        
        features_df = pd.read_sql_query(query, engine)
        
        if features_df.empty:
            return []
        
        # Prepare features for prediction (same order as training)
        X = features_df[['total_km', 'km_since_service', 'days_since_service', 'avg_vibration_last_10']]
        X.fillna(0, inplace=True)
        
        # Predict probabilities
        probabilities = model.predict_proba(X)[:, 1]  # Probability of class 1 (failure)
        
        # Prepare response
        predictions = []
        for i, row in features_df.iterrows():
            predictions.append({
                "bike_id": int(row['bike_id']),
                "failure_probability": float(probabilities[i]),
                "total_km": float(row['total_km']),
                "days_since_last_service": int(row['days_since_service'] or 999)
            })
        
        # Sort by failure probability (highest first)
        predictions.sort(key=lambda x: x['failure_probability'], reverse=True)
        return predictions
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/plan_route")
def plan_route(bike_ids: List[int]):
    try:
        MAPBOX_TOKEN = os.getenv("MAPBOX_ACCESS_TOKEN")
        if not MAPBOX_TOKEN:
            raise HTTPException(status_code=500, detail="Mapbox token not configured")
        
        # Get locations for selected bikes (using mock data for now)
        locations = []
        for bike_id in bike_ids:
            # In a real scenario, you'd query the database for the last known location
            mock_lat = 40.7128 + (random.random() - 0.5) * 0.1
            mock_lon = -74.0060 + (random.random() - 0.5) * 0.1
            locations.append(f"{mock_lon},{mock_lat}")
        
        if len(locations) < 2:
            return {"geometry": None}
        
        # Call Mapbox Directions API
        coordinates = ";".join(locations)
        url = f"https://api.mapbox.com/directions/v5/mapbox/driving/{coordinates}?geometries=geojson&access_token={MAPBOX_TOKEN}"
        
        response = requests.get(url)
        data = response.json()
        
        if response.status_code != 200 or 'routes' not in data:
            raise HTTPException(status_code=500, detail="Failed to get route from Mapbox")
        
        return data['routes'][0]['geometry']
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)