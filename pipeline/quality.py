"""Data-quality gates. Any 'error' aborts the run; 'warn' is logged."""

CHECKS = [
    ("error", "null keys", "SELECT count(*) FROM raw_readings WHERE city IS NULL OR ts IS NULL"),
    ("error", "temp out of range", "SELECT count(*) FROM raw_readings WHERE temp_c NOT BETWEEN -10 AND 60"),
    ("error", "humidity out of range", "SELECT count(*) FROM raw_readings WHERE humidity NOT BETWEEN 0 AND 100"),
    ("error", "negative pollutants", "SELECT count(*) FROM raw_readings WHERE pm25 < 0 OR pm10 < 0"),
    ("warn", "aqi out of range", "SELECT count(*) FROM raw_readings WHERE aqi NOT BETWEEN 0 AND 500"),
    ("warn", "stale data (>6h)", """SELECT count(*) FROM (SELECT city, max(ts) m FROM raw_readings GROUP BY 1)
                                   WHERE m < now()::TIMESTAMP - INTERVAL 6 HOUR"""),
]

def run(con):
    errors, warns = [], []
    for level, name, sql in CHECKS:
        bad = con.execute(sql).fetchone()[0]
        if bad:
            (errors if level == "error" else warns).append(f"{name}: {bad} rows")
    return errors, warns
