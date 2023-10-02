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
    SELECT
        d.DS_NAME AS "Radar Name",
        b.RADAR_MODE AS "Antenna Type",
        ROUND(COALESCE(b.TIME_OFFSET_CALC_S, -1), 5) AS "Time Bias",
        ROUND(COALESCE(b.RANGE_BIAS_CALC_M, -1), 5) AS "Range Bias",
        ROUND(COALESCE((b.RANGE_GAIN_CALC - 1) * 1852, -1), 5) AS "Range Gain",
        ROUND(COALESCE(b.AZIMUTH_BIAS_CALC_DEG, -1), 5) AS "Azimuth Bias",
        ROUND(COALESCE(n.RANGE_ERROR_SD_CALC_M, -1), 5) AS "Range Noise",
        ROUND(COALESCE(n.AZIMUTH_ERROR_SD_CALC_DEG, -1), 5) AS "Azimuth Noise",
        ROUND(COALESCE(b.ECC_VALUE_CALC_DEG, -1), 5) AS "Ecc Value",
        ROUND(COALESCE(b.ECC_ANGLE_CALC_DEG, -1), 5) AS "Ecc Angle"
    FROM AN_RADAR_BIASES b
    LEFT JOIN AN_RADAR_NOISES n 
        ON  b.DS_ID = n.DS_ID
        AND b.RADAR_MODE = n.RADAR_MODE
        AND b.ACTION_ID = n.ACTION_ID
    INNER JOIN LE_DS d ON b.DS_ID = d.DS_ID
    WHERE b.ACTION_ID = 2;

    """

detection_rate_query = """
        SELECT
        d.DS_NAME AS ds_name,
        r.radar_type_id AS ds_type,
        COUNT(CASE WHEN tra.detection_P = 1 THEN 1 ELSE NULL END) /
        COUNT(CASE WHEN tra.detection_P IN (0, 1) THEN 1 ELSE NULL END) * 100 AS pdP,
        COUNT(CASE WHEN tra.detection_S = 1 THEN 1 ELSE NULL END) /
        COUNT(CASE WHEN tra.detection_S IN (0, 1) THEN 1 ELSE NULL END) * 100 AS pdS,
        COUNT(CASE WHEN tra.detection_M = 1 THEN 1 ELSE NULL END) /
        COUNT(CASE WHEN tra.detection_M IN (0, 1) THEN 1 ELSE NULL END) * 100 AS pdM,
        COUNT(CASE WHEN tra.detection_PS = 1 THEN 1 ELSE NULL END) /
        COUNT(CASE WHEN tra.detection_PS IN (0, 1) THEN 1 ELSE NULL END) * 100 AS pdPS,
        COUNT(CASE WHEN tra.detection_PM = 1 THEN 1 ELSE NULL END) /
        COUNT(CASE WHEN tra.detection_PM IN (0, 1) THEN 1 ELSE NULL END) * 100 AS pdPM
    FROM
        an_tr_rt_associations tra
    JOIN
        an_actions_otr a ON tra.ds_id = a.ds_id AND a.action_id = 2
    JOIN
        sd_radar s ON tra.REC_NUM = s.REC_NUM
    JOIN
        le_ds d ON s.ds_id = d.ds_id
    JOIN
        ds_radar r ON s.ds_id = r.ds_id
    GROUP BY
        d.DS_NAME
    ORDER BY
        d.DS_NAME;
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