"""Extract + incremental load of hourly weather and air-quality readings."""
import logging
import time
import pandas as pd
import requests
from .config import CITIES, INITIAL_BACKFILL_DAYS, MAX_BACKFILL_DAYS

log = logging.getLogger(__name__)
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
AQ_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

DDL = """CREATE TABLE IF NOT EXISTS raw_readings(
    city VARCHAR, ts TIMESTAMP, temp_c DOUBLE, humidity DOUBLE, wind_kmh DOUBLE,
    pm25 DOUBLE, pm10 DOUBLE, aqi DOUBLE, PRIMARY KEY(city, ts))"""

RETRIES = 4
TIMEOUT = 60


def _get(url, loc, hourly, past_days):
    params = dict(latitude=loc["lat"], longitude=loc["lon"], hourly=hourly,
                  past_days=past_days, forecast_days=1, timezone="Asia/Kolkata")
    for attempt in range(RETRIES):
        try:
            r = requests.get(url, params=params, timeout=TIMEOUT)
            r.raise_for_status()
            return pd.DataFrame(r.json()["hourly"])
        except requests.RequestException as e:
            wait = 5 * 2 ** attempt  # exponential backoff: 5s, 10s, 20s, 40s
            log.warning("retry %s/%s for %s: %s (waiting %ss)", attempt + 1, RETRIES, url, e, wait)
            time.sleep(wait)
    raise RuntimeError(f"API failed after retries: {url}")


def fetch_city(name, loc, past_days):
    w = _get(WEATHER_URL, loc, "temperature_2m,relative_humidity_2m,wind_speed_10m", past_days)
    a = _get(AQ_URL, loc, "pm2_5,pm10,us_aqi", past_days)
    df = w.merge(a, on="time", how="outer").rename(columns={
        "time": "ts", "temperature_2m": "temp_c", "relative_humidity_2m": "humidity",
        "wind_speed_10m": "wind_kmh", "pm2_5": "pm25", "us_aqi": "aqi"})
    df.insert(0, "city", name)
    df["ts"] = pd.to_datetime(df["ts"])
    return df[df["ts"] <= pd.Timestamp.now()]  # drop future placeholder rows


def backfill_days(con, city):
    """Incremental logic: only fetch what we don't have yet."""
    last = con.execute("SELECT max(ts) FROM raw_readings WHERE city=?", [city]).fetchone()[0]
    if last is None:
        return INITIAL_BACKFILL_DAYS
    gap = (pd.Timestamp.now() - pd.Timestamp(last)).days + 1
    return max(1, min(gap, MAX_BACKFILL_DAYS))


def load(con, df):
    con.execute(DDL)
    con.register("df", df)
    con.execute("""INSERT OR REPLACE INTO raw_readings
        SELECT city, ts, temp_c, humidity, wind_kmh, pm25, pm10, aqi FROM df""")
    con.unregister("df")
    return len(df)


def run(con):
    """Load each city independently; one bad city must not kill the whole run."""
    con.execute(DDL)
    total, failed = 0, []
    for name, loc in CITIES.items():
        try:
            days = backfill_days(con, name)
            n = load(con, fetch_city(name, loc, days))
            log.info("%s: loaded %d rows (past_days=%d)", name, n, days)
            total += n
        except Exception as e:
            log.error("%s: FAILED, skipping this run (%s)", name, e)
            failed.append(name)
    if failed:
        log.warning("Failed cities: %s (they will catch up on the next run)", failed)
    if len(failed) > len(CITIES) // 2:
        raise RuntimeError(f"Too many cities failed: {failed}")
    return total