use config::{Config, File}; // Removed unused ConfigError
use mysql_async::{Pool, prelude::*, Row, Opts};
use rusqlite::{Connection, params};
use chrono::NaiveDate;
use tokio;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Load configurations using ConfigBuilder
    let settings = Config::builder()
        .add_source(File::with_name("config"))
        .build()?;

    let mysql_host = settings.get_string("Credentials.mysql_host")?;
    let mysql_user = settings.get_string("Credentials.mysql_user")?;
    let mysql_password = settings.get_string("Credentials.mysql_password")?;

    // Connect to MySQL
    let mysql_opts = Opts::from_url(&format!("mysql://{}:{}@{}/", mysql_user, mysql_password, mysql_host))?;
    let pool = Pool::new(mysql_opts);
    let mut conn = pool.get_conn().await?;

    // Connect to SQLite
    let sqlite_conn = Connection::open("rqmData.db")?;

    // Create tables in SQLite if they don't exist
    sqlite_conn.execute(
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

    sqlite_conn.execute(
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

    // SQL queries
    let biases_query = "your SQL query here for biases";
    let detection_rate_query = "your SQL query here for detection rates";

    // Query databases starting with "job_verifsassuser_"
    let databases_to_query: Vec<String> = conn.query("SHOW DATABASES LIKE 'job_verifsassuser_%'")
        .await?
        .map(|result| {
            result.map(|row| row.get::<_, String>(0).unwrap())
        }).await?;  // Collect results after mapping

    for database in databases_to_query {
        let job_date_str = "01/01/2023"; // Placeholder for user input
        if let Ok(job_date) = NaiveDate::parse_from_str(&job_date_str, "%d/%m/%Y") {
            let job_date_formatted = job_date.format("%d/%m/%Y").to_string();

            // Switch to the selected database
            conn.query_drop(format!("USE `{}`", database)).await?;

            // Perform queries and store results in SQLite
            let biases_results: Vec<(String, Option<f64>, Option<f64>)> = conn.query(biases_query).await?;
            for row in biases_results {
                sqlite_conn.execute("INSERT INTO biases (Radar_Name, Time_Bias, Range_Bias, Job_Date) VALUES (?1, ?2, ?3, ?4)", 
                                    params![row.0, row.1, row.2, job_date_formatted])?;
            }
        } else {
            println!("Invalid date format. Please enter the date in 'dd/mm/yyyy' format (e.g., '01/01/2023').");
        }
    }

    // Clean up
    conn.disconnect().await?;
    Ok(())
}

