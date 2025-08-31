
from sqlalchemy import Column, Integer, String, Float, DateTime, Date
from database import Base

class Bike(Base):
    __tablename__ = "bikes" 
    
    bike_id = Column(Integer, primary_key=True, index=True)
    status = Column(String)
    purchased_date = Column(Date)
    last_serviced_date = Column(Date) 
    total_distance_km = Column(Float)  
    created_at = Column(DateTime) 

class Ride(Base):
    __tablename__ = "rides"
    
    ride_id = Column(Integer, primary_key=True, index=True)
    bike_id = Column(Integer)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    distance_km = Column(Float)
    avg_vibration = Column(Float)
    weather_condition = Column(String)
    created_at = Column(DateTime)

class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"
    
    record_id = Column(Integer, primary_key=True, index=True)
    bike_id = Column(Integer)
    maintenance_date = Column(Date)
    component = Column(String)
    action = Column(String)
    associated_ride_id = Column(Integer)
    created_at = Column(DateTime)