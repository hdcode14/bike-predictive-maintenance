# scripts/create_database.py
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def create_database_schema():
    DATABASE_URL = os.getenv("DATABASE_URL")
    engine = create_engine(DATABASE_URL)
    
    # SQL statements to create tables
    sql_statements = [
        """
        DROP TABLE IF EXISTS maintenance_records CASCADE;
        DROP TABLE IF EXISTS rides CASCADE;
        DROP TABLE IF EXISTS bikes CASCADE;
        DROP TABLE IF EXISTS bike_features CASCADE;
        """,
        """
        CREATE TABLE bikes (
            bike_id SERIAL PRIMARY KEY,
            status VARCHAR(20) DEFAULT 'active',
            purchased_date DATE,
            last_serviced_date DATE,
            total_distance_km FLOAT DEFAULT 0
        );
        """,
        """
        CREATE TABLE rides (
            ride_id SERIAL PRIMARY KEY,
            bike_id INTEGER REFERENCES bikes(bike_id),
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            start_lat FLOAT,
            start_lon FLOAT,
            end_lat FLOAT,
            end_lon FLOAT,
            distance_km FLOAT,
            avg_vibration FLOAT,
            weather_condition VARCHAR(20)
        );
        """,
        """
        CREATE TABLE maintenance_records (
            record_id SERIAL PRIMARY KEY,
            bike_id INTEGER REFERENCES bikes(bike_id),
            maintenance_date DATE NOT NULL,
            component VARCHAR(20) NOT NULL,
            action VARCHAR(20) NOT NULL,
            associated_ride_id INTEGER REFERENCES rides(ride_id)
        );
        """,
        """
        CREATE TABLE bike_features (
            bike_id INTEGER PRIMARY KEY REFERENCES bikes(bike_id),
            calculation_date DATE,
            total_km FLOAT,
            total_km_since_last_service FLOAT,
            days_since_last_service INTEGER,
            avg_vibration_last_10_rides FLOAT,
            max_vibration_last_5_rides FLOAT,
            num_rides_last_7_days INTEGER,
            num_rides_in_rain_last_30_days INTEGER
        );
        """
    ]
    
    with engine.connect() as conn:
        for statement in sql_statements:
            conn.execute(text(statement))
        conn.commit()
    
    print("Database schema created successfully!")

if __name__ == "__main__":
    create_database_schema()