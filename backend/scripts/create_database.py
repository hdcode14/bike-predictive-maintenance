import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def create_tables():
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bike_maintenance.db")
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    
    # SQLite-compatible SQL statements
    sql_statements = [
        "DROP TABLE IF EXISTS maintenance_records;",
        "DROP TABLE IF EXISTS rides;", 
        "DROP TABLE IF EXISTS bikes;",
        """
        CREATE TABLE bikes (
            bike_id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT DEFAULT 'active',
            purchased_date TEXT,
            last_serviced_date TEXT,
            total_distance_km REAL DEFAULT 0
        );
        """,
        """
        CREATE TABLE rides (
            ride_id INTEGER PRIMARY KEY AUTOINCREMENT,
            bike_id INTEGER,
            start_time TEXT,
            end_time TEXT,
            start_lat REAL,
            start_lon REAL,
            end_lat REAL,
            end_lon REAL,
            distance_km REAL,
            avg_vibration REAL,
            weather_condition TEXT,
            FOREIGN KEY (bike_id) REFERENCES bikes (bike_id)
        );
        """,
        """
        CREATE TABLE maintenance_records (
            record_id INTEGER PRIMARY KEY AUTOINCREMENT,
            bike_id INTEGER,
            maintenance_date TEXT,
            component TEXT,
            action TEXT,
            associated_ride_id INTEGER,
            FOREIGN KEY (bike_id) REFERENCES bikes (bike_id),
            FOREIGN KEY (associated_ride_id) REFERENCES rides (ride_id)
        );
        """
    ]
    
    with engine.connect() as conn:
        for statement in sql_statements:
            conn.execute(text(statement))
        conn.commit()
    
    print("SQLite database tables created successfully!")

if __name__ == "__main__":
    create_tables()