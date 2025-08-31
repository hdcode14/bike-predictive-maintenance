from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, date
import models
from database import engine, get_db, test_db_connection
import json

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Bike Predictive Maintenance API"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint with database verification"""
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@app.get("/bikes", response_model=List[Dict[str, Any]])
def get_bikes(db: Session = Depends(get_db)):
    """Get all bikes data"""
    try:
        bikes = db.query(models.Bike).all()
        return [
            {
                "bike_id": bike.bike_id,
                "status": bike.status,
                "purchased_date": bike.purchased_date.isoformat() if bike.purchased_date else None,
                "last_serviced_date": bike.last_serviced_date.isoformat() if bike.last_serviced_date else None,
                "total_distance_km": bike.total_distance_km,
                "created_at": bike.created_at.isoformat() if bike.created_at else None
            }
            for bike in bikes
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching bikes: {str(e)}")

@app.get("/rides", response_model=List[Dict[str, Any]])
def get_rides(db: Session = Depends(get_db)):
    """Get all rides data"""
    try:
        rides = db.query(models.Ride).all()
        return [
            {
                "ride_id": ride.ride_id,
                "bike_id": ride.bike_id,
                "start_time": ride.start_time.isoformat() if ride.start_time else None,
                "end_time": ride.end_time.isoformat() if ride.end_time else None,
                "distance_km": ride.distance_km,
                "avg_vibration": ride.avg_vibration,
                "weather_condition": ride.weather_condition,
                "created_at": ride.created_at.isoformat() if ride.created_at else None
            }
            for ride in rides
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching rides: {str(e)}")

@app.get("/maintenance", response_model=List[Dict[str, Any]])
def get_maintenance_records(db: Session = Depends(get_db)):
    """Get all maintenance records"""
    try:
        records = db.query(models.MaintenanceRecord).all()
        return [
            {
                "record_id": record.record_id,
                "bike_id": record.bike_id,
                "maintenance_date": record.maintenance_date.isoformat() if record.maintenance_date else None,
                "component": record.component,
                "action": record.action,
                "associated_ride_id": record.associated_ride_id,
                "created_at": record.created_at.isoformat() if record.created_at else None
            }
            for record in records
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching maintenance records: {str(e)}")

@app.get("/predictions", response_model=List[Dict[str, Any]])
def get_predictions(db: Session = Depends(get_db)):
    """Get maintenance predictions based on ride data and maintenance history"""
    try:
        # Get all bikes with their rides and maintenance history
        bikes = db.query(models.Bike).all()
        
        if not bikes:
            return []  # Return empty list instead of error if no bikes
        
        predictions = []
        
        for bike in bikes:
            # Get recent rides for this bike
            recent_rides = db.query(models.Ride).filter(
                models.Ride.bike_id == bike.bike_id
            ).order_by(models.Ride.start_time.desc()).limit(10).all()
            
            # Calculate prediction metrics with safe defaults
            total_vibration = 0
            vibration_count = 0
            recent_distance = 0
            
            for ride in recent_rides:
                if ride.avg_vibration is not None:
                    total_vibration += ride.avg_vibration
                    vibration_count += 1
                if ride.distance_km is not None:
                    recent_distance += ride.distance_km
            
            avg_vibration = total_vibration / vibration_count if vibration_count > 0 else 0
            
            # Safe access to bike attributes
            total_distance = bike.total_distance_km or 0
            bike_status = bike.status or "active"
            
            # Enhanced prediction logic
            issues = []
            confidence = 0.5
            
            if avg_vibration > 0.8:
                priority = "high"
                issues.extend(["suspension issues", "wheel alignment"])
                confidence = max(confidence, 0.9)
            elif avg_vibration > 0.5:
                priority = "medium"
                issues.extend(["tire pressure", "general checkup"])
                confidence = max(confidence, 0.7)
            
            if total_distance > 2000:
                priority = "high"
                issues.extend(["chain wear", "brake pads", "bearing replacement"])
                confidence = max(confidence, 0.85)
            elif total_distance > 1000:
                priority = "medium" if priority != "high" else "high"
                issues.extend(["chain lubrication", "brake adjustment"])
                confidence = max(confidence, 0.65)
            
            # If no specific issues found, recommend routine maintenance
            if not issues:
                priority = "low"
                issues = ["routine maintenance"]
                confidence = 0.5
            
            # Remove duplicates
            issues = list(set(issues))
            
            # Safe date formatting
            last_service = None
            if bike.last_serviced_date:
                if isinstance(bike.last_serviced_date, str):
                    last_service = bike.last_serviced_date
                else:
                    last_service = bike.last_serviced_date.isoformat()
            
            prediction = {
                "bike_id": bike.bike_id,
                "bike_status": bike_status,
                "total_distance_km": total_distance,
                "recent_distance_km": recent_distance,
                "avg_vibration": round(avg_vibration, 2),
                "maintenance_priority": priority,
                "predicted_issues": issues,
                "confidence_score": round(confidence, 2),
                "recommended_maintenance": f"Check {', '.join(issues)}",
                "last_service": last_service or "Never",
                "recent_rides_count": len(recent_rides)
            }
            predictions.append(prediction)
        
        return predictions
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Prediction error: {error_details}")  # Debug output
        raise HTTPException(status_code=500, detail=f"Error generating predictions: {str(e)}")
    

@app.get("/test-data")
def create_test_data(db: Session = Depends(get_db)):
    """Create test data for development"""
    try:
        # Clear existing data
        db.query(models.MaintenanceRecord).delete()
        db.query(models.Ride).delete()
        db.query(models.Bike).delete()
        db.commit()
        
        # Add test bikes
        test_bikes = [
            models.Bike(
                bike_id=1,
                status="active",
                purchased_date=date(2023, 1, 15),
                last_serviced_date=date(2023, 10, 15),
                total_distance_km=1250.5
            ),
            models.Bike(
                bike_id=2,
                status="active",
                purchased_date=date(2023, 3, 20),
                last_serviced_date=date(2023, 11, 20),
                total_distance_km=850.2
            ),
            models.Bike(
                bike_id=3,
                status="maintenance",
                purchased_date=date(2022, 8, 10),
                last_serviced_date=date(2023, 9, 5),
                total_distance_km=2300.8
            ),
        ]
        
        db.add_all(test_bikes)
        db.commit()
        
        # Add test rides
        test_rides = [
            models.Ride(
                bike_id=1,
                start_time=datetime(2023, 12, 1, 8, 0, 0),
                end_time=datetime(2023, 12, 1, 9, 30, 0),
                distance_km=25.5,
                avg_vibration=0.7,
                weather_condition="sunny"
            ),
            models.Ride(
                bike_id=2,
                start_time=datetime(2023, 12, 1, 10, 0, 0),
                end_time=datetime(2023, 12, 1, 11, 15, 0),
                distance_km=18.2,
                avg_vibration=0.4,
                weather_condition="cloudy"
            ),
            models.Ride(
                bike_id=3,
                start_time=datetime(2023, 11, 30, 14, 0, 0),
                end_time=datetime(2023, 11, 30, 16, 0, 0),
                distance_km=35.8,
                avg_vibration=0.9,
                weather_condition="rainy"
            ),
        ]
        
        db.add_all(test_rides)
        db.commit()
        
        return {
            "message": "Test data created successfully",
            "bikes_added": len(test_bikes),
            "rides_added": len(test_rides)
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating test data: {str(e)}")

if __name__ == "__main__":
    # Test database connection
    test_db_connection()
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)