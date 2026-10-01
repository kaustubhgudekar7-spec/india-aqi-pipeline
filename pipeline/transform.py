"""SQL models: staging -> daily aggregate -> anomalies."""
MODELS = {
"stg_readings": """CREATE OR REPLACE VIEW stg_readings AS
    SELECT city, ts, temp_c, humidity, wind_kmh, pm25, pm10, aqi
    FROM raw_readings WHERE temp_c IS NOT NULL""",

"agg_daily": """CREATE OR REPLACE TABLE agg_daily AS
    SELECT city, CAST(ts AS DATE) AS day,
           round(avg(temp_c),1) AS avg_temp, round(avg(humidity),1) AS avg_humidity,
           round(avg(pm25),1) AS avg_pm25, max(pm25) AS max_pm25,
           round(avg(aqi),0) AS avg_aqi, max(aqi) AS max_aqi, count(*) AS n_readings
    FROM stg_readings GROUP BY 1,2""",

# z-score of PM2.5 vs the previous 7 days (168 hours) for the same city
"fct_anomalies": """CREATE OR REPLACE TABLE fct_anomalies AS
    WITH s AS (
      SELECT city, ts, pm25,
        avg(pm25)    OVER w AS mu,
        stddev(pm25) OVER w AS sd
      FROM stg_readings WHERE pm25 IS NOT NULL
      WINDOW w AS (PARTITION BY city ORDER BY ts ROWS BETWEEN 168 PRECEDING AND 1 PRECEDING))
    SELECT city, ts, pm25, round((pm25-mu)/sd,2) AS z_score
    FROM s WHERE sd > 0 AND abs((pm25-mu)/sd) > 3""",
}

def run(con):
    for sql in MODELS.values():
        con.execute(sql)
