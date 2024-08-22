import sqlite3
import random
from datetime import datetime, timedelta

DATA_DB = "rqmData.db"

def generate_fake_data(num_days=30):
    conn = sqlite3.connect(DATA_DB)
    cursor = conn.cursor()

    # Create tables (using DATE data type for Job_Date)
    cursor.execute('''
        CREATE TABLE biases (
            Radar_Name TEXT,
            Antenna_Type TEXT,
            Time_Bias REAL,
            Range_Bias REAL,
            Range_Gain REAL,
            Azimuth_Bias REAL,
            Range_Noise REAL,
            Azimuth_Noise REAL,
            Ecc_Value REAL,
            Ecc_Angle REAL,
            Job_Date DATE
        )
    ''')

    cursor.execute('''
        CREATE TABLE detection_rates (
            ds_name TEXT,
            ds_type INT,
            pdP REAL,
            pdS REAL,
            pdM REAL,
            pdPS REAL,
            pdPM REAL,
            Job_Date DATE
        )
    ''')

    # Insert fake data
    radars = ['Radar A', 'Radar B', 'Radar C']
    antenna_types = ['Type 1', 'Type 2']
    start_date = datetime.now() - timedelta(days=num_days)

    for i in range(num_days):
        current_date = start_date + timedelta(days=i)
        for radar in radars:
            for antenna_type in antenna_types:
                cursor.execute('''
                    INSERT INTO biases VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    radar,
                    antenna_type,
                    random.uniform(-1, 1),  # Time_Bias
                    random.uniform(-100, 100),  # Range_Bias
                    random.uniform(0.9, 1.1),  # Range_Gain
                    random.uniform(-10, 10),  # Azimuth_Bias
                    random.uniform(0, 5),  # Range_Noise
                    random.uniform(0, 2),  # Azimuth_Noise
                    random.uniform(-5, 5),  # Ecc_Value
                    random.uniform(0, 360),  # Ecc_Angle
                    current_date  # Store as a datetime object directly
                ))

                cursor.execute('''
                    INSERT INTO detection_rates VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    radar,
                    random.randint(1, 3),  # ds_type
                    random.uniform(80, 100),  # pdP
                    random.uniform(70, 90),  # pdS
                    random.uniform(60, 80),  # pdM
                    random.uniform(50, 70),  # pdPS
                    random.uniform(40, 60),  # pdPM
                    current_date  # Store as a datetime object directly
                ))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    generate_fake_data()