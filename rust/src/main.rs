use mysql_async::{prelude::*, Pool, Opts, Conn};
use rusqlite::{Connection, params};
use chrono::NaiveDate;
use tokio;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mysql_opts = Opts::from_url("mysql://RDQE:RDQE@localhost/")?;
    let pool = Pool::new(mysql_opts);
    let mut conn = pool.get_conn().await?;

    let sqlite_conn = Connection::open("rqmData.db")?;
    setup_sqlite(&sqlite_conn)?;

    // Fetch databases starting with "job_verifsassuser_"
    let databases: Vec<String> = conn.query("SHOW DATABASES LIKE 'job_verifsassuser_%'").await?;

    for database in databases {
        let job_date = NaiveDate::from_ymd(2023, 1, 1);
        let job_date_formatted = job_date.format("%d/%m/%Y").to_string();

        // Handling biases and detection rates for each database
        if let Err(e) = handle_biases(&mut conn, &sqlite_conn, &database, &job_date_formatted).await {
            eprintln!("Error handling biases for database {}: {}", database, e);
        }
        if let Err(e) = handle_detection_rates(&mut conn, &sqlite_conn, &database, &job_date_formatted).await {
            eprintln!("Error handling detection rates for database {}: {}", database, e);
        }
    }

    conn.disconnect().await?;
    Ok(())
}

async fn handle_biases(conn: &mut Conn, sqlite_conn: &Connection, database: &str, job_date_formatted: &str) -> Result<(), Box<dyn std::error::Error>> {
    conn.query_drop(format!("USE `{}`", database)).await?;

    let biases_query = r#"
        SELECT
            d.DS_NAME AS "Radar_Name",
            b.RADAR_MODE AS "Antenna_Type",
            ROUND(COALESCE(b.TIME_OFFSET_CALC_S, -1), 5) AS "Time_Bias",
            ROUND(COALESCE(b.RANGE_BIAS_CALC_M, -1), 5) AS "Range_Bias",
            ROUND(COALESCE((b.RANGE_GAIN_CALC - 1) * 1852, -1), 5) AS "Range_Gain",
            ROUND(COALESCE(b.AZIMUTH_BIAS_CALC_DEG, -1), 5) AS "Azimuth_Bias",
            ROUND(COALESCE(n.RANGE_ERROR_SD_CALC_M, -1), 5) AS "Range_Noise",
            ROUND(COALESCE(n.AZIMUTH_ERROR_SD_CALC_DEG, -1), 5) AS "Azimuth_Noise",
            ROUND(COALESCE(b.ECC_VALUE_CALC_DEG, -1), 5) AS "Ecc_Value",
            ROUND(COALESCE(b.ECC_ANGLE_CALC_DEG, -1), 5) AS "Ecc_Angle"
        FROM AN_RADAR_BIASES b
        LEFT JOIN AN_RADAR_NOISES n 
            ON b.DS_ID = n.DS_ID AND b.RADAR_MODE = n.RADAR_MODE AND b.ACTION_ID = n.ACTION_ID
        INNER JOIN LE_DS d ON b.DS_ID = d.DS_ID
        WHERE b.ACTION_ID = 2;
    "#;
    
    let biases_results: Vec<(String, String, f64, f64, f64, f64, f64, f64, f64, f64)> = conn.query(biases_query).await?;

    for row in biases_results {
        sqlite_conn.execute(
            "INSERT INTO biases (Radar_Name, Antenna_Type, Time_Bias, Range_Bias, Range_Gain, Azimuth_Bias, Range_Noise, Azimuth_Noise, Ecc_Value, Ecc_Angle, Job_Date) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11)",
            params![row.0, row.1, row.2, row.3, row.4, row.5, row.6, row.7, row.8, row.9, job_date_formatted],
        )?;
    }

    Ok(())
}

