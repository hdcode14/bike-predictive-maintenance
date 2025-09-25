import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

def generate_synthetic_data():
    engine = create_engine(os.getenv("DATABASE_URL"))
    
    # Clear existing data
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM maintenance_records;"))
        conn.execute(text("DELETE FROM rides;"))
        conn.execute(text("DELETE FROM bikes;"))
        conn.commit()

    # Generate bikes
    bikes_data = []
    for i in range(1, 101):  # 100 bikes
        bikes_data.append({
            'bike_id': i,
            'purchased_date': datetime.now() - timedelta(days=random.randint(100, 365)),
            'status': 'active',
            'total_distance_km': 0
        })
    
    bikes_df = pd.DataFrame(bikes_data)
    bikes_df.to_sql('bikes', engine, if_exists='append', index=False)
    print("Generated 100 bikes")

    # Generate rides and maintenance records
    all_rides = []
    all_maintenance = []
    
    for bike_id in range(1, 101):
        current_date = datetime.now() - timedelta(days=90)  # 90 days of history
        last_maintenance_date = current_date - timedelta(days=random.randint(10, 30))
        total_km = 0
        
        # Only 70% of bikes will have failures (more realistic)
        bike_will_have_failures = random.random() < 0.7
        
        while current_date <= datetime.now():
            # 0-4 rides per day
            num_rides = random.randint(0, 4)
            for _ in range(num_rides):
                # Simulate ride
                is_long_ride = random.random() < 0.2
                distance = random.uniform(1, 15) if is_long_ride else random.uniform(0.5, 5)
                is_hard_ride = random.random() < 0.15
                vibration = random.uniform(8, 20) if is_hard_ride else random.uniform(1, 7)
                weather = 'rain' if random.random() < 0.2 else 'clear'
                
                ride_data = {
                    'bike_id': bike_id,
                    'start_time': current_date - timedelta(hours=random.randint(1, 5)),
                    'end_time': current_date,
                    'start_lat': 40.7 + random.uniform(-0.1, 0.1),
                    'start_lon': -74.0 + random.uniform(-0.1, 0.1),
                    'end_lat': 40.7 + random.uniform(-0.1, 0.1),
                    'end_lon': -74.0 + random.uniform(-0.1, 0.1),
                    'distance_km': distance,
                    'avg_vibration': vibration,
                    'weather_condition': weather
                }
                all_rides.append(ride_data)
                total_km += distance
                
                # Only simulate maintenance for bikes that will have failures
                if bike_will_have_failures and is_hard_ride and (datetime.now() - last_maintenance_date).days > 7:
                    fail_component = random.choice(['brake', 'chain', 'tire'])
                    failure_date = current_date + timedelta(days=random.randint(5, 14))
                    if failure_date <= datetime.now():
                        maint_data = {
                            'bike_id': bike_id,
                            'maintenance_date': failure_date,
                            'component': fail_component,
                            'action': 'replaced',
                            'associated_ride_id': len(all_rides)
                        }
                        all_maintenance.append(maint_data)
                        last_maintenance_date = failure_date
            
            current_date += timedelta(days=1)
    
    # Save to database
    rides_df = pd.DataFrame(all_rides)
    rides_df.to_sql('rides', engine, if_exists='append', index=False)
    print(f"Generated {len(all_rides)} rides")
    
    if all_maintenance:
        maint_df = pd.DataFrame(all_maintenance)
        maint_df.to_sql('maintenance_records', engine, if_exists='append', index=False)
        print(f"Generated {len(all_maintenance)} maintenance records for {len(set([m['bike_id'] for m in all_maintenance]))} bikes")
    else:
        print("No maintenance records generated")
    
    # Update total distance for each bike
    with engine.connect() as conn:
        for bike_id in range(1, 101):
            result = conn.execute(text(f"SELECT SUM(distance_km) FROM rides WHERE bike_id = {bike_id}"))
            total_dist = result.scalar() or 0
            conn.execute(text(f"UPDATE bikes SET total_distance_km = {total_dist} WHERE bike_id = {bike_id}"))
        conn.commit()
    
    print("Synthetic data generation complete!")
    print(f"Bikes with failures: {len(set([m['bike_id'] for m in all_maintenance])) if all_maintenance else 0}")
    print(f"Bikes without failures: {100 - (len(set([m['bike_id'] for m in all_maintenance])) if all_maintenance else 0)}")

if __name__ == "__main__":
    generate_synthetic_data()