# backend/models.py
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Bike(Base):
    __tablename__ = "bikes"
    bike_id = Column(Integer, primary_key=True, index=True)
    status = Column(String, default='active')
    purchased_date = Column(Date)
    last_serviced_date = Column(Date, nullable=True)
    total_distance_km = Column(Float, default=0.0)

class Ride(Base):
    __tablename__ = "rides"
    ride_id = Column(Integer, primary_key=True, index=True)
    bike_id = Column(Integer, ForeignKey("bikes.bike_id"))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    start_lat = Column(Float)
    start_lon = Column(Float)
    end_lat = Column(Float)
    end_lon = Column(Float)
    distance_km = Column(Float)
    avg_vibration = Column(Float)
    weather_condition = Column(String)

class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"
    record_id = Column(Integer, primary_key=True, index=True)
    bike_id = Column(Integer, ForeignKey("bikes.bike_id"))
    maintenance_date = Column(Date)
    component = Column(String)
    action = Column(String)
    associated_ride_id = Column(Integer, ForeignKey("rides.ride_id"), nullable=True)