async fn handle_detection_rates(conn: &mut Conn, sqlite_conn: &Connection, database: &str, job_date_formatted: &str) -> Result<(), Box<dyn std::error::Error>> {
    conn.query_drop(format!("USE `{}`", database)).await?;

    let detection_rate_query = r#"
        SELECT
            d.DS_NAME AS "ds_name",
            r.radar_type_id AS "ds_type",
            COUNT(CASE WHEN tra.detection_P = 1 THEN 1 ELSE NULL END) / COUNT(CASE WHEN tra.detection_P IN (0, 1) THEN 1 ELSE NULL END) * 100 AS "pdP",
            COUNT(CASE WHEN tra.detection_S = 1 THEN 1 ELSE NULL END) / COUNT(CASE WHEN tra.detection_S IN (0, 1) THEN 1 ELSE NULL END) * 100 AS "pdS",
            COUNT(CASE WHEN tra.detection_M = 1 THEN 1 ELSE NULL END) / COUNT(CASE WHEN tra.detection_M IN (0, 1) THEN 1 ELSE NULL END) * 100 AS "pdM",
            COUNT(CASE WHEN tra.detection_PS = 1 THEN 1 ELSE NULL END) / COUNT(CASE WHEN tra.detection_PS IN (0, 1) THEN 1 ELSE NULL END) * 100 AS "pdPS",
            COUNT(CASE WHEN tra.detection_PM = 1 THEN 1 ELSE NULL END) / COUNT(CASE WHEN tra.detection_PM IN (0, 1) THEN 1 ELSE NULL END) * 100 AS "pdPM"
        FROM an_tr_rt_associations tra
        JOIN an_actions_otr a ON tra.ds_id = a.ds_id AND a.action_id = 2
        JOIN sd_radar s ON tra.REC_NUM = s.REC_NUM
        JOIN le_ds d ON s.ds_id = d.ds_id
        JOIN ds_radar r ON s.ds_id = r.ds_id
        GROUP BY d.DS_NAME
        ORDER BY d.DS_NAME;
    "#;
    
    let detection_rate_results: Vec<(String, String, f64, f64, f64, f64, f64)> = 
    conn.exec_map(detection_rate_query, (), |row| {
        let (ds_name, ds_type, pdP, pdS, pdM, pdPS, pdPM): (String, Vec<u8>, Vec<u8>, Vec<u8>, Vec<u8>, Option<Vec<u8>>, Vec<u8>) = mysql_async::from_row(row);
        let ds_type = String::from_utf8(ds_type).unwrap();
        let pdP = String::from_utf8(pdP).unwrap().parse::<f64>().unwrap();
        let pdS = String::from_utf8(pdS).unwrap().parse::<f64>().unwrap();
        let pdM = String::from_utf8(pdM).unwrap().parse::<f64>().unwrap();
        let pdPS = pdPS.map(|v| String::from_utf8(v).unwrap().parse::<f64>().unwrap());
        let pdPM = String::from_utf8(pdPM).unwrap().parse::<f64>().unwrap();
        (ds_name, ds_type, pdP, pdS, pdM, pdPS.unwrap_or(0.0), pdPM)
    }).await?;

    for row in detection_rate_results {
        sqlite_conn.execute(
            "INSERT INTO detection_rates (ds_name, ds_type, pdP, pdS, pdM, pdPS, pdPM, Job_Date) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8)",
            params![row.0, row.1, row.2, row.3, row.4, row.5, row.6, job_date_formatted],
        )?;
    }

    Ok(())
}

fn setup_sqlite(conn: &Connection) -> rusqlite::Result<()> {
    conn.execute(
        "CREATE TABLE IF NOT EXISTS biases (
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
        )", []
    )?;

    conn.execute(
        "CREATE TABLE IF NOT EXISTS detection_rates (
            ds_name TEXT,
            ds_type INT,
            pdP REAL,
            pdS REAL,
            pdM REAL,
            pdPS REAL,
            pdPM REAL,
            Job_Date TEXT
        )", []
    )?;
    Ok(())
}
