import mysql.connector
import sqlite3
from datetime import datetime
import configparser

# Create a ConfigParser object and read the config file
config = configparser.ConfigParser()
config.read('config.ini')

# Replace with your actual connection details
mysql_host = config['Credentials']['mysqlhost']
mysql_user = config['Credentials']['mysql_user']
mysql_password = config['Credentials']['mysql_password']

# Provided SQL queries
biases_query = """
    SELECT LE_DS.DS_NAME "Radar Name", AN_RADAR_BIASES.RADAR_MODE "Antenna Type",
    CASE WHEN TIME_OFFSET_CALC_S IS NULL THEN -1 ELSE ROUND(TIME_OFFSET_CALC_S, 5) END "Time Bias",
    CASE WHEN AN_RADAR_BIASES.RANGE_BIAS_CALC_M IS NULL THEN -1 ELSE ROUND(AN_RADAR_BIASES.RANGE_BIAS_CALC_M, 5) END "Range Bias",
    CASE WHEN AN_RADAR_BIASES.RANGE_GAIN_CALC IS NULL THEN -1 ELSE ROUND((AN_RADAR_BIASES.RANGE_GAIN_CALC - 1) * 1852, 5) END "Range Gain",
    CASE WHEN AN_RADAR_BIASES.AZIMUTH_BIAS_CALC_DEG IS NULL THEN -1 ELSE ROUND(AN_RADAR_BIASES.AZIMUTH_BIAS_CALC_DEG, 5) END "Azimuth Bias",
    CASE WHEN AN_RADAR_NOISES.RANGE_ERROR_SD_CALC_M IS NULL THEN -1 ELSE ROUND(AN_RADAR_NOISES.RANGE_ERROR_SD_CALC_M, 5) END "Range Noise",
    CASE WHEN AZIMUTH_ERROR_SD_CALC_DEG IS NULL THEN -1 ELSE ROUND(AZIMUTH_ERROR_SD_CALC_DEG, 5) END "Azimuth Noise",
    CASE WHEN AN_RADAR_BIASES.ECC_VALUE_CALC_DEG IS NULL THEN -1 ELSE ROUND(AN_RADAR_BIASES.ECC_VALUE_CALC_DEG, 5) END "Ecc Value",
    CASE WHEN AN_RADAR_BIASES.ECC_ANGLE_CALC_DEG IS NULL THEN -1 ELSE ROUND(AN_RADAR_BIASES.ECC_ANGLE_CALC_DEG, 5) END "Ecc Angle"
    FROM AN_RADAR_BIASES
    LEFT JOIN AN_RADAR_NOISES
    ON (
        AN_RADAR_NOISES.DS_ID = AN_RADAR_BIASES.DS_ID  AND
        AN_RADAR_NOISES.RADAR_MODE = AN_RADAR_BIASES.RADAR_MODE  AND
        AN_RADAR_NOISES.ACTION_ID = AN_RADAR_BIASES.ACTION_ID)
    INNER JOIN LE_DS
    ON (AN_RADAR_BIASES.DS_ID=LE_DS.DS_ID)
    WHERE
    AN_RADAR_BIASES.ACTION_ID=2;
    """

detection_rate_query = """
    SELECT 
        LE_DS.DS_NAME ds_name, 
        ds_radar.radar_type_id ds_type,
        COUNT(CASE WHEN detection_P IN (1) THEN 1 ELSE NULL END) /
        COUNT(CASE WHEN detection_P IN (0, 1) THEN 1 ELSE NULL END) * 100 pdP,
        COUNT(CASE WHEN detection_S IN (1) THEN 1 ELSE NULL END) /
        COUNT(CASE WHEN detection_S IN (0, 1) THEN 1 ELSE NULL END) * 100 pdS,
        COUNT(CASE WHEN detection_M IN (1) THEN 1 ELSE NULL END) /
        COUNT(CASE WHEN detection_M IN (0, 1) THEN 1 ELSE NULL END) * 100 pdM,
        COUNT(CASE WHEN detection_PS IN (1) THEN 1 ELSE NULL END) /
        COUNT(CASE WHEN detection_PS IN (0, 1) THEN 1 ELSE NULL END) * 100 pdPS,
        COUNT(CASE WHEN detection_PM IN (1) THEN 1 ELSE NULL END) /
        COUNT(CASE WHEN detection_PM IN (0, 1) THEN 1 ELSE NULL END) * 100 pdPM 
    FROM (
        (
            (
                an_tr_rt_associations
                JOIN
                an_actions_otr
                ON an_actions_otr.action_id=2 AND
                an_tr_rt_associations.ds_id=an_actions_otr.ds_id 
            ) 
            JOIN 
            sd_radar 
            ON an_tr_rt_associations.REC_NUM=sd_radar.REC_NUM 
        ) 
        JOIN 
        le_ds 
        ON sd_radar.ds_id=le_ds.ds_id
    )
    JOIN
    ds_radar
    ON sd_radar.ds_id=ds_radar.ds_id
    GROUP BY le_ds.ds_name
    ORDER BY le_ds.ds_name;
    """

# Connect to the remote MariaDB server
mysql_connection = mysql.connector.connect(
    host=mysql_host,
    user=mysql_user,
    password=mysql_password
)

# Create an SQLite database and connect to it
sqlite_connection = sqlite3.connect('rqmData.db')
sqlite_cursor = sqlite_connection.cursor()

# Execute the provided SQL queries
try:
    if mysql_connection.is_connected():
        mysql_cursor = mysql_connection.cursor()

        # Find databases that begin with "job_verifsassuser_"
        mysql_cursor.execute("SHOW DATABASES LIKE 'job_verifsassuser_%'")
        databases_to_query = [database[0] for database in mysql_cursor.fetchall()]

        for database in databases_to_query:
            # Prompt the user for the date of the job in "dd/mm/yyyy" format
            job_date_str = input(f"Enter the date for job '{database}' (dd/mm/yyyy): ")

            try:
                # Parse the input date string into a datetime object
                job_date = datetime.strptime(job_date_str, "%d/%m/%Y")

                # Format the datetime object as a string in the desired format (dd/mm/yyyy)
                job_date_formatted = job_date.strftime("%d/%m/%Y")

                # Create the "biases" table if it doesn't exist
                sqlite_cursor.execute('''CREATE TABLE IF NOT EXISTS biases (
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
                    Job_Date TEXT
                )''')

                # Create the "detection_rates" table if it doesn't exist
                sqlite_cursor.execute('''CREATE TABLE IF NOT EXISTS detection_rates (
                    ds_name TEXT,
                    ds_type INT,
                    pdP REAL,
                    pdS REAL,
                    pdM REAL,
                    pdPS REAL,
                    pdPM REAL,
                    Job_Date TEXT
                )''')

                # Execute the biases_query
                mysql_cursor.execute(f"USE `{database}`")
                mysql_cursor.execute(biases_query)
                biases_results = mysql_cursor.fetchall()

                # Insert data into the "biases" table with the date
                for row in biases_results:
                    # Insert data with column names explicitly listed
                    sqlite_cursor.execute(
                        "INSERT INTO biases (Radar_Name, Antenna_Type, Time_Bias, Range_Bias, Range_Gain, Azimuth_Bias, Range_Noise, Azimuth_Noise, Ecc_Value, Ecc_Angle, Job_Date) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (row + (job_date_formatted,))
                    )

                # Execute the detection_rate_query
                mysql_cursor.execute(detection_rate_query)
                detection_rate_results = mysql_cursor.fetchall()

                # Insert data into the "detection_rates" table with the date
                for row in detection_rate_results:
                    # Convert numeric values to float or set to -1 if None
                    ds_name = row[0]
                    ds_type = row[1]
                    pdP = float(row[2]) if row[2] is not None else -1
                    pdS = float(row[3]) if row[3] is not None else -1
                    pdM = float(row[4]) if row[4] is not None else -1
                    pdPS = float(row[5]) if row[5] is not None else -1
                    pdPM = float(row[6]) if row[6] is not None else -1

                    sqlite_cursor.execute(
                        "INSERT INTO detection_rates (ds_name, ds_type, pdP, pdS, pdM, pdPS, pdPM, Job_Date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (ds_name, ds_type, pdP, pdS, pdM, pdPS, pdPM, job_date_formatted)
                    )

            except ValueError:
                print(f"Invalid date format. Please enter the date in 'dd/mm/yyyy' format (e.g., '01/01/2023').")

    # Commit the changes to the SQLite database
    sqlite_connection.commit()

except mysql.connector.Error as e:
    print("MySQL Error: ", e)

finally:
    if mysql_connection.is_connected():
        mysql_cursor.close()
        mysql_connection.close()

    sqlite_cursor.close()
    sqlite_connection.close